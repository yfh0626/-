from skills.skill import Skill
from core.movement import same_line
import random


class NormalAttack(Skill):
    def __init__(self):
        super().__init__("normal_attack", "普通攻击", "攻击上下左右相邻格的目标格；敌人在目标格时造成角色基础攻击伤害。", cooldown=0, target_required=True, range=1, energy_cost=10)

    def cast(self, state, caster, target, log):
        if target is None:
            log("普通攻击需要选择目标格。")
            return
        if not state.in_bounds(*target):
            log("普通攻击目标不能超出棋盘边界。")
            return
        max_range = 1 + _range_bonus(caster)
        dist = state.distance(caster.pos, target)
        if dist < 1 or dist > max_range:
            log(f"普通攻击只能选择 {max_range} 格内的格子。")
            return
        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        enemy = state.get_enemy_of(caster)
        state.push(5.0, caster, state._apply_damage,
                   target=enemy, amount=getattr(caster, "attack", 10),
                   max_dist=max_range, hit_cell=target, skill_name=self.name)
        return True


class Guard(Skill):
    def __init__(self):
        super().__init__("guard", "格挡",
                         "选择上下左右一格，格挡该方向上的非范围攻击。",
                         cooldown=2, target_required=True, range=1,
                         energy_cost=25)

    def cast(self, state, caster, target, log):
        if target is None:
            log("格挡需要选择方向格。")
            return

        row, col = target
        if not state.in_bounds(row, col):
            log("格挡方向不能超出棋盘边界。")
            return

        if state.distance(caster.pos, target) != 1:
            log("格挡只能选择上下左右相邻 1 格。")
            return

        cr, cc = caster.pos
        direction = (row - cr, col - cc)
        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        state.push(4.6, caster, state._apply_status,
                   target=caster, key="guard_direction", value=direction)
        state.push(4.6, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log,
                   message=f"{caster.name} 准备格挡 {direction} 方向的攻击。")


class Dash(Skill):
    def __init__(self):
        super().__init__("dash", "冲刺",
                         "水平方向冲刺 3 格，撞到敌人时触发位移。",
                         cooldown=2, target_required=True, range=3,
                         energy_cost=10)

    def cast(self, state, caster, target, log):
        if target is None:
            log("冲刺需要选择目标格。")
            return

        caster_row, caster_col = caster.pos
        target_row, target_col = target
        if target_row != caster_row or target_col == caster_col:
            log("冲刺只能选择水平方向。")
            return

        direction = 1 if target_col > caster_col else -1
        dest_col = caster_col + direction * (3 + _move_bonus(caster))
        dest = state.clamp_pos(caster_row, dest_col)
        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        state.push(3.0, caster, state._apply_move, pos=dest)
        state.push(3.0, caster, state._handle_cooldown, skill=self)


class Blink(Skill):
    def __init__(self):
        super().__init__("blink", "闪现",
                         "选择中间行非边缘格，在其周围随机闪现到无人格。",
                         cooldown=3, target_required=True,
                         energy_cost=20)

    def cast(self, state, caster, target, log):
        if target is None:
            log("闪现需要选择目标格。")
            return

        row, col = target
        middle_row = state.rows // 2
        if row != middle_row:
            log("闪现只能选择中间一行。")
            return

        if col <= 0 or col >= state.cols - 1:
            log("闪现不能选择中间行两边的格子。")
            return

        candidates = []
        for r in range(row - 1, row + 2):
            for c in range(col - 1, col + 2):
                if state.in_bounds(r, c) and not state.is_occupied(r, c):
                    candidates.append((r, c))

        if not candidates:
            log("闪现范围内没有可用空格。")
            return

        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        state.push(3.0, caster, state._apply_move,
                   pos=random.choice(candidates))
        state.push(3.0, caster, state._handle_cooldown, skill=self)


class Focus(Skill):
    def __init__(self):
        super().__init__("focus", "蓄势",
                         "恢复 30 点能量。",
                         cooldown=0, target_required=False,
                         energy_cost=0)

    def cast(self, state, caster, target, log):
        old_energy = caster.energy
        caster.energy = min(caster.max_energy, caster.energy + 30)
        restored = caster.energy - old_energy
        state.push(4.7, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log,
                   message=f"{caster.name} 使用蓄势，恢复 {restored} 点能量。")


def _has_enough_energy(caster, skill, log):
    if caster.energy < skill.energy_cost:
        log(f"{skill.name} 需要 {skill.energy_cost} 点能量。")
        return False
    return True


def _spend_energy(caster, skill):
    caster.energy = max(0, caster.energy - skill.energy_cost)


def _range_bonus(caster):
    return 1 if getattr(caster, "status", {}).get("range_boost") else 0


def _move_bonus(caster):
    return 1 if getattr(caster, "status", {}).get("move_boost") else 0


class MinorHeal(Skill):
    def __init__(self):
        super().__init__("minor_heal", "小治疗", "回复 15 点生命值。", cooldown=7, target_required=False, energy_cost=40)
    def cast(self,state,caster,target,log):
        if not _has_enough_energy(caster,self,log): return
        _spend_energy(caster,self); old_hp=caster.hp; caster.hp=min(caster.max_hp,caster.hp+15)
        state.push(0,caster,state._log,message=f"{caster.name} 回复了 {caster.hp-old_hp} 点生命值。")
        state.push(4.6,caster,state._handle_cooldown,skill=self)


class HeavySlash(Skill):
    def __init__(self):
        super().__init__("heavy_slash", "重斩", "攻击目标格；敌人在目标格时造成 30 点伤害。", cooldown=2, target_required=True, range=1, energy_cost=25)

    def cast(self, state, caster, target, log):
        if target is None:
            log("重斩需要选择目标格。")
            return
        if not state.in_bounds(*target):
            log("重斩目标不能超出棋盘边界。")
            return
        max_range = 1 + _range_bonus(caster)
        dist = state.distance(caster.pos, target)
        if dist < 1 or dist > max_range:
            log(f"重斩只能选择 {max_range} 格内的格子。")
            return
        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        enemy = state.get_enemy_of(caster)
        state.push(5.0, caster, state._apply_damage,
                   target=enemy, amount=30, max_dist=max_range,
                   hit_cell=target, skill_name=self.name)
        state.push(5.0, caster, state._handle_cooldown, skill=self)
        return True


class PiercingShot(Skill):
    def __init__(self):
        super().__init__("piercing_shot", "贯穿射击",
                         "选择同行或同列的方向格；敌人在该方向直线上时造成 15 点伤害。",
                         cooldown=3, target_required=True, energy_cost=20)

    def cast(self, state, caster, target, log):
        if target is None:
            log("贯穿射击需要选择目标方向格。")
            return
        if not state.in_bounds(*target):
            log("贯穿射击目标不能超出棋盘边界。")
            return
        if not same_line(caster.pos, target) or target == caster.pos:
            log("贯穿射击只能选择同行或同列的方向格。")
            return
        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        enemy = state.get_enemy_of(caster)
        direction = self._direction(caster.pos, target)
        state.push(5.0, caster, state._apply_damage,
                   target=enemy, amount=15,
                   hit_ray={"origin": caster.pos, "direction": direction},
                   skill_name=self.name)
        state.push(5.0, caster, state._handle_cooldown, skill=self)
        return True

    @staticmethod
    def _direction(caster_pos, target):
        cr, cc = caster_pos
        tr, tc = target
        if tr == cr:
            return (0, 1 if tc > cc else -1)
        return (1 if tr > cr else -1, 0)


class AreaBlast(Skill):
    def __init__(self):
        super().__init__("area_blast", "范围爆破",
                         "选择距离自己不超过 2 格的中心格，对 3x3 区域内敌人造成 14 点伤害。",
                         cooldown=3, target_required=True, range=2, energy_cost=40)

    def cast(self, state, caster, target, log):
        if target is None:
            log("范围爆破需要选择 3x3 区域中心格。")
            return
        if not state.in_bounds(*target):
            log("范围爆破中心不能超出棋盘边界。")
            return
        if state.distance(caster.pos, target) > 2:
            log("范围爆破中心距离不能超过 2 格。")
            return
        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        enemy = state.get_enemy_of(caster)
        hit_area = {
            (r, c)
            for r in range(target[0] - 1, target[0] + 2)
            for c in range(target[1] - 1, target[1] + 2)
            if state.in_bounds(r, c)
        }
        state.push(5.0, caster, state._apply_damage,
                   target=enemy, amount=14, is_area=True,
                   hit_area=hit_area, skill_name=self.name)
        state.push(5.0, caster, state._handle_cooldown, skill=self)
        return True


class Roll(Skill):
    def __init__(self):
        super().__init__("roll", "翻滚",
                         "同线移动最多 2 格并获得闪避。",
                         cooldown=3, target_required=True, range=2,
                         energy_cost=20)

    def cast(self, state, caster, target, log):
        if target is None:
            log("翻滚需要选择目标格。")
            return
        row, col = state.clamp_pos(target[0], target[1])
        target = (row, col)
        max_range = 2 + _move_bonus(caster)
        if state.distance(caster.pos, target) > max_range:
            log(f"翻滚距离不能超过 {max_range} 格。")
            return
        if not same_line(caster.pos, target):
            log("翻滚只能选择同一行或同一列。")
            return
        enemy = state.get_enemy_of(caster)
        if target == enemy.pos:
            log("目标格被占用。")
            return
        if not _has_enough_energy(caster, self, log):
            return
        _spend_energy(caster, self)
        state.push(3.0, caster, state._apply_move, pos=target)
        state.push(4.9, caster, state._apply_status, target=caster, key="roll_evade_pending", value=True)
        state.push(4.9, caster, state._handle_cooldown, skill=self)


class HookStep(Skill):
    def __init__(self):
        super().__init__("hook_step", "钩步",
                         "将同线 3 格内的敌人拉近，或自己移动到空格。",
                         cooldown=3, target_required=True, range=3,
                         energy_cost=20)

    def cast(self, state, caster, target, log):
        if target is None:
            log("钩步需要选择目标格。")
            return
        row, col = state.clamp_pos(target[0], target[1])
        target = (row, col)
        max_range = 3 + _move_bonus(caster)
        if state.distance(caster.pos, target) > max_range:
            log(f"钩步距离不能超过 {max_range} 格。")
            return
        if not same_line(caster.pos, target):
            log("钩步只能选择同一行或同一列。")
            return

        enemy = state.get_enemy_of(caster)
        if target == enemy.pos:
            cr, cc = caster.pos
            er, ec = enemy.pos
            if cr == er:
                new_ec = ec + (1 if cc > ec else -1)
            else:
                new_er = er + (1 if cr > er else -1)
            new_pos = state.clamp_pos(cr if cr == er else new_er,
                                       new_ec if cr == er else ec)
            if new_pos != caster.pos and not state.is_occupied(*new_pos):
                state.push(3.0, caster, state._apply_move, target=enemy, pos=new_pos)
            else:
                log("无法拉近。")
                return False
        else:
            if state.is_occupied(*target):
                log("目标格被占用。")
                return
            state.push(3.0, caster, state._apply_move, pos=target)
        state.push(3.0, caster, state._handle_cooldown, skill=self)


class ShieldWall(Skill):
    def __init__(self):
        super().__init__("shield_wall", "盾墙",
                         "本回合受到的伤害减少 70%。",
                         cooldown=5, target_required=False,
                         energy_cost=30)

    def cast(self, state, caster, target, log):
        state.push(4.8, caster, state._apply_status, target=caster,
                   key="shield_wall", value=True)
        state.push(4.8, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 展开盾墙。")


class CounterStance(Skill):
    def __init__(self):
        super().__init__("counter_stance", "反击姿态",
                         "本回合受到攻击时反击 10 点伤害。",
                         cooldown=4, target_required=False,
                         energy_cost=20)

    def cast(self, state, caster, target, log):
        state.push(4.8, caster, state._apply_status, target=caster,
                   key="counter_stance", value=True)
        state.push(4.8, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 进入反击姿态。")


class EnergyCharge(Skill):
    def __init__(self):
        super().__init__("energy_charge", "能量充盈",
                         "我方所有技能冷却减少 2。",
                         cooldown=4, target_required=False,
                         energy_cost=30)

    def cast(self, state, caster, target, log):
        for skill in state.all_skills.get(caster, []):
            for _ in range(2):
                skill.reduce_cooldown()
        state.push(2, caster, state._handle_cooldown, skill=self)
        state.push(0, caster, state._log, message=f"{caster.name} 使用能量充盈，所有技能冷却减少 2。")


class Silence(Skill):
    def __init__(self):
        super().__init__("silence", "沉默",
                         "选择 3 格内目标格；敌人在目标格时阻止敌人本轮行动。",
                         cooldown=4, target_required=True, range=3, energy_cost=15)

    def cast(self, state, caster, target, log):
        if target is None or not state.in_bounds(*target):
            log("沉默需要选择场内目标格。")
            return False
        if state.distance(caster.pos, target) > 3:
            log("沉默距离不能超过 3 格。")
            return False
        enemy = state.get_enemy_of(caster)
        if enemy.pos == target:
            state.push(1, caster, state._handle_silence, target=enemy)
            state.push(1, caster, state._apply_status, target=enemy, key="silenced", value=2)
            state.push(0, caster, state._log, message=f"{caster.name} 沉默 {enemy.name}。")
        else:
            state.push(0, caster, state._log, message=f"{caster.name} 的沉默没有命中。")
        state.push(1, caster, state._handle_cooldown, skill=self)
        return True

    def on_turn_start(self, state, caster, log):
        enemy = state.get_enemy_of(caster)
        dur = enemy.special_state.get("silenced", 0)
        if dur > 0:
            state.push(1, caster, state._apply_status, target=enemy, key="silenced", value=dur - 1)


