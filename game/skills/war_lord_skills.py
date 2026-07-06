from skills.skill import Skill


class WarCommandForms(Skill):
    def __init__(self):
        super().__init__(
            skill_id="war_command_forms",
            name="战令三式",
            description=(
                "连续释放三段战令：壹段位移距离 +1 并首次受击免疫；"
                "贰段伤害技能伤害 +5、攻击范围 +1；"
                "叁段获得防御战令，每次受伤减少 3 点，持续 3 轮。"
            ),
            cooldown=3,
            target_required=False,
            energy_cost=0,
        )
        # 0=下一次释放壹段，1=下一次释放贰段，2=下一次释放叁段。
        self.phase = 0

    def cast(self, state, caster, target, log):
        self._clear_form_buffs(caster)

        if self.phase == 0:
            caster.status["move_boost"] = True
            caster.status["first_hit_shield"] = True
            caster.special_state["move_boost"] = True
            caster.special_state["first_hit_shield"] = True
            self.phase = 1
            if log:
                log("战令三式·壹：位移距离 +1，首次受击免疫。")
            return True

        if self.phase == 1:
            caster.status["attack_boost"] = True
            caster.status["range_boost"] = True
            caster.special_state["attack_boost"] = True
            caster.special_state["range_boost"] = True
            self.phase = 2
            if log:
                log("战令三式·贰：所有伤害技能伤害 +5，攻击范围 +1。")
            return True

        state.push(0.18, caster, state._apply_status,
                   target=caster, key="war_defense_reduce", value=3)
        state.push(0.18, caster, state._apply_status,
                   target=caster, key="war_defense_turns", value=3)
        state.push(0.19, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log,
                   message="战令三式·叁：获得防御战令，受伤减少 3 点，持续 3 轮。")
        self.phase = 0
        return True

    @staticmethod
    def _clear_form_buffs(caster):
        for key in ("move_boost", "first_hit_shield", "attack_boost", "range_boost"):
            caster.status.pop(key, None)
            caster.special_state.pop(key, None)


class KingMightFormation(Skill):
    def __init__(self):
        super().__init__(
            skill_id="king_might_formation",
            name="王威压阵",
            description=(
                "获得 1 点战意。战意不足 2 点时命中敌人施加虚弱，"
                "使其所有伤害 -2，持续 2 轮；战意达到 2 点时消耗 2 点战意追击相邻敌人，造成 30 点伤害。"
            ),
            cooldown=2,
            target_required=True,
            energy_cost=20,
        )

    def cast(self, state, caster, target, log):
        if target is None or not state.in_bounds(*target):
            log("王威压阵需要选择场内目标格。")
            return False

        enemy = state.get_enemy_of(caster)
        caster.status["war_intent"] = caster.status.get("war_intent", 0) + 1
        caster.special_state["war_intent"] = caster.status["war_intent"]

        if caster.status["war_intent"] >= 2:
            caster.status["war_intent"] -= 2
            caster.special_state["war_intent"] = caster.status["war_intent"]
            if target == enemy.pos and state.distance(caster.pos, target) <= 1:
                state.push_damage(enemy, 30, source=caster)
                log(f"{caster.name} 消耗 2 点战意追击，造成 30 点伤害。")
            else:
                caster.status["war_intent"] += 1
                caster.special_state["war_intent"] = caster.status["war_intent"]
                log("王威压阵追击没有命中。")
        else:
            if target == enemy.pos:
                state.push_status(enemy, "weak_damage_down", 2, source=caster)
                state.push_status(enemy, "weak_damage_down_turns", 2, source=caster)
                log(f"{caster.name} 展开压阵，{enemy.name} 虚弱：所有伤害 -2，持续 2 轮。")
            else:
                log("王威压阵没有命中。")

        self.start_cooldown()
        return True
