from skills.skill import Skill


class FrenzyCurse(Skill):
    def __init__(self):
        super().__init__(
            skill_id="frenzy_curse",
            name="疯咒乱魂",
            description="锁定命中敌人；敌人从下一回合开始随机移动 2 回合，期间每回合扣除 8 点能量。",
            cooldown=6,
            target_required=False,
            range=None,
            energy_cost=30,
        )

    def cast(self, state, caster, target, log):
        enemy = state.get_enemy_of(caster)
        state.push(0.06, caster, state._apply_status,
                   target=enemy, key="_chaos_random_pending", value=2)
        state.push(0.06, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log,
                   message=f"{caster.name} 释放疯咒乱魂，锁定命中 {enemy.name}；效果将从下一回合开始。")
        return True


class ChaosBackfire(Skill):
    def __init__(self):
        super().__init__(
            skill_id="chaos_backfire",
            name="失控反噬",
            description="选择一个 2×2 区域的左上角。命中乱魂中的敌人时使其当前生命值减半；否则使其从下一回合开始随机移动 2 回合。",
            cooldown=9,
            target_required=True,
            range=None,
            energy_cost=40,
        )

    def cast(self, state, caster, target, log):
        if target is None:
            log("失控反噬需要选择 2×2 区域的左上角。")
            return False

        row, col = target
        if not state.in_bounds(row, col) or not state.in_bounds(row + 1, col + 1):
            log("失控反噬请选择 2×2 区域的左上角，不能选择最下行或最右列。")
            return False

        enemy = state.get_enemy_of(caster)
        state.push(5.26, caster, state._handle_chaos_backfire_area,
                   target=enemy, top_left=target)
        state.push(5.26, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log,
                   message=f"{caster.name} 选择以 {target} 为左上角的 2×2 区域释放失控反噬。")
        return True
