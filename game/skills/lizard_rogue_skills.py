from skills.skill import Skill
from core.movement import same_line


class TongueStrike(Skill):
    def __init__(self): super().__init__(skill_id="tongue_strike", name="断舌奇袭", description="同线 3 格内选择目标格；命中敌人时拉近并造成伤害。", cooldown=4, target_required=True, range=3, energy_cost=23)

    def cast(self, state, caster, target, log):
        enemy = state.get_enemy_of(caster)
        if target is None or not state.in_bounds(*target):
            log("断舌奇袭需要选择场内目标格。")
            return False
        if state.distance(caster.pos, target) > 3:
            log("断舌奇袭距离不能超过 3 格。")
            return False
        if not same_line(caster.pos, target):
            log("断舌奇袭只能选择同行或同列的格子。")
            return False

        hit_cell = target
        if enemy.pos == target:
            cr, cc = caster.pos
            er, ec = enemy.pos
            if cr == er:
                ec = ec + (1 if cc > ec else -1)
            else:
                er = er + (1 if cr > er else -1)
            new_pos = state.clamp_pos(er, ec)
            if new_pos != caster.pos and not state.is_occupied(*new_pos):
                state.push(3.8, caster, state._apply_move, target=enemy, pos=new_pos)
                hit_cell = new_pos

        dmg = 28 if caster.special_state.get("invisible") else 20
        state.push(5.2, caster, state._apply_damage, target=enemy, amount=dmg,
                   hit_cell=hit_cell, skill_name=self.name)
        state.push(5.2, caster, state._handle_cooldown, skill=self)
        return True


class ChameleonCloak(Skill):
    def __init__(self):
        super().__init__(
            skill_id="chameleon_cloak",
            name="融影变色",
            description="进入隐身状态，持续两个回合；隐身时断舌奇袭伤害提高。",
            cooldown=5,
            target_required=False,
            energy_cost=35,
        )

    def cast(self, state, caster, target, log):
        # 本轮 4.7 结算后进入隐身；之后两个完整回合可享受隐身加成。
        # 第三个回合的行动和伤害结算仍有加成，随后在 5.95 显形。
        state.push(4.7, caster, state._apply_status,
                   target=caster, key="invisible", value=2)
        state.push(4.7, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 融入暗影，进入隐身。")
        return True

    def on_turn_start(self, state, caster, log):
        invisible_turns = caster.special_state.get("invisible", 0)
        if not isinstance(invisible_turns, int) or invisible_turns <= 0:
            return
        state.push(5.95, caster, self._tick_invisible, target=caster)

    def _tick_invisible(self, data, state, log, actor=None):
        target = data.get("target", actor)
        if target is None:
            return
        invisible_turns = target.special_state.get("invisible", 0)
        if not isinstance(invisible_turns, int) or invisible_turns <= 0:
            return
        next_turns = invisible_turns - 1
        state._set_status(target, "invisible", next_turns)
        if log and next_turns <= 0:
            log(f"{target.name} 的隐身在本轮结算后结束。")
