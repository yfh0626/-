from skills.skill import Skill


class AstralProtection(Skill):
    def __init__(self):
        super().__init__(
            skill_id="astral_protection",
            name="星界庇护",
            description="消耗 30 点能量，下一轮处于无敌状态。",
            cooldown=3,
            target_required=False,
            energy_cost=30,
        )

    def cast(self, state, caster, target, log):
        if not _has_enough_energy(caster, self, log):
            return False

        _spend_energy(caster, self)
        state.push(0.05, caster, state._apply_status,
                   target=caster, key="_astral_pending", value=True)
        state.push(0.05, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 进入星界庇护，下一轮无敌。")

    def on_turn_start(self, state, caster, log):
        if caster.special_state.get("_astral_pending"):
            state.push(0.05, caster, state._apply_status,
                       target=caster, key="invincible", value=True)
            state.push(0.05, caster, state._apply_status,
                       target=caster, key="_astral_pending", value=False)
        else:
            state.push(0.05, caster, state._apply_status,
                       target=caster, key="invincible", value=False)


class DimensionSwap(Skill):
    def __init__(self):
        super().__init__(skill_id="dimension_swap", name="维度换位", description="消耗 30 点能量，选择目标格；敌人在目标格时交换位置，并使敌方本轮攻击反弹给自身。", cooldown=3, target_required=True, energy_cost=30)
    def cast(self,state,caster,target,log):
        if target is None or not state.in_bounds(*target): log("维度换位需要选择场内目标格。"); return False
        if not _has_enough_energy(caster,self,log): return False
        enemy=state.get_enemy_of(caster); old_caster_pos=caster.pos; _spend_energy(caster,self)
        if enemy.pos==target:
            state.push(3.7,caster,state._apply_move,pos=enemy.pos); state.push(3.7,caster,state._apply_move,target=enemy,pos=old_caster_pos); state.push(3.7,caster,state._apply_status,target=enemy,key="redirect_self",value=True); state.push(0,caster,state._log,message=f"{caster.name} 使用维度换位，与 {enemy.name} 交换位置。")
        else: state.push(0,caster,state._log,message=f"{caster.name} 的维度换位没有命中。")
        state.push(3.7,caster,state._handle_cooldown,skill=self); return True


def _has_enough_energy(caster, skill, log):
    if caster.energy < skill.energy_cost:
        log(f"{skill.name} 需要 {skill.energy_cost} 点能量。")
        return False
    return True


def _spend_energy(caster, skill):
    caster.energy = max(0, caster.energy - skill.energy_cost)
