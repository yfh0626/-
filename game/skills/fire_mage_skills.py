from skills.skill import Skill


class FireTornado(Skill):
    def __init__(self):
        super().__init__(
            skill_id="fire_tornado",
            name="火龙卷",
            description="消耗 50 点能量，选择中间行非边缘格，3×3 范围火焰爆发，造成 30 点伤害。",
            cooldown=4,
            target_required=True,
            energy_cost=50,
        )

    def cast(self, state, caster, target, log):
        if not _has_enough_energy(caster, self, log):
            return

        if target is None:
            log("火龙卷需要选择目标格。")
            return

        row, col = target
        middle_row = state.rows // 2
        if row != middle_row:
            log("火龙卷只能选择中间一行。")
            return

        if col <= 0 or col >= state.cols - 1:
            log("火龙卷不能选择中间行两边的格子。")
            return

        enemy = state.get_enemy_of(caster)
        area = {
            (r, c)
            for r in range(row - 1, row + 2)
            for c in range(col - 1, col + 2)
            if state.in_bounds(r, c)
        }
        _spend_energy(caster, self)
        state.push(5.12, caster, state._apply_damage, target=enemy, amount=30,
                   is_area=True, hit_area=area, skill_name=self.name)
        state.push(5.12, caster, state._handle_cooldown, skill=self)


class FlameSweep(Skill):
    def __init__(self):
        super().__init__(
            skill_id="flame_sweep",
            name="烈焰横扫",
            description="消耗 50 点能量，一整行火焰攻击，造成 30 点伤害。",
            cooldown=4,
            target_required=True,
            energy_cost=50,
        )

    def cast(self, state, caster, target, log):
        if not _has_enough_energy(caster, self, log):
            return

        if target is None:
            log("烈焰横扫需要选择目标格。")
            return

        cr, _ = caster.pos
        tr, _ = target
        if cr != tr:
            log("烈焰横扫只能选择同行格子。")
            return
        enemy = state.get_enemy_of(caster)
        _spend_energy(caster, self)
        state.push(5.11, caster, state._apply_damage, target=enemy, amount=30,
                   hit_line={"axis": "row", "value": tr}, skill_name=self.name)
        state.push(5.11, caster, state._handle_cooldown, skill=self)


def _has_enough_energy(caster, skill, log):
    if caster.energy < skill.energy_cost:
        log(f"{skill.name} 需要 {skill.energy_cost} 点能量。")
        return False
    return True


def _spend_energy(caster, skill):
    caster.energy = max(0, caster.energy - skill.energy_cost)
