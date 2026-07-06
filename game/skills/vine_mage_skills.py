from skills.skill import Skill


class LifeDrain(Skill):
    def __init__(self):
        super().__init__(
            skill_id="life_drain",
            name="森罗汲取",
            description="消耗 40 点能量。选择 2×2 区域的左上角，若敌人在区域内则造成 20 点伤害。",
            cooldown=3,
            target_required=True,
            energy_cost=40,
        )

    def cast(self, state, caster, target, log):
        enemy = state.get_enemy_of(caster)
        area = self._normalize_2x2_area(state, target)

        if area is None:
            log("森罗汲取需要选择 2×2 区域的左上角，不能选择最下行或最右列。")
            return False

        if not _has_enough_energy(caster, self, log):
            return False

        _spend_energy(caster, self)
        state.push(5.13, caster, state._apply_damage, target=enemy, amount=20,
                   hit_area=area, skill_name=self.name,
                   on_hit_effects=[{
                       "fn": self._apply_life_drain_energy,
                       "data": {"target": enemy, "caster": caster, "amount": 20},
                   }])
        state.push(5.13, caster, state._handle_cooldown, skill=self)
        log(f"{caster.name} 使用森罗汲取。")
        return True

    def _apply_life_drain_energy(self, data, state, log, actor=None):
        enemy = data.get("target")
        caster = data.get("caster") or actor
        if enemy is None or caster is None:
            return
        amount = max(0, data.get("amount", 0))
        drain = min(amount, getattr(enemy, "energy", 0), caster.max_energy - caster.energy)
        enemy.energy = max(0, enemy.energy - drain)
        caster.energy = min(caster.max_energy, caster.energy + drain)
        if log:
            log(f"{caster.name} 的森罗汲取吸取 {drain} 点能量。")

    def _normalize_2x2_area(self, state, target):
        # 兼容同学版本的“四格列表”与当前 UI 的“左上角单格”两种输入。
        if isinstance(target, tuple) and len(target) == 2 and all(isinstance(x, int) for x in target):
            row, col = target
            if row < 0 or col < 0 or not state.in_bounds(row + 1, col + 1):
                return None
            return {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}

        if self._is_valid_2x2_area(state, target):
            return {tuple(cell) for cell in target}

        return None

    def _is_valid_2x2_area(self, state, target):
        if not isinstance(target, (list, tuple)) or len(target) != 4:
            return False

        cells = []
        for cell in target:
            if not isinstance(cell, (list, tuple)) or len(cell) != 2:
                return False
            row, col = cell
            if not state.in_bounds(row, col):
                return False
            cells.append((row, col))

        if len(set(cells)) != 4:
            return False

        rows = sorted({row for row, _ in cells})
        cols = sorted({col for _, col in cells})
        if len(rows) != 2 or len(cols) != 2:
            return False
        if rows[1] - rows[0] != 1 or cols[1] - cols[0] != 1:
            return False

        return set(cells) == {
            (rows[0], cols[0]),
            (rows[0], cols[1]),
            (rows[1], cols[0]),
            (rows[1], cols[1]),
        }


class VineSeal(Skill):
    def __init__(self):
        super().__init__(skill_id="vine_seal", name="万藤封禁", description="消耗 50 点能量。选择目标格；敌人在目标格时阻止其本轮技能生效。", cooldown=5, target_required=True, energy_cost=50)
    def cast(self,state,caster,target,log):
        if target is None or not state.in_bounds(*target): log("万藤封禁需要选择场内目标格。"); return False
        if not _has_enough_energy(caster,self,log): return False
        enemy=state.get_enemy_of(caster); _spend_energy(caster,self)
        if enemy.pos==target: state.push(1.5,caster,state._handle_silence,target=enemy); log(f"{caster.name} 使用万藤封禁，{enemy.name} 本轮技能被阻止。")
        else: state.push(0,caster,state._log,message=f"{caster.name} 的万藤封禁没有命中。")
        state.push(1.5,caster,state._handle_cooldown,skill=self); return True


def _has_enough_energy(caster, skill, log):
    if caster.energy < skill.energy_cost:
        log(f"{skill.name} 需要 {skill.energy_cost} 点能量。")
        return False
    return True


def _spend_energy(caster, skill):
    caster.energy = max(0, caster.energy - skill.energy_cost)
