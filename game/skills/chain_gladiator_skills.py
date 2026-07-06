from skills.skill import Skill


class JudgmentChain(Skill):
    def __init__(self):
        super().__init__(
            skill_id="judgment_chain",
            name="断罪锁链",
            description="首次选择 3 格内目标格牵制；牵制后再次选择 5 格内目标格结算伤害，伤害为 5 + 5×当前敌我距离。",
            cooldown=3,
            target_required=True,
            range=None,
            energy_cost=20,
        )

    def cast(self, state, caster, target, log):
        if target is None or not state.in_bounds(*target):
            log("断罪锁链需要选择场内目标格。")
            return False

        enemy = state.get_enemy_of(caster)
        if caster.special_state.get("chain_tethered"):
            if state.distance(caster.pos, target) > 5:
                log("断罪锁链二段结算距离不能超过 5 格。")
                return False

            dist = state.distance(caster.pos, enemy.pos)
            dmg = 5 + 5 * dist
            if target == enemy.pos and dist <= 5:
                state.push(5.18, caster, state._apply_damage,
                           target=enemy, amount=dmg, max_dist=5)
            else:
                state.push(0, caster, state._log,
                           message=f"{caster.name} 的断罪锁链没有命中。")

            state.push(5.18, caster, state._apply_status,
                       target=caster, key="chain_tethered", value=False)
            state.push(5.18, caster, state._apply_status,
                       target=caster, key="chain_target", value=None)
            state.push(5.18, caster, state._apply_status,
                       target=caster, key="chain_max_dist", value=None)
            state.push(5.18, caster, state._handle_cooldown, skill=self)
            return True

        if state.distance(caster.pos, target) > 3:
            log("断罪锁链首次牵制距离不能超过 3 格。")
            return False

        if target == enemy.pos:
            state.push(3.8, caster, state._apply_status,
                       target=caster, key="chain_tethered", value=True)
            state.push(3.8, caster, state._apply_status,
                       target=caster, key="chain_target", value=enemy.name)
            state.push(3.8, caster, state._apply_status,
                       target=caster, key="chain_max_dist", value=3)
            state.push(0, caster, state._log,
                       message=f"{caster.name} 投出锁链牵制 {enemy.name}。")
        else:
            state.push(0, caster, state._log,
                       message=f"{caster.name} 的断罪锁链没有命中。")
        state.push(3.8, caster, state._handle_cooldown, skill=self)
        return True


class GallowsDance(Skill):
    def __init__(self):
        super().__init__(
            skill_id="gallows_dance",
            name="绞刑轮舞",
            description="攻击自身周围4格敌人：无锁链造成 15 点，有锁链造成 25 点，并缩小锁距、降低对方攻击。",
            cooldown=3,
            target_required=False,
            energy_cost=30,
        )

    def cast(self, state, caster, target, log):
        enemy = state.get_enemy_of(caster)
        cr, cc = caster.pos

        adjacent = any((cr + dr, cc + dc) == enemy.pos
                       for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)])

        if caster.special_state.get("chain_tethered"):
            if adjacent:
                new_max = max(1, caster.special_state.get("chain_max_dist", 3) - 1)
                state.push(3.9, caster, state._apply_status,
                           target=caster, key="chain_max_dist", value=new_max)
                state.push(0, caster, state._log, message=f"{caster.name} 缩小锁距至 {new_max}。")

                state.push(3.91, caster, state._apply_status,
                           target=enemy, key="weakened", value=True)
                state.push(0, caster, state._log, message=f"{enemy.name} 攻击力降低（单次有效）。")

                state.push(5.19, caster, state._apply_damage, target=enemy, amount=25)
            else:
                state.push(0, caster, state._log, message="敌人不在绞刑轮舞范围内。")
            state.push(5.19, caster, state._handle_cooldown, skill=self)
        else:
            if adjacent:
                state.push(5.15, caster, state._apply_damage, target=enemy, amount=15)
            else:
                state.push(0, caster, state._log, message="敌人不在绞刑轮舞范围内。")
            state.push(5.15, caster, state._handle_cooldown, skill=self)

        state.push(0, caster, state._log, message=f"{caster.name} 使用绞刑轮舞。")
        return True
