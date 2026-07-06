from skills.skill import Skill


class BoneExplosion(Skill):
    def __init__(self):
        super().__init__(
            skill_id="bone_explosion",
            name="同殒骨爆",
            description="结算时若敌人在 3×7 范围内，双方各受 30 点无视防御伤害；若敌人已离开范围，则自身直接死亡，但可被残骨重组救回。",
            cooldown=4,
            target_required=False,
            energy_cost=25,
        )

    def cast(self, state, caster, target, log):
        state.push(5.25, caster, state._handle_bone_explosion,
                   target=state.get_enemy_of(caster), amount=30)
        state.push(5.25, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log,
                   message=f"{caster.name} 引发同殒骨爆，结算时若敌人在范围内双方各受 30 点伤害。")
        return True


class BoneRebuild(Skill):
    def __init__(self):
        super().__init__(
            skill_id="bone_rebuild",
            name="残骨重组",
            description="进入残骨状态，第一次死亡时复活并恢复到 35 点生命。",
            cooldown=20,
            target_required=False,
            energy_cost=40,
        )

    def cast(self, state, caster, target, log):
        state.push(0.15, caster, state._apply_status,
                   target=caster, key="death_immune", value=True)
        state.push(0.15, caster, state._apply_status,
                   target=caster, key="_bone_revive", value=True)
        state.push(0.15, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 进入残骨状态，受到致命伤害时将复活。")
        return True

    def on_turn_start(self, state, caster, log):
        if caster.special_state.get("_bone_revive") and caster.hp <= 1:
            caster.hp = min(caster.max_hp, 35)
            state.push(0.15, caster, state._apply_status,
                       target=caster, key="death_immune", value=False)
            state.push(0.15, caster, state._apply_status,
                       target=caster, key="_bone_revive", value=False)
            if log:
                log(f"{caster.name} 残骨重组触发，复活并恢复到 35 点生命。")
        return True
