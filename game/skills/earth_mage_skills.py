from skills.skill import Skill


class MudEruption(Skill):
    def __init__(self):
        super().__init__(
            skill_id="mud_eruption",
            name="泥潭迸发",
            description="消耗 40 点能量。首次选择一个格子留下泥潭；场上已有泥潭时，再释放会引爆泥潭周围造成 20 点伤害。",
            cooldown=3,
            target_required=False,
            energy_cost=40,
        )

    def cast(self, state, caster, target, log):
        enemy = state.get_enemy_of(caster)
        had_mud = bool(state.mud_cells)

        if had_mud:
            if not _has_enough_energy(caster, self, log):
                return False

            mud_cell = next(iter(state.mud_cells))
            area = self._cross_area(state, mud_cell)
            state.push(3.6, caster, state._apply_damage, target=enemy, amount=20,
                       ignore_defense=True, is_area=True, hit_area=area,
                       skill_name=self.name)
            _spend_energy(caster, self)
            state.mud_cells.clear()
            state.push(3.6, caster, state._handle_cooldown, skill=self)
            log(f"{caster.name} 引爆 {mud_cell} 的泥潭。")
            return True

        if target is None or not state.in_bounds(*target):
            log("泥潭迸发需要先选择一个场内格子留下泥潭。")
            return False

        if not _has_enough_energy(caster, self, log):
            return False

        _spend_energy(caster, self)
        state.mud_cells.add(target)
        state.push(3.6, caster, state._handle_cooldown, skill=self)
        log(f"{caster.name} 在 {target} 留下泥潭。")
        return True

    def _cross_area(self, state, center):
        row, col = center
        cells = [
            (row, col),
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        ]
        return {cell for cell in cells if state.in_bounds(*cell)}


class RockSpike(Skill):
    def __init__(self):
        super().__init__(skill_id="rock_spike", name="岩突震荡",
            description="消耗 40 点能量。选择自己同行或同列的方向格，敌人在该方向直线上时造成 20 点伤害。", cooldown=4, target_required=True, energy_cost=40)

    def cast(self, state, caster, target, log):
        if target is None or not state.in_bounds(*target):
            log("岩突震荡需要选择一个场内格子。")
            return False
        cr, cc = caster.pos
        tr, tc = target
        if (cr != tr and cc != tc) or target == caster.pos:
            log("岩突震荡只能选择同行或同列的方向格。")
            return False
        if not _has_enough_energy(caster, self, log):
            return False
        _spend_energy(caster, self)
        enemy = state.get_enemy_of(caster)
        direction = _direction(caster.pos, target)
        state.push(5.22, caster, state._apply_damage, target=enemy, amount=20,
                   ignore_defense=True, is_area=True,
                   hit_ray={"origin": caster.pos, "direction": direction},
                   skill_name=self.name)
        state.push(5.22, caster, state._handle_cooldown, skill=self)
        return True


def _direction(caster_pos, target):
    cr, cc = caster_pos
    tr, tc = target
    if tr == cr:
        return (0, 1 if tc > cc else -1)
    return (1 if tr > cr else -1, 0)


def _has_enough_energy(caster, skill, log):
    if caster.energy < skill.energy_cost:
        log(f"{skill.name} 需要 {skill.energy_cost} 点能量。")
        return False
    return True


def _spend_energy(caster, skill):
    caster.energy = max(0, caster.energy - skill.energy_cost)
