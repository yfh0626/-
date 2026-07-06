from skills.skill import Skill


class SkyDive(Skill):
    def __init__(self):
        super().__init__(
            skill_id="sky_dive",
            name="俯天急袭",
            description="飞到场上任意空格。若落点距离敌人不超过 1 格，则造成 20 点伤害。",
            cooldown=4,
            target_required=True,
            energy_cost=25,
        )

    def cast(self, state, caster, target, log):
        if target is None:
            log("俯天急袭需要选择目标格。")
            return False
        row, col = state.clamp_pos(target[0], target[1])
        target = (row, col)
        if state.is_occupied(*target):
            log("目标格被占用。")
            return False
        state.push(3.61, caster, state._apply_move, pos=target)
        enemy = state.get_enemy_of(caster)
        area = {
            (r, c)
            for r in range(target[0] - 1, target[0] + 2)
            for c in range(target[1] - 1, target[1] + 2)
            if state.in_bounds(r, c)
        }
        state.push(5.24, caster, state._apply_damage, target=enemy, amount=20,
                   hit_area=area, skill_name=self.name)
        state.push(5.24, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 俯天急袭飞到 {target}。")
        return True


class FeatherMark(Skill):
    def __init__(self):
        super().__init__(
            skill_id="feather_mark",
            name="坠羽印记",
            description="选一列留下印记。若敌人在印记列则每轮受到 10 点伤害，最后一轮爆炸造成 20 点伤害。",
            cooldown=6,
            target_required=True,
            energy_cost=30,
        )

    def cast(self, state, caster, target, log):
        if target is None:
            log("坠羽印记需要选择目标列。")
            return False
        _, col = state.clamp_pos(target[0], target[1])
        state.push(4.6, caster, state._apply_status,
                   target=caster, key="feather_col", value=col)
        state.push(4.6, caster, state._apply_status,
                   target=caster, key="feather_turns", value=3)
        state.push(4.6, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 在列 {col} 留下坠羽印记，持续 3 轮。")
        return True

    def on_turn_start(self, state, caster, log):
        turns = caster.special_state.get("feather_turns", 0)
        if turns <= 0:
            return
        enemy = state.get_enemy_of(caster)
        col = caster.special_state.get("feather_col")
        if enemy.pos[1] != col:
            return
        turns -= 1
        if turns <= 0:
            dmg = 20
            state.push(5.5, caster, state._apply_status,
                       target=caster, key="feather_turns", value=0)
        else:
            dmg = 10
            state.push(5.5, caster, state._apply_status,
                       target=caster, key="feather_turns", value=turns)
        state.push(5.5, caster, state._apply_damage, target=enemy, amount=dmg,
                   ignore_defense=True)
        state.push(0, caster, state._log,
                   message=f"坠羽印记{'爆炸' if turns <= 0 else '触发'}，{enemy.name} 受到 {dmg} 点伤害。")
