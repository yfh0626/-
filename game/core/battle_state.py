import random

class Effect:
    def __init__(self, priority, actor, resolve_fn, **data):
        self.priority = priority
        self.actor = actor
        self.resolve_fn = resolve_fn
        self.data = data


class BattleState:
    def __init__(self, rows, cols, player, enemy,
                 characters=None, all_skills=None):
        self.rows = rows
        self.cols = cols

        self.player = player
        self.enemy = enemy

        self.characters = characters or [player, enemy]
        self.all_skills = all_skills or {}

        self.selected_skill = None
        self.selected_cell = None

        self.effects = []
        self.draw = False

        self._common_move_requests = []
        self.mud_cells = set()
        self._round_damage_taken = set()

    # ── push interface ──

    def push(self, priority, actor, fn, **data):
        self.effects.append(Effect(priority, actor, fn, **data))

    # 兼容旧接口：不改变同学版 Effect 队列，只是允许旧代码继续调用。
    def push_damage(self, target, damage, source=None, priority=5.0, **data):
        self.push(priority, source, self._apply_damage,
                  target=target, amount=damage, **data)

    def apply_damage(self, target, damage, source=None, priority=5.0, **data):
        self.push_damage(target=target, damage=damage, source=source,
                         priority=priority, **data)

    def push_status(self, target, key, value, source=None, priority=4.0, **data):
        self.push(priority, source, self._apply_status,
                  target=target, key=key, value=value, **data)

    def push_move(self, actor, new_pos, source=None, priority=3.0, **data):
        self.push(priority, source or actor, self._apply_move,
                  target=actor, pos=new_pos, **data)

    # ── resolution ──

    def resolve(self, decision_a, decision_b, log, abort_if_first_fails=False):
        self.effects.clear()
        self.draw = False
        self._common_move_requests.clear()
        self._round_damage_taken.clear()

        decisions = [decision_a, decision_b]
        first_cast_success = True
        chaos_random_active_this_round = set()

        for decision in decisions:
            if decision is None:
                continue
            actor = decision[0]
            if actor is not None and self._is_chaos_random_active(actor):
                chaos_random_active_this_round.add(actor)

        # 先尝试提交双方主动技能效果，但不立即结算。
        # 如果玩家技能释放失败，可直接中止本轮：不揭晓 AI、不触发回合效果、不减少冷却。
        for index, decision in enumerate(decisions):
            if decision is None:
                continue
            actor, skill, target = decision
            if actor is None or skill is None or self._is_chaos_random_active(actor):
                continue
            energy_cost = max(0, getattr(skill, "energy_cost", 0))
            if getattr(actor, "energy", 0) < energy_cost:
                if log:
                    log(f"{actor.name} \u80fd\u91cf\u4e0d\u8db3\uff0c\u65e0\u6cd5\u4f7f\u7528 {skill.name}\uff08\u9700\u8981 {energy_cost} \u70b9\uff09\u3002")
                return {
                    "round_resolved": False,
                    "first_cast_success": index != 0,
                    "failure_reason": "energy",
                    "failed_actor": actor,
                    "failed_skill": skill,
                    "required_energy": energy_cost,
                }

        for index, decision in enumerate(decisions):
            if decision is None:
                if index == 0 and abort_if_first_fails:
                    return {"round_resolved": False, "first_cast_success": False}
                continue

            actor, skill, target = decision
            if actor is None or actor.hp <= 0:
                if index == 0 and abort_if_first_fails:
                    return {"round_resolved": False, "first_cast_success": False}
                continue

            if self._is_chaos_random_active(actor):
                self._schedule_chaos_random_action(actor)
                continue

            if skill is None:
                if index == 0 and abort_if_first_fails:
                    return {"round_resolved": False, "first_cast_success": False}
                continue

            energy_cost = max(0, getattr(skill, "energy_cost", 0))
            if getattr(actor, "energy", 0) < energy_cost:
                if log:
                    log(f"{actor.name} 能量不足，无法使用 {skill.name}（需要 {energy_cost} 点）。")
                self.effects.clear()
                self._common_move_requests.clear()
                return {
                    "round_resolved": False,
                    "first_cast_success": index != 0,
                    "failure_reason": "energy",
                    "failed_actor": actor,
                    "failed_skill": skill,
                    "required_energy": energy_cost,
                }

            before_effect_count = len(self.effects)
            before_energy = getattr(actor, "energy", 0)
            result = skill.cast(state=self, caster=actor, target=target, log=log)
            added_effects = len(self.effects) > before_effect_count
            cast_success = (result is not False) and (result is True or added_effects)

            if cast_success:
                after_energy = getattr(actor, "energy", 0)
                already_spent = energy_cost > 0 and after_energy != before_energy
                if not already_spent:
                    self.push(2, actor, self._handle_energy_cost,
                              target=actor, amount=energy_cost, skill=skill)
            elif index == 0:
                first_cast_success = False
                if abort_if_first_fails:
                    self.effects.clear()
                    self._common_move_requests.clear()
                    return {"round_resolved": False, "first_cast_success": False}

        # 玩家主动技能已确认成功后，再加入回合开始/持续状态效果。
        # 这样点错技能不会推进毒伤、隐身递减、复活等状态。
        for char, skills in self.all_skills.items():
            for skill in skills:
                skill.on_turn_start(state=self, caster=char, log=log)

        # Sort by priority, tiebreak by actor order
        actor_order = {}
        if decision_a and decision_a[0] is not None:
            actor_order[decision_a[0]] = 0
        if decision_b and decision_b[0] is not None:
            actor_order[decision_b[0]] = 1
        self.effects.sort(key=lambda e: (e.priority, actor_order.get(e.actor, 99)))

        # Silence filter (engine-held)
        _silence_fn = self._handler_id(self._handle_silence)
        _filter_funcs = {self._handler_id(self._apply_damage),
                         self._handler_id(self._apply_move),
                         self._handler_id(self._apply_status)}
        for e in list(self.effects):
            if self._handler_id(e.resolve_fn) == _silence_fn:
                target = e.data["target"]
                self.effects = [ef for ef in self.effects
                                if not (ef.actor is target
                                        and self._handler_id(ef.resolve_fn) in _filter_funcs)]

        # Dispatch。结算中追加的效果（如反击）也会继续按优先级执行。
        while self.effects:
            self.effects.sort(key=lambda e: (e.priority, actor_order.get(e.actor, 99)))
            e = self.effects.pop(0)
            e.resolve_fn(e.data, self, log, e.actor)

        self._advance_chaos_random_states(chaos_random_active_this_round, log)

        # Death prevention (persistent)
        for char in self.characters:
            if self._get_status(char, "death_immune") and char.hp <= 0:
                char.hp = 1
                if log:
                    log(f"{char.name} 触发不死效果！")

        # Death + draw
        if all(c.hp <= 0 for c in self.characters):
            for c in self.characters:
                c.hp = 1
            self.draw = True
            if log:
                log("双方同时倒下——平局！")

        roll_evade_rewards = self._roll_evade_reward_targets(decisions)

        # Clear one-turn booleans
        for char in self.characters:
            for key in ("dodge", "shield_wall", "counter_stance",
                        "first_hit_shield", "guard_direction",
                        "directional_guard", "invincible",
                        "roll_evade_pending"):
                self._clear_status(char, key)

        for char in roll_evade_rewards:
            self._set_status(char, "dodge", True)
            if log:
                log(f"{char.name} 翻滚避开了本轮攻击，获得闪避状态。")

        self._tick_duration_statuses(log)

        return {"round_resolved": True, "first_cast_success": first_cast_success}

    # ── effect handlers ──

    def _tick_duration_statuses(self, log=None):
        for char in self.characters:
            self._tick_duration_status(char, "war_defense_turns", "war_defense_reduce", log, "防御战令")
            self._tick_duration_status(char, "weak_damage_down_turns", "weak_damage_down", log, "虚弱")

    def _tick_duration_status(self, char, turn_key, effect_key, log=None, display_name="状态"):
        turns = int(self._get_status(char, turn_key, 0) or 0)
        if turns <= 0:
            return
        turns -= 1
        if turns <= 0:
            self._clear_status(char, turn_key)
            self._clear_status(char, effect_key)
            if log:
                log(f"{char.name} 的{display_name}效果结束。")
        else:
            self._set_status(char, turn_key, turns)

    def _roll_evade_reward_targets(self, decisions):
        rewards = []
        for decision in decisions:
            if decision is None:
                continue
            actor = decision[0]
            if actor is None or not self._get_status(actor, "roll_evade_pending"):
                continue
            enemy = self.get_enemy_of(actor)
            enemy_used_attack = any(
                other is not None
                and other[0] is enemy
                and self._is_attack_skill(other[1])
                for other in decisions
            )
            if enemy_used_attack and actor not in self._round_damage_taken:
                rewards.append(actor)
        return rewards

    @staticmethod
    def _is_attack_skill(skill):
        attack_skill_ids = {
            "normal_attack", "heavy_slash", "piercing_shot", "area_blast",
            "fire_tornado", "flame_sweep", "mud_eruption", "rock_spike",
            "life_drain", "sky_dive", "tongue_strike", "bone_explosion",
            "judgment_chain", "gallows_dance", "poison_shadow_dart",
            "bone_eroding_poison", "wound_cleave", "undying_blood_oath",
        }
        return getattr(skill, "skill_id", None) in attack_skill_ids

    def _is_chaos_random_active(self, character):
        return int(self._get_status(character, "chaos_random_turns", 0) or 0) > 0

    def _schedule_chaos_random_action(self, actor):
        self.push(0, actor, self._log,
                  message=f"{actor.name} 处于乱魂状态，本回合无法自主释放技能，只会随机移动。")
        self.push(0.07, actor, self._handle_energy_drain,
                  target=actor, amount=8, reason="乱魂状态")
        self.push(3.0, actor, self._apply_random_move, target=actor)

    def _advance_chaos_random_states(self, active_this_round, log):
        for char in self.characters:
            current = int(self._get_status(char, "chaos_random_turns", 0) or 0)
            pending = int(self._get_status(char, "_chaos_random_pending", 0) or 0)

            remaining = current
            if char in active_this_round:
                remaining = max(0, current - 1)

            new_turns = max(remaining, pending)
            if new_turns > 0:
                self._set_status(char, "chaos_random_turns", new_turns)
            else:
                self._clear_status(char, "chaos_random_turns")

            if pending > 0:
                self._clear_status(char, "_chaos_random_pending")
                if log:
                    log(f"{char.name} 将从下一回合开始进入乱魂随机移动状态，持续 {pending} 回合。")
            elif char in active_this_round and current > 0 and new_turns == 0:
                if log:
                    log(f"{char.name} 摆脱了乱魂随机移动状态。")

    def _log(self, data, state, log, actor=None):
        if log and "message" in data:
            log(data["message"])

    def _apply_damage(self, data, state, log, actor=None):
        actor = actor or data.get("actor")
        target = data["target"]

        if not self._damage_hit_check(data, target, actor, log):
            return

        max_dist = data.get("max_dist")
        if max_dist is not None:
            if actor is not None and self._get_status(actor, "range_boost"):
                max_dist += 1
            if actor is None or self.distance(actor.pos, target.pos) > max_dist:
                if log and actor is not None:
                    log(f"{actor.name} 的攻击距离不足。")
                return

        amount = data["amount"]
        ignore_defense = data.get("ignore_defense", False)

        s = target.special_state
        if self._get_status(target, "invincible"):
            if log: log(f"{target.name} 处于无敌状态。")
            return
        if self._get_status(target, "dodge"):
            self._clear_status(target, "dodge")
            if log: log(f"{target.name} 闪避了伤害！")
            return

        if amount > 0 and self._get_status(target, "first_hit_shield"):
            self._clear_status(target, "first_hit_shield")
            if log:
                log(f"{target.name} 的战令护盾抵消了首次伤害。")
            return

        guard_direction = self._get_status(target, "guard_direction")
        if guard_direction and not data.get("is_area", False) and actor is not None:
            tr, tc = target.pos
            ar, ac = actor.pos
            gr, gc = guard_direction
            same_guarded_column = gc == 0 and ac == tc and (ar - tr) * gr > 0
            same_guarded_row = gr == 0 and ar == tr and (ac - tc) * gc > 0
            if same_guarded_column or same_guarded_row:
                if log:
                    log(f"{target.name} 格挡了来自该方向的攻击。")
                return

        # 维度换位反弹：攻击者伤害自己
        if actor is not None and actor.special_state.get("redirect_self"):
            target = actor
            actor.special_state.pop("redirect_self", None)
            actor.status.pop("redirect_self", None)
            if log: log(f"{target.name} 的攻击被反弹！")
            s = target.special_state

        if actor is not None and self._get_status(actor, "attack_boost") and not data.get("no_attack_boost", False):
            amount += 5
            if log:
                log(f"{actor.name} 的战令强化使伤害 +5。")
        if self._get_status(target, "shield_wall"):
            amount = int(amount * 0.3)
        if actor is not None and actor.special_state.get("weakened"):
            amount = max(0, amount - 5)
            actor.special_state.pop("weakened", None)
            actor.status.pop("weakened", None)
            if log: log(f"{actor.name} 攻击力被削弱，伤害 -5。")
        weak_down = int(self._get_status(actor, "weak_damage_down", 0) or 0) if actor is not None else 0
        if weak_down > 0 and amount > 0:
            amount = max(0, amount - weak_down)
            if log:
                log(f"{actor.name} 处于虚弱状态，伤害 -{weak_down}。")
        war_defense = int(self._get_status(target, "war_defense_reduce", 0) or 0)
        if war_defense > 0 and amount > 0 and not ignore_defense:
            amount = max(0, amount - war_defense)
            if log:
                log(f"{target.name} 的防御战令使伤害 -{war_defense}。")
        # 防御值机制已删除：所有角色等效 defense=0，攻击直接造成全额伤害。
        # ignore_defense 参数保留给旧技能兼容，但现在不再改变伤害。

        if (amount > 0 and actor is not None
                and self._get_status(target, "counter_stance")
                and not data.get("counter_reflect", False)):
            reflected = amount
            amount = int(amount * 0.5)
            self.effects.append(Effect(5.9, target, self._apply_damage,
                                       target=actor, amount=reflected,
                                       counter_reflect=True))
            self._clear_status(target, "counter_stance")
            if log:
                log(f"{target.name} 的反击姿态触发，返还 {reflected} 点伤害并自身承受 50%。")

        shield = getattr(target, "shield", 0)
        if shield > 0:
            blocked = min(shield, amount)
            amount -= blocked
            target.shield -= blocked
        target.hp = max(0, target.hp - amount)
        if amount > 0:
            self._round_damage_taken.add(target)
        if log:
            log(f"{target.name} 受到 {amount} 点伤害。")

        # 伤害命中后续效果（血痕、冷却等），仅在伤害实际生效时触发
        if amount > 0:
            for effect_data in data.get("on_hit_effects", []):
                fn = effect_data["fn"]
                fn(effect_data["data"], state, log, actor)

        if False and amount > 0 and target.special_state.get("counter_stance"):
            self.effects.append(Effect(5.9, target, self._apply_damage,
                                       actor=target, target=actor, amount=10))
            self._clear_status(target, "counter_stance")
            if log: log(f"{target.name} 的反击姿态触发！")

    def _damage_hit_check(self, data, target, actor=None, log=None):
        """Return True only when the target is inside the selected hit shape.

        Skills may pass one of the following optional keys:
        - hit_cell: exact selected grid.
        - hit_area: iterable of selected grids.
        - hit_ray: {"origin": (r,c), "direction": (dr,dc)}; target must be on that ray.
        - hit_line: {"axis": "row"/"col", "value": int}; target must be on that row/col.
        Old skills that do not pass any key keep their original lock-on behavior.
        """
        if target is None:
            return False

        skill_name = data.get("skill_name", "攻击")

        hit_cell = data.get("hit_cell")
        if hit_cell is not None and tuple(target.pos) != tuple(hit_cell):
            if log and data.get("log_miss", True):
                name = getattr(actor, "name", "角色") if actor is not None else "角色"
                log(f"{name} 的{skill_name}未命中。")
            return False

        hit_area = data.get("hit_area")
        if hit_area is not None:
            area = {tuple(cell) for cell in hit_area}
            if tuple(target.pos) not in area:
                if log and data.get("log_miss", True):
                    name = getattr(actor, "name", "角色") if actor is not None else "角色"
                    log(f"{name} 的{skill_name}未命中。")
                return False

        hit_line = data.get("hit_line")
        if hit_line is not None:
            axis = hit_line.get("axis")
            value = hit_line.get("value")
            tr, tc = target.pos
            if (axis == "row" and tr != value) or (axis == "col" and tc != value):
                if log and data.get("log_miss", True):
                    name = getattr(actor, "name", "角色") if actor is not None else "角色"
                    log(f"{name} 的{skill_name}未命中。")
                return False

        hit_ray = data.get("hit_ray")
        if hit_ray is not None:
            origin = hit_ray.get("origin")
            direction = hit_ray.get("direction")
            if origin is None or direction is None:
                return False
            orow, ocol = origin
            drow, dcol = direction
            trow, tcol = target.pos
            on_ray = False
            if drow == 0 and dcol != 0:
                on_ray = (trow == orow and (tcol - ocol) * dcol > 0)
            elif dcol == 0 and drow != 0:
                on_ray = (tcol == ocol and (trow - orow) * drow > 0)
            if not on_ray:
                if log and data.get("log_miss", True):
                    name = getattr(actor, "name", "角色") if actor is not None else "角色"
                    log(f"{name} 的{skill_name}未命中。")
                return False

        return True

    def _apply_status(self, data, state, log, actor=None):
        self._set_status(data["target"], data["key"], data["value"])

    def _apply_move(self, data, state, log, actor=None):
        target = data.get("target", actor)
        if target.special_state.get("mud_pool", 0) > 0:
            if log: log(f"{target.name} 陷入泥潭，无法移动。")
            return
        pos = data["pos"]
        if pos in self.mud_cells:
            if log:
                log(f"{target.name} 被泥潭阻碍，无法移动到 {pos}。")
            return
        target.pos = pos

    def _apply_random_move(self, data, state, log, actor=None):
        target = data.get("target", actor)
        if target is None:
            return
        if target.special_state.get("mud_pool", 0) > 0:
            if log: log(f"{target.name} 陷入泥潭，无法随机移动。")
            return

        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                if pos != target.pos and pos not in self.mud_cells and not self.is_occupied(r, c):
                    candidates.append(pos)

        if not candidates:
            if log: log(f"{target.name} 乱魂随机移动失败：场上没有可用空格。")
            return

        old_pos = target.pos
        target.pos = random.choice(candidates)
        if log:
            log(f"{target.name} 乱魂随机移动：{old_pos} → {target.pos}。")

    def _handle_chaos_backfire_area(self, data, state, log, actor=None):
        caster = actor
        enemy = data.get("target")
        top_left = data.get("top_left")
        if enemy is None or top_left is None:
            return

        row, col = top_left
        area = {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
        if enemy.pos not in area:
            if log:
                log(f"失控反噬未命中：{enemy.name} 不在以 {top_left} 为左上角的 2×2 区域内。")
            return

        if self._is_chaos_random_active(enemy):
            old_hp = enemy.hp
            enemy.hp = max(0, old_hp // 2)
            if log:
                log(f"失控反噬命中乱魂中的 {enemy.name}，其生命值从 {old_hp} 降至 {enemy.hp}。")
        else:
            self._set_status(enemy, "_chaos_random_pending", 2)
            if log:
                log(f"失控反噬命中 {enemy.name}，将使其从下一回合开始随机移动 2 回合。")

    def _handle_energy_drain(self, data, state, log, actor=None):
        target = data.get("target", actor)
        amount = max(0, data.get("amount", 0))
        if target is None or amount <= 0:
            return
        old_energy = getattr(target, "energy", 0)
        target.energy = max(0, old_energy - amount)
        if log:
            reason = data.get("reason", "状态")
            log(f"{target.name} 受{reason}影响，扣除 {old_energy - target.energy} 点能量。")

    def _handle_cooldown(self, data, state, log, actor=None):
        data["skill"].start_cooldown()

    def _handle_cd_reset(self, data, state, log, actor=None):
        data["skill"].current_cd = 0

    def _handle_shield(self, data, state, log, actor=None):
        data["target"].shield += data["amount"]

    def _handle_energy_cost(self, data, state, log, actor=None):
        target = data["target"]
        amount = max(0, data.get("amount", 0))
        if amount <= 0:
            return
        old_energy = getattr(target, "energy", 0)
        target.energy = max(0, old_energy - amount)
        if log:
            skill = data.get("skill")
            skill_name = getattr(skill, "name", "技能")
            log(f"{target.name} 使用{skill_name}消耗了 {old_energy - target.energy} 点能量。")

    def _kill_directly(self, data, state, log, actor=None):
        target = data.get("target", actor)
        if target is None:
            return
        # 直接死亡不清除 death_immune / _bone_revive，因此可被残骨重组救回。
        target.hp = 0
        if log:
            log(f"{target.name} {data.get('reason', '直接死亡')}。")

    def _handle_bone_explosion(self, data, state, log, actor=None):
        caster = actor
        enemy = data.get("target")
        if caster is None or enemy is None:
            return
        cr, cc = caster.pos
        er, ec = enemy.pos
        if abs(cr - er) > 1 or abs(cc - ec) > 3:
            # 回到原始机制：骨爆是否命中只看结算时敌人是否仍在 3×7 范围内。
            # 直接死亡不清除 death_immune/_bone_revive，因此残骨重组期间空爆可被救回。
            self._kill_directly({"target": caster, "reason": "同殒骨爆未命中敌方，反噬身亡"},
                                state, log, caster)
            return
        dmg = data.get("amount", 30)
        self._apply_damage({"target": enemy, "amount": dmg, "ignore_defense": True},
                           state, log, caster)
        self._apply_damage({"target": caster, "amount": dmg, "ignore_defense": True},
                           state, log, caster)
        if log:
            log(f"同殒骨爆命中，{caster.name} 与 {enemy.name} 各承受 {dmg} 点无视防御伤害。")

    def _handle_silence(self, data, state, log, actor=None):
        pass  # marker only; engine filters in resolve

    def _handle_death_prevent(self, data, state, log, actor=None):
        target = data["target"]
        if target.hp <= 0:
            target.hp = 1
            if log: log(f"{target.name} 触发不死效果！")

    # ── helpers ──

    def _handler_id(self, fn):
        return getattr(fn, "__func__", fn)

    def _get_status(self, character, key, default=None):
        if character is None:
            return default
        if key in getattr(character, "special_state", {}):
            return character.special_state.get(key, default)
        return getattr(character, "status", {}).get(key, default)

    def _set_status(self, character, key, value):
        if character is None:
            return
        if value is False or value is None or value == 0:
            self._clear_status(character, key)
            return
        character.special_state[key] = value
        character.status[key] = value

    def _clear_status(self, character, key):
        if character is None:
            return
        character.special_state.pop(key, None)
        character.status.pop(key, None)

    def clamp_pos(self, row, col):
        row = max(0, min(self.rows - 1, row))
        col = max(0, min(self.cols - 1, col))
        return row, col

    def in_bounds(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_occupied(self, row, col):
        pos = (row, col)
        return any(c.pos == pos for c in self.characters)

    def get_enemy_of(self, character):
        if character is self.player:
            return self.enemy
        return self.player

    def distance(self, a, b):
        ar, ac = a
        br, bc = b
        return abs(ar - br) + abs(ac - bc)
