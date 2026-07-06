from skills.skill import Skill
from core.movement import same_line


class WoundCleave(Skill):
    def __init__(self): super().__init__(skill_id="wound_cleave", name="裂创斩", description="朝同线最多 2 格的方向斩击，命中敌人时叠加血痕。", cooldown=2, target_required=True, range=2, energy_cost=25)

    def cast(self, state, caster, target, log):
        if target is None or not state.in_bounds(*target):
            log("裂创斩需要选择场内目标格。")
            return False
        if not same_line(caster.pos, target) or target == caster.pos:
            log("裂创斩只能选择同行或同列的方向格。")
            return False
        max_range = 2 + _range_bonus(caster)
        if state.distance(caster.pos, target) > max_range:
            log(f"裂创斩距离不能超过 {max_range} 格。")
            return False
        enemy = state.get_enemy_of(caster)
        marks = enemy.special_state.get("blood_mark", 0)
        dmg = 12 + 4 * marks
        rage = caster.special_state.get("blood_rage", 0)
        if rage > 0:
            dmg += 5
        state.push(5.17, caster, state._apply_damage, target=enemy, amount=dmg,
                   max_dist=2, hit_ray={"origin": caster.pos, "direction": _direction(caster.pos, target)},
                   skill_name=self.name,
                   on_hit_effects=[{
                       "fn": self._apply_wound_on_hit,
                       "data": {"target": enemy, "marks": marks + 1, "rage": rage, "caster": caster},
                   }])
        state.push(5.17, caster, state._handle_cooldown, skill=self)
        return True

    def _apply_wound_on_hit(self, data, state, log, actor=None):
        enemy = data.get("target")
        caster = data.get("caster") or actor
        if enemy is not None:
            state._set_status(enemy, "blood_mark", data.get("marks", 1))
        rage = data.get("rage", 0)
        if caster is not None and rage > 0:
            state._set_status(caster, "blood_rage", rage - 1)


class UndyingBloodOath(Skill):
    def __init__(self): super().__init__(skill_id="undying_blood_oath", name="血誓不灭", description="血量低于 35% 时进入血誓状态；转化后可朝同线 3 格方向横扫。", cooldown=6, target_required=False, energy_cost=10)
    def cast(self,state,caster,target,log):
        threshold=int(caster.max_hp*0.35)
        if caster.hp>threshold: log(f"血量高于 35%，无法使用血誓不灭（当前 HP：{caster.hp}）。"); return
        enemy=state.get_enemy_of(caster)
        if caster.special_state.get("transformed"):
            if target is None or not state.in_bounds(*target): log("血誓横扫需要选择场内目标格。"); return
            if not same_line(caster.pos,target) or target==caster.pos: log("血誓横扫只能选择同行或同列的方向格。"); return
            max_range = 3 + _range_bonus(caster)
            if state.distance(caster.pos, target) > max_range:
                log(f"血誓横扫距离不能超过 {max_range} 格。")
                return False
            dmg=int((caster.max_hp-caster.hp)*0.5)+10
            state.push(5.23,caster,state._apply_damage,target=enemy,amount=dmg,max_dist=3,
                       hit_ray={"origin": caster.pos, "direction": _direction(caster.pos, target)},
                       skill_name="血誓横扫",
                       on_hit_effects=[{
                           "fn": self._clear_blood_mark_on_hit,
                           "data": {"target": enemy},
                       }])
            state.push(5.23,caster,state._handle_cooldown,skill=self); return True
        state.push(0.2,caster,state._apply_status,target=caster,key="death_immune",value=True); state.push(0.2,caster,state._apply_status,target=caster,key="vow_active",value=2); state.push(0.2,caster,state._apply_status,target=caster,key="transformed",value=True); state.push(0.3,caster,state._apply_status,target=caster,key="blood_rage",value=caster.special_state.get("blood_rage",0)+2); state.push(0.3,caster,state._handle_cd_reset,skill=self); state.push(0.3,caster,state._log,message=f"{caster.name} 进入血誓状态！获得不死和 2 层血怒。")
    def _clear_blood_mark_on_hit(self, data, state, log, actor=None):
        enemy = data.get("target")
        if enemy is not None:
            state._set_status(enemy, "blood_mark", 0)

    def on_turn_start(self,state,caster,log):
        vow=caster.special_state.get("vow_active",0)
        if vow>0:
            vow-=1; state.push(0.2,caster,state._apply_status,target=caster,key="vow_active",value=vow)
            if vow<=0: state.push(0.2,caster,state._apply_status,target=caster,key="death_immune",value=False)


def _range_bonus(caster):
    return 1 if getattr(caster, "status", {}).get("range_boost") else 0


def _direction(caster_pos, target):
    cr, cc = caster_pos
    tr, tc = target
    if tr == cr:
        return (0, 1 if tc > cc else -1)
    return (1 if tr > cr else -1, 0)
