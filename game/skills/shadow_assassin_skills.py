from skills.skill import Skill
from core.movement import same_line


class PoisonShadowDart(Skill):
    def __init__(self):
        super().__init__(
            skill_id="poison_shadow_dart",
            name="毒影飞镖",
            description="选择同行或同列的方向格；敌人在该方向直线上时造成 15 点伤害并中毒 3 回合，每轮 5 点毒伤。",
            cooldown=4,
            target_required=True,
            energy_cost=25,
        )

    def cast(self, state, caster, target, log):
        if target is None or not state.in_bounds(*target):
            log("毒影飞镖需要选择场内目标格。")
            return False
        if not same_line(caster.pos, target) or target == caster.pos:
            log("毒影飞镖只能选择同行或同列的方向格。")
            return False
        enemy = state.get_enemy_of(caster)
        state.push(5.2, caster, state._apply_damage, target=enemy, amount=15,
                   hit_ray={"origin": caster.pos, "direction": _direction(caster.pos, target)},
                   skill_name=self.name,
                   on_hit_effects=[{
                       "fn": self._apply_poison_on_hit,
                       "data": {"target": enemy},
                   }])
        state.push(5.2, caster, state._handle_cooldown, skill=self)
        return True

    def _apply_poison_on_hit(self, data, state, log, actor=None):
        enemy = data.get("target")
        if enemy is None:
            return
        state._set_status(enemy, "poison", 3)
        if log:
            caster_name = getattr(actor, "name", "角色") if actor is not None else "角色"
            log(f"{caster_name} 掷出毒影飞镖，{enemy.name} 中毒 3 回合。")

    def on_turn_start(self, state, caster, log):
        enemy = state.get_enemy_of(caster)
        poison = enemy.special_state.get("poison", 0)
        if poison > 0:
            state.push(5.21, caster, state._apply_damage, target=enemy, amount=5, ignore_defense=True)
            state.push(5.21, caster, state._apply_status, target=enemy, key="poison", value=poison - 1)
            state.push(5.21, caster, state._apply_status, target=caster, key="_poison_dmg", value=5)


class BoneErodingPoison(Skill):
    def __init__(self):
        super().__init__(
            skill_id="bone_eroding_poison",
            name="蚀骨催毒",
            description="选择同行或同列的方向格；命中中毒敌人时追加 10 点伤害，并在本轮毒伤结算后延长 2 回合中毒时间。",
            cooldown=4,
            target_required=True,
            energy_cost=25,
        )

    def cast(self, state, caster, target, log):
        if target is None or not state.in_bounds(*target):
            log("蚀骨催毒需要选择场内目标格。")
            return False
        if not same_line(caster.pos, target) or target == caster.pos:
            log("蚀骨催毒只能选择同行或同列的方向格。")
            return False
        enemy = state.get_enemy_of(caster)
        poison_turns = enemy.special_state.get("poison", 0)
        if not isinstance(poison_turns, int) or poison_turns <= 0:
            state.push(0, caster, state._log, message=f"{caster.name} 的蚀骨催毒没有生效。")
            state.push(5.205, caster, state._handle_cooldown, skill=self)
            return True
        state.push(5.205, caster, state._apply_damage, target=enemy, amount=10,
                   hit_ray={"origin": caster.pos, "direction": _direction(caster.pos, target)},
                   skill_name=self.name,
                   on_hit_effects=[{
                       "fn": self._queue_poison_extension_on_hit,
                       "data": {"target": enemy, "extra_turns": 2},
                   }])
        state.push(5.205, caster, state._handle_cooldown, skill=self)
        return True

    def _queue_poison_extension_on_hit(self, data, state, log, actor=None):
        enemy = data.get("target")
        if enemy is None:
            return
        state.push(5.23, actor, self._extend_poison_after_tick,
                   target=enemy, extra_turns=data.get("extra_turns", 2))

    def _extend_poison_after_tick(self, data, state, log, actor=None):
        enemy = data.get("target")
        if enemy is None:
            return
        extra_turns = int(data.get("extra_turns", 2) or 0)
        current = int(enemy.special_state.get("poison", 0) or 0)
        state._set_status(enemy, "poison", current + extra_turns)
        if log:
            log(f"{enemy.name} 的中毒时间延长 {extra_turns} 回合。")


def _direction(caster_pos, target):
    cr, cc = caster_pos
    tr, tc = target
    if tr == cr:
        return (0, 1 if tc > cc else -1)
    return (1 if tr > cr else -1, 0)
