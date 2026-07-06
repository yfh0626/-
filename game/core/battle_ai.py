"""Battle AI controllers.

The AI is intentionally chosen and encrypted at the beginning of a round.
Therefore all decision functions must use only the current state at commit time,
which is the board state after the previous round has fully ended.
"""

from __future__ import annotations

import random
import time
from typing import Callable, Iterable, Optional


AI_CONFIGS = {
    "easy": {
        "name": "简单 AI",
        "short_name": "简单",
        "character_id": "vine_mage",
        "basic_skill_ids": [
            "normal_attack",
            "dash",
            "focus",
            "guard",
            "heavy_slash",
            "minor_heal",
        ],
        "desc": "藤蔓法师：随机性较强，攻击判断较弱。",
    },
    "normal": {
        "name": "普通 AI",
        "short_name": "普通",
        "character_id": "fire_mage",
        "basic_skill_ids": [
            "normal_attack",
            "dash",
            "minor_heal",
            "area_blast",
            "roll",
            "counter_stance",
        ],
        "desc": "火焰法师：按距离判断攻击、治疗和位移。",
    },
    "hard": {
        "name": "困难 AI",
        "short_name": "困难",
        "character_id": "bone_general",
        "basic_skill_ids": [
            "normal_attack",
            "dash",
            "focus",
            "minor_heal",
            "roll",
            "piercing_shot",
        ],
        "desc": "殉爆骨将：本地深度 2 搜索，枚举玩家可能走位并加入下一轮跟进收益。",
    },
}


INVALID_TARGET = object()
HARD_AI_SEARCH_DEPTH = 2


def get_ai_config(difficulty: str) -> dict:
    return AI_CONFIGS.get(difficulty, AI_CONFIGS["normal"])


class BattleAIController:
    def __init__(self, difficulty: str = "normal"):
        self.difficulty = difficulty if difficulty in AI_CONFIGS else "normal"

    def choose(self, state, ai, opponent, skills):
        """Return a legal committed choice: (actor, skill, target)."""
        if ai is None or ai.hp <= 0:
            return (None, None, None)
        if self._is_forced_random(ai):
            return (ai, None, "__chaos_random__")

        if self.difficulty == "easy":
            return self._choose_easy(state, ai, opponent, skills)
        if self.difficulty == "hard":
            return self._choose_hard(state, ai, opponent, skills)
        return self._choose_normal(state, ai, opponent, skills)

    # ── common helpers ──────────────────────────────────────────────────

    @staticmethod
    def _is_forced_random(actor) -> bool:
        return int(getattr(actor, "special_state", {}).get("chaos_random_turns", 0) or 0) > 0

    @staticmethod
    def _skill(skills, skill_id: str):
        for skill in skills:
            if getattr(skill, "skill_id", None) == skill_id:
                return skill
        return None

    @staticmethod
    def _usable(skill, actor) -> bool:
        return skill is not None and skill.can_use(actor)

    def _choice(self, ai, skill, target):
        if skill is None or target is INVALID_TARGET:
            return None
        return (ai, skill, target)

    @staticmethod
    def _weighted_pick(items):
        """Pick one (item, weight) pair and return item."""
        valid = [(item, max(0, weight)) for item, weight in items if weight > 0]
        if not valid:
            return None
        total = sum(weight for _, weight in valid)
        if total <= 0:
            return None
        mark = random.uniform(0, total)
        acc = 0
        for item, weight in valid:
            acc += weight
            if mark <= acc:
                return item
        return valid[-1][0]

    def _redistributed_pick(self, entries):
        """Redistribute unavailable entries' probabilities equally to available ones."""
        available = [(item, weight) for item, weight, is_available in entries if is_available]
        if not available:
            return None
        invalid_total = sum(weight for _, weight, is_available in entries if not is_available)
        bonus = invalid_total / len(available)
        return self._weighted_pick([(item, weight + bonus) for item, weight in available])

    @staticmethod
    def _adjacent_cells(state, pos):
        row, col = pos
        candidates = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cell = (row + dr, col + dc)
            if state.in_bounds(*cell):
                candidates.append(cell)
        return candidates

    def _random_adjacent(self, state, pos):
        cells = self._adjacent_cells(state, pos)
        if not cells:
            return INVALID_TARGET
        return random.choice(cells)

    @staticmethod
    def _step_towards(state, start, goal):
        sr, sc = start
        gr, gc = goal
        options = []
        if gc < sc:
            options.append((sr, sc - 1))
        elif gc > sc:
            options.append((sr, sc + 1))
        if gr < sr:
            options.append((sr - 1, sc))
        elif gr > sr:
            options.append((sr + 1, sc))
        options = [cell for cell in options if state.in_bounds(*cell)]
        if not options:
            return INVALID_TARGET
        options.sort(key=lambda cell: state.distance(cell, goal))
        return options[0]

    @staticmethod
    def _random_life_drain_target(state):
        # LifeDrain interprets target as the top-left cell of a valid 2×2 area.
        if state.rows < 2 or state.cols < 2:
            return INVALID_TARGET
        return (random.randrange(0, state.rows - 1), random.randrange(0, state.cols - 1))

    @staticmethod
    def _near_opponent_cells(state, opponent_pos):
        row, col = opponent_pos
        weighted = [((row, col), 80)]
        for cell in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]:
            weighted.append((cell, 5))
        return [(cell, weight) for cell, weight in weighted if state.in_bounds(*cell)]

    @staticmethod
    def _line_direction(origin, target):
        orow, ocol = origin
        trow, tcol = target
        if trow == orow and tcol != ocol:
            return (0, 1 if tcol > ocol else -1)
        if tcol == ocol and trow != orow:
            return (1 if trow > orow else -1, 0)
        return None

    @staticmethod
    def _area_3x3(state, center):
        row, col = center
        return {
            (r, c)
            for r in range(row - 1, row + 2)
            for c in range(col - 1, col + 2)
            if state.in_bounds(r, c)
        }

    # ── easy AI ─────────────────────────────────────────────────────────

    def _choose_easy(self, state, ai, opponent, skills):
        # If every non-focus skill is unavailable because of CD/energy, use Focus.
        focus = self._skill(skills, "focus")
        non_focus_usable = any(
            self._usable(skill, ai) and getattr(skill, "skill_id", None) != "focus"
            for skill in skills
        )
        if not non_focus_usable and self._usable(focus, ai):
            return (ai, focus, None)

        attack_choice = self._easy_attack_choice(state, ai, opponent, skills)
        support_choice = self._easy_support_choice(state, ai, opponent, skills)

        if attack_choice is None and support_choice is None:
            if self._usable(focus, ai):
                return (ai, focus, None)
            return (None, None, None)
        if attack_choice is None:
            return support_choice
        if support_choice is None:
            return attack_choice

        return attack_choice if random.random() < 0.65 else support_choice

    def _easy_attack_choice(self, state, ai, opponent, skills):
        normal = self._choice_if_usable(skills, ai, "normal_attack", lambda: self._random_adjacent(state, ai.pos))
        heavy = self._choice_if_usable(skills, ai, "heavy_slash", lambda: self._step_towards(state, ai.pos, opponent.pos))
        drain = self._choice_if_usable(skills, ai, "life_drain", lambda: self._random_life_drain_target(state))
        seal = self._choice_if_usable(skills, ai, "vine_seal", lambda: opponent.pos)

        return self._redistributed_pick([
            (normal, 50, normal is not None),
            (heavy, 25, heavy is not None),
            (drain, 15, drain is not None),
            (seal, 10, seal is not None),
        ])

    def _easy_support_choice(self, state, ai, opponent, skills):
        guard = self._choice_if_usable(skills, ai, "guard", lambda: self._random_adjacent(state, ai.pos))
        dash = self._choice_if_usable(skills, ai, "dash", lambda: self._dash_target(state, ai, opponent, closer=True))
        focus = self._choice_if_usable(skills, ai, "focus", lambda: None)
        heal = self._choice_if_usable(skills, ai, "minor_heal", lambda: None)

        return self._redistributed_pick([
            (guard, 25, guard is not None),
            (dash, 25, dash is not None),
            (focus, 25, focus is not None),
            (heal, 25, heal is not None),
        ])

    def _choice_if_usable(self, skills, ai, skill_id: str, target_fn: Callable):
        skill = self._skill(skills, skill_id)
        if not self._usable(skill, ai):
            return None
        target = target_fn()
        return self._choice(ai, skill, target)


    # ── hard AI: Bone General depth-2 expected-value search ─────────────

    def _choose_hard(self, state, ai, opponent, skills):
        """Expected-value local search for Bone General.

        Search depth is intentionally shallow but now includes a second ply:
        enumerate the AI's legal current action, enumerate a compact set of
        opponent current-round movement scenarios, then add a discounted
        next-round follow-up value before choosing the best average score. This
        method is called when the AI commitment is created, before the player
        chooses the current-round action, so it only observes the board state at
        the end of the previous round.
        """
        deadline = time.perf_counter() + 1.15
        search_depth = HARD_AI_SEARCH_DEPTH
        candidates = self._hard_candidate_actions(state, ai, opponent, skills, deadline, search_depth)

        if not candidates:
            focus = self._skill(skills, "focus")
            if self._usable(focus, ai):
                return (ai, focus, None)
            return (None, None, None)

        best_score = max(score for score, _choice, _reason in candidates)
        # Mostly choose the exact best action.  Tiny random tie-breaking keeps
        # the same-valued choices from becoming visually repetitive.
        best = [(choice, reason) for score, choice, reason in candidates if score >= best_score - 0.10]
        choice, reason = random.choice(best)
        ai.special_state["_hard_ai_last_reason"] = reason
        ai.special_state["_hard_ai_last_score"] = round(best_score, 2)
        ai.special_state["_hard_ai_candidates"] = len(candidates)
        ai.special_state["_hard_ai_depth"] = search_depth
        return choice

    def _hard_candidate_actions(self, state, ai, opponent, skills, deadline, search_depth=1):
        opponent_scenarios = self._hard_opponent_scenarios(state, ai, opponent, deadline)
        candidates = []

        def add(skill_id, target, reason):
            if time.perf_counter() > deadline:
                return
            skill = self._skill(skills, skill_id)
            if not self._usable(skill, ai):
                return
            if target is INVALID_TARGET:
                return
            score = self._hard_expected_score(state, ai, opponent, skill, target, opponent_scenarios, search_depth, deadline)
            candidates.append((score, (ai, skill, target), reason))

        # Exclusive Bone General skills.  Bone Explosion is only considered
        # when the player is already inside the current 3×7 threat area.
        # If the player starts outside the area, choosing it is never useful
        # under the real rule because the opponent can only make it worse by
        # moving away, so the hard AI must not randomly self-destruct.
        if self._hard_bone_explosion_hits(ai.pos, opponent.pos):
            add("bone_explosion", None, "搜索同殒骨爆：玩家当前在骨爆范围内，按可能走位计算平均换血收益")

        # 残骨重组（二技能）按单独标准判断：血量大于 35 时绝不使用；
        # 血量不高于 35 时才根据距离、低血量程度、以及一技能可用性打分。
        if self._hard_should_consider_bone_rebuild(state, ai, opponent, skills):
            skill = self._skill(skills, "bone_rebuild")
            score = self._hard_bone_rebuild_score(state, ai, opponent, skills)
            candidates.append((score, (ai, skill, None), "单独评分残骨重组：低血量、近距离、一技能可衔接"))

        # User-specified common skills for hard AI.
        add("focus", None, "搜索蓄势：评估能量缺口")
        add("minor_heal", None, "搜索小治疗：评估回复收益")

        normal = self._skill(skills, "normal_attack")
        if self._usable(normal, ai):
            max_range = 1 + self._hard_range_bonus(ai)
            for cell in self._cells_within(state, ai.pos, max_range, include_self=False):
                add("normal_attack", cell, "搜索普通攻击目标格")

        piercing = self._skill(skills, "piercing_shot")
        if self._usable(piercing, ai):
            for cell in self._hard_direction_targets(state, ai.pos):
                add("piercing_shot", cell, "搜索贯穿射击方向")

        dash = self._skill(skills, "dash")
        if self._usable(dash, ai):
            row, col = ai.pos
            for dc in (-1, 1):
                direction_cell = (row, col + dc)
                if state.in_bounds(*direction_cell):
                    add("dash", direction_cell, "搜索冲刺方向以调整骨爆距离")

        roll = self._skill(skills, "roll")
        if self._usable(roll, ai):
            for cell in self._hard_roll_targets(state, ai):
                add("roll", cell, "搜索翻滚落点以调整骨爆距离/规避伤害")

        # If every real skill is blocked by energy/CD, fall back to Focus if usable.
        return candidates

    def _hard_should_consider_bone_rebuild(self, state, ai, opponent, skills):
        """Gate Bone General's second skill with the user-specified rule.

        残骨重组是保命/换血前置技能，不能再被通用搜索在高血量时误选。
        """
        skill = self._skill(skills, "bone_rebuild")
        if not self._usable(skill, ai):
            return False
        if bool(ai.special_state.get("death_immune") or ai.special_state.get("_bone_revive")):
            return False
        # 关键硬限制：35 血以上一定不用二技能。
        if max(0, getattr(ai, "hp", 0)) > 35:
            return False
        return True

    def _hard_bone_rebuild_score(self, state, ai, opponent, skills):
        """Separate scoring for Bone General's second skill.

        标准来自之前的设计：离敌方越近越适合开，血量越低越适合开，
        一技能可用时加分，方便下一轮直接同殒骨爆换血。
        """
        hp = max(0.0, float(getattr(ai, "hp", 0)))
        max_hp = max(1.0, float(getattr(ai, "max_hp", 1)))
        dist = state.distance(ai.pos, opponent.pos)
        bone_explosion = self._skill(skills, "bone_explosion")

        # 35 血以上由 gate 拦截；这里再给一个极低分防御误调用。
        if hp > 35:
            return -999.0

        # 血量越低分越高：1 血附近最高，35 血附近仍可用但不盲目开。
        low_hp_score = max(0.0, 35.0 - hp) * 2.4
        danger_score = max(0.0, 0.35 - hp / max_hp) * 120.0

        # 距离越近越好；已经在骨爆 3×7 范围内时额外加分。
        close_score = max(0.0, 7.0 - float(dist)) * 6.0
        if self._hard_bone_explosion_hits(ai.pos, opponent.pos):
            close_score += 26.0

        # 一技能可用时鼓励先开二技能，为后续同殒骨爆换血创造条件。
        combo_score = 0.0
        if self._usable(bone_explosion, ai):
            combo_score += 34.0
        elif bone_explosion is not None and getattr(bone_explosion, "current_cd", 0) <= 1:
            combo_score += 16.0

        # 对方血量太低时，通常没必要开保命前置，直接找击杀更好。
        opp_hp = max(0.0, float(getattr(opponent, "hp", 0)))
        finish_penalty = 22.0 if opp_hp <= 30 else 0.0

        return 60.0 + low_hp_score + danger_score + close_score + combo_score - finish_penalty

    def _hard_expected_score(self, state, ai, opponent, skill, target, opponent_scenarios, search_depth=1, deadline=None):
        skill_id = getattr(skill, "skill_id", "")
        ai_pos_after = self._hard_ai_final_pos(state, ai, skill_id, target)
        total = 0.0
        weight_sum = 0.0
        for scenario in opponent_scenarios:
            w = max(0.01, float(scenario.get("weight", 1.0)))
            total += w * self._hard_score_against_scenario(
                state, ai, opponent, skill, target, ai_pos_after, scenario, search_depth, deadline
            )
            weight_sum += w
        return total / max(weight_sum, 0.01)

    def _hard_score_against_scenario(self, state, ai, opponent, skill, target, ai_pos_after, scenario, search_depth=1, deadline=None):
        skill_id = getattr(skill, "skill_id", "")
        opp_pos_after = scenario["pos"]
        opp_expected_heal = scenario.get("heal", 0.0)
        incoming = self._hard_estimate_opponent_threat_at(state, ai_pos_after, opp_pos_after, opponent)

        ai_hp = max(0.0, float(getattr(ai, "hp", 0)))
        opp_hp = max(0.0, float(getattr(opponent, "hp", 0)))
        ai_max_hp = max(1.0, float(getattr(ai, "max_hp", 1)))
        opp_max_hp = max(1.0, float(getattr(opponent, "max_hp", 1)))
        ai_hp_pct = ai_hp / ai_max_hp
        opp_hp_pct = opp_hp / opp_max_hp
        revive_active = bool(ai.special_state.get("death_immune") or ai.special_state.get("_bone_revive"))
        opponent_dodge = bool(opponent.special_state.get("dodge") or opponent.status.get("dodge"))
        opponent_invincible = bool(opponent.special_state.get("invincible") or opponent.status.get("invincible"))
        skill_cost = max(0, getattr(skill, "energy_cost", 0))

        damage_to_opp = 0.0
        damage_to_ai = 0.0
        direct_death = False
        miss_by_range = False
        future_value = 0.0
        positional = self._hard_position_score(state, ai_pos_after, opp_pos_after, ai, opponent)

        if skill_id == "bone_explosion":
            hit_range = self._hard_bone_explosion_hits(ai_pos_after, opp_pos_after)
            if hit_range:
                # Real rule after this revision: Bone Explosion is considered
                # successful as long as the enemy is still inside 3×7 at
                # resolution time.  Dodge/invincible may prevent the enemy's HP
                # loss, but that no longer turns the explosion into a miss.
                if not opponent_dodge and not opponent_invincible:
                    damage_to_opp = 30
                damage_to_ai = 30
                if revive_active:
                    future_value += 72  # encourage rebuild → aggressive explosion trades
                else:
                    future_value += 14
            else:
                miss_by_range = True
                direct_death = True
                damage_to_ai = ai_hp
                # More aggressive than the previous version: when the player
                # starts inside the blast area, a possible dodge-out scenario is
                # penalized, but not so harshly that the AI never trades.  If
                # rebuild is active, the miss is much less scary because it can
                # be revived next turn.
                future_value -= 18 if revive_active else 95

        elif skill_id == "bone_rebuild":
            if revive_active:
                return -90.0
            future_value += 60
            if ai_hp_pct <= 0.35:
                future_value += 76
            elif ai_hp_pct <= 0.60:
                future_value += 38
            # Prepare rebuild before entering or while already in explosion range.
            if self._hard_bone_explosion_hits(ai_pos_after, opp_pos_after):
                future_value += 42
            if opp_hp_pct <= 0.30:
                future_value -= 30

        elif skill_id == "normal_attack":
            if tuple(opp_pos_after) == tuple(target):
                damage_to_opp = getattr(ai, "attack", 10)
            else:
                future_value -= 5
                future_value += max(0, 3 - state.distance(target, opp_pos_after))

        elif skill_id == "piercing_shot":
            direction = self._line_direction(ai.pos, target)
            if direction and self._hard_on_ray(ai.pos, direction, opp_pos_after):
                damage_to_opp = 15
            else:
                future_value -= 4

        elif skill_id == "minor_heal":
            heal = min(15, max(0.0, ai_max_hp - ai_hp))
            if heal <= 0:
                future_value -= 36
            else:
                damage_to_ai -= heal
                if ai_hp_pct <= 0.35:
                    future_value += 34
                elif ai_hp_pct <= 0.60:
                    future_value += 14

        elif skill_id == "focus":
            restored = min(30, max(0, ai.max_energy - ai.energy))
            if restored <= 0:
                future_value -= 35
            else:
                future_value += restored * 0.75
                energy_pct = ai.energy / max(1, ai.max_energy)
                if energy_pct < 0.30:
                    future_value += 55
                elif energy_pct < 0.50:
                    future_value += 24

        elif skill_id in {"dash", "roll"}:
            future_value += positional
            # Strongly prefer moving into explosion threat range, especially if
            # rebuild is active or rebuild will soon be available.
            if self._hard_bone_explosion_hits(ai_pos_after, opp_pos_after):
                future_value += 42 if revive_active else 22
            else:
                future_value -= 8
            if ai_hp_pct <= 0.30 and state.distance(ai_pos_after, opp_pos_after) > state.distance(ai.pos, opp_pos_after):
                future_value += 12

        # Expected opponent healing makes damage slightly less valuable.
        effective_opp_hp = min(opp_max_hp, opp_hp + opp_expected_heal)
        opp_after = max(0.0, effective_opp_hp - damage_to_opp)
        ai_after = ai_hp - damage_to_ai - incoming * self._hard_incoming_damage_multiplier(skill_id)

        if revive_active and ai_after <= 0:
            # Death prevention leaves 1 HP, then BoneRebuild restores at next
            # turn start.  Model the next-turn practical value as 36 HP.
            ai_after = min(ai_max_hp, 36.0)
            future_value += 48 if miss_by_range else 28
        elif direct_death and not revive_active:
            ai_after = 0.0

        opp_after_pct = opp_after / opp_max_hp
        ai_after_pct = max(0.0, ai_after) / ai_max_hp

        score = 0.0
        # Use HP percentages rather than raw HP, so Bone General correctly
        # values its large health pool when trading 30-for-30.
        score += (opp_hp_pct - opp_after_pct) * 520.0
        score += (ai_after_pct - ai_hp_pct) * 420.0
        score -= skill_cost * 0.10
        score -= getattr(skill, "cooldown", 0) * 0.12
        score += future_value
        # 稍微提高距离/站位因素权重，让优势时更愿意压近，劣势较大时更愿意拉开。
        score += positional * 0.65

        if opp_after <= 0:
            score += 260
        if ai_after <= 0:
            # A range-miss from Bone Explosion is still bad, but now slightly
            # less paralyzing than before; outside-current-range actions are
            # already filtered out in candidate generation.
            if skill_id == "bone_explosion" and miss_by_range:
                score -= 130 if not revive_active else 10
            else:
                score -= 260

        if skill_id == "bone_explosion":
            if revive_active and self._hard_bone_explosion_hits(ai_pos_after, opp_pos_after):
                score += 58
            if miss_by_range:
                score -= 65 if not revive_active else 8
            elif damage_to_opp <= 0:
                # Enemy was in range but dodged/was invincible: not a miss, but
                # the trade failed to hurt the player.
                score -= 28

        if search_depth > 1 and (deadline is None or time.perf_counter() < deadline):
            score += 0.35 * self._hard_followup_score(
                state, ai, opponent, ai_pos_after, opp_pos_after,
                max(0.0, ai_after), opp_after, revive_active
            )

        return score

    def _hard_followup_score(self, state, ai, opponent, ai_pos, opp_pos, ai_hp, opp_hp, revive_active):
        """Heuristic second-ply value for Bone General's next round.

        This keeps the hard AI fast enough for the UI while making it prefer
        moves that set up rebuild → bone explosion, good piercing lines, and
        safer spacing one round later.
        """
        if opp_hp <= 0:
            return 220.0
        if ai_hp <= 0 and not revive_active:
            return -220.0

        skills = list(state.all_skills.get(ai, []))
        ai_max_hp = max(1.0, float(getattr(ai, "max_hp", 1)))
        opp_max_hp = max(1.0, float(getattr(opponent, "max_hp", 1)))
        dist = state.distance(ai_pos, opp_pos)
        values = [self._hard_position_score(state, ai_pos, opp_pos, ai, opponent) * 0.8]

        def soon_usable(skill_id):
            skill = self._skill(skills, skill_id)
            if skill is None:
                return False
            if getattr(skill, "current_cd", 0) > 1:
                return False
            return getattr(ai, "energy", 0) >= max(0, getattr(skill, "energy_cost", 0))

        if soon_usable("bone_explosion"):
            if self._hard_bone_explosion_hits(ai_pos, opp_pos):
                trade_value = (min(30.0, opp_hp) / opp_max_hp) * 520.0
                self_risk = 0.0 if revive_active else (min(30.0, ai_hp) / ai_max_hp) * 260.0
                values.append(trade_value - self_risk + (70 if revive_active else 18))
            else:
                values.append(-42.0)

        if soon_usable("bone_rebuild") and not revive_active and ai_hp <= 35:
            rebuild_value = 30.0
            rebuild_value += max(0.0, 35.0 - ai_hp) * 1.6
            rebuild_value += max(0.0, 7.0 - float(dist)) * 3.5
            if self._hard_bone_explosion_hits(ai_pos, opp_pos):
                rebuild_value += 24.0
            values.append(rebuild_value)

        if soon_usable("normal_attack") and dist <= 1:
            values.append((getattr(ai, "attack", 10) / opp_max_hp) * 430.0 + 8.0)

        if soon_usable("piercing_shot") and (ai_pos[0] == opp_pos[0] or ai_pos[1] == opp_pos[1]):
            values.append((15.0 / opp_max_hp) * 430.0 + 10.0)

        if soon_usable("minor_heal") and ai_hp < ai_max_hp:
            heal = min(15.0, ai_max_hp - ai_hp)
            heal_value = (heal / ai_max_hp) * 360.0
            if ai_hp / ai_max_hp <= 0.35:
                heal_value += 24.0
            values.append(heal_value)

        if soon_usable("focus") and getattr(ai, "energy", 0) < getattr(ai, "max_energy", 100):
            values.append(18.0)

        # Prefer positions that either threaten bone explosion now or can reach it
        # with one dash/roll next turn.
        if self._hard_bone_explosion_hits(ai_pos, opp_pos):
            values.append(28.0 if revive_active else 12.0)
        elif dist <= 5:
            values.append(max(-12.0, 18.0 - dist * 4.0))

        return max(values)

    def _hard_opponent_scenarios(self, state, ai, opponent, deadline):
        """Compact possible current-round player outcomes.

        Only actions from the player's actually carried, off-cooldown and
        affordable skills are represented.  This keeps the hard AI transparent:
        it may know public cooldown/energy information, but it does not invent
        unavailable movement options.
        """
        skills = list(state.all_skills.get(opponent, []))
        usable_ids = {getattr(skill, "skill_id", "") for skill in skills if self._usable(skill, opponent)}
        scenarios = []

        def add(pos, weight, desc="", heal=0.0):
            if time.perf_counter() > deadline:
                return
            if not state.in_bounds(*pos):
                return
            if pos != opponent.pos and state.is_occupied(*pos):
                return
            key = (tuple(pos), round(float(heal), 2), desc)
            scenarios.append({"pos": tuple(pos), "weight": weight, "desc": desc, "heal": heal, "key": key})

        # Staying represents all currently usable non-movement actions: attacks,
        # guard, focus, shields, controls, or choosing no effective move.
        non_move_ids = usable_ids - {"dash", "roll", "blink", "hook_step"}
        stay_weight = 2.6 + 0.35 * len(non_move_ids)
        add(opponent.pos, stay_weight, "停留/可用非位移技能")

        # Healing does not change position but changes expected HP.
        heal_skill = self._skill(skills, "minor_heal")
        if self._usable(heal_skill, opponent):
            heal = min(15, max(0, opponent.max_hp - opponent.hp))
            if heal > 0:
                add(opponent.pos, self._hard_player_action_weight(state, ai, opponent, opponent.pos, "heal"), "小治疗", heal=heal)

        dash = self._skill(skills, "dash")
        if self._usable(dash, opponent):
            row, col = opponent.pos
            for dc in (-1, 1):
                direction_cell = (row, col + dc)
                if not state.in_bounds(*direction_cell):
                    continue
                final = state.clamp_pos(row, col + dc * (3 + self._hard_move_bonus(opponent)))
                weight = self._hard_player_action_weight(state, ai, opponent, final, "dash")
                add(final, weight, "冲刺")

        roll = self._skill(skills, "roll")
        if self._usable(roll, opponent):
            for cell in self._hard_roll_targets(state, opponent):
                weight = self._hard_player_action_weight(state, ai, opponent, cell, "roll")
                add(cell, weight, "翻滚")

        hook = self._skill(skills, "hook_step")
        if self._usable(hook, opponent):
            row, col = opponent.pos
            max_range = 3 + self._hard_move_bonus(opponent)
            for dist in range(1, max_range + 1):
                for dr, dc in [(-dist, 0), (dist, 0), (0, -dist), (0, dist)]:
                    cell = (row + dr, col + dc)
                    if not state.in_bounds(*cell):
                        continue
                    if state.is_occupied(*cell):
                        continue
                    if cell in getattr(state, "mud_cells", set()):
                        continue
                    weight = self._hard_player_action_weight(state, ai, opponent, cell, "hook_step") * 0.85
                    add(cell, weight, "钩步空格位移")

        blink = self._skill(skills, "blink")
        if self._usable(blink, opponent):
            middle = state.rows // 2
            for center_col in range(1, state.cols - 1):
                center = (middle, center_col)
                if time.perf_counter() > deadline:
                    break
                # Blink target must be selected first; final cell is random in 3×3.
                for pos in self._area_3x3(state, center):
                    if not state.is_occupied(*pos):
                        weight = self._hard_player_action_weight(state, ai, opponent, pos, "blink") * 0.18
                        add(pos, weight, "闪现可能落点")

        # Merge duplicate positions/heal buckets and cap to keep the search fast.
        merged = {}
        for sc in scenarios:
            key = (sc["pos"], sc.get("heal", 0.0))
            if key not in merged:
                merged[key] = dict(sc)
            else:
                merged[key]["weight"] += sc["weight"]
                if sc.get("desc") not in merged[key].get("desc", ""):
                    merged[key]["desc"] += "/" + sc.get("desc", "")

        result = sorted(merged.values(), key=lambda x: x["weight"], reverse=True)
        return result[:30] or [{"pos": opponent.pos, "weight": 1.0, "desc": "默认", "heal": 0.0}]

    def _hard_player_action_weight(self, state, ai, opponent, final_pos, action_kind):
        """Estimate how likely the player is to choose this visible legal option.

        When Bone General has HP percentage advantage, players are modeled as
        more likely to move away.  When the player has HP percentage advantage,
        they are modeled as more likely to close in and pressure the AI.
        """
        old_dist = state.distance(opponent.pos, ai.pos)
        new_dist = state.distance(final_pos, ai.pos)
        ai_pct = max(0.0, getattr(ai, "hp", 0)) / max(1, getattr(ai, "max_hp", 1))
        opp_pct = max(0.0, getattr(opponent, "hp", 0)) / max(1, getattr(opponent, "max_hp", 1))
        hp_gap = ai_pct - opp_pct

        if action_kind == "heal":
            weight = 1.1
            if opp_pct <= 0.35:
                weight += 1.2
            if ai_pct > opp_pct + 0.15:
                weight += 0.5
            return max(0.15, weight)

        if action_kind == "dash":
            weight = 1.15
        elif action_kind == "roll":
            weight = 0.85
        elif action_kind == "hook_step":
            weight = 0.75
        elif action_kind == "blink":
            weight = 0.45
        else:
            weight = 1.0

        moved_away = new_dist > old_dist
        moved_closer = new_dist < old_dist
        if hp_gap > 0.12:  # AI has percentage HP advantage: player tends to kite.
            if moved_away:
                weight *= 1.85
            elif moved_closer:
                weight *= 0.55
        elif hp_gap < -0.12:  # Player has percentage HP advantage: player tends to pressure.
            if moved_closer:
                weight *= 1.65
            elif moved_away:
                weight *= 0.70
        else:
            if moved_away:
                weight *= 1.15
            elif moved_closer:
                weight *= 1.05

        # Moving out of the current Bone Explosion area is a plausible but not
        # dominant response; most players do not always run directly away.
        if self._hard_bone_explosion_hits(ai.pos, opponent.pos) and not self._hard_bone_explosion_hits(ai.pos, final_pos):
            weight *= 1.20 if hp_gap > 0.12 else 0.92

        return max(0.10, weight)

    @staticmethod
    def _hard_range_bonus(actor):
        return 1 if getattr(actor, "status", {}).get("range_boost") else 0

    @staticmethod
    def _hard_move_bonus(actor):
        return 1 if getattr(actor, "status", {}).get("move_boost") else 0

    @staticmethod
    def _hard_bone_explosion_hits(ai_pos, opponent_pos):
        ar, ac = ai_pos
        pr, pc = opponent_pos
        return abs(ar - pr) <= 1 and abs(ac - pc) <= 3

    def _hard_ai_final_pos(self, state, ai, skill_id, target):
        if skill_id == "dash" and target is not None:
            return self._hard_dash_final_pos(state, ai, target)
        if skill_id == "roll" and target is not None and state.in_bounds(*target):
            return tuple(target)
        return tuple(ai.pos)

    def _hard_dash_final_pos(self, state, ai, target):
        row, col = ai.pos
        _tr, tc = target
        direction = 1 if tc > col else -1
        return state.clamp_pos(row, col + direction * (3 + self._hard_move_bonus(ai)))

    def _hard_roll_targets(self, state, actor):
        row, col = actor.pos
        max_range = 2 + self._hard_move_bonus(actor)
        candidates = []
        for dist in range(1, max_range + 1):
            for dr, dc in [(-dist, 0), (dist, 0), (0, -dist), (0, dist)]:
                cell = (row + dr, col + dc)
                if not state.in_bounds(*cell):
                    continue
                if state.is_occupied(*cell):
                    continue
                if cell in getattr(state, "mud_cells", set()):
                    continue
                candidates.append(cell)
        return candidates

    def _hard_direction_targets(self, state, origin):
        row, col = origin
        cells = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            cell = (row + dr, col + dc)
            if state.in_bounds(*cell):
                cells.append(cell)
        return cells

    @staticmethod
    def _hard_on_ray(origin, direction, pos):
        orow, ocol = origin
        drow, dcol = direction
        row, col = pos
        if drow == 0 and dcol != 0:
            return row == orow and (col - ocol) * dcol > 0
        if dcol == 0 and drow != 0:
            return col == ocol and (row - orow) * drow > 0
        return False

    def _hard_position_score(self, state, ai_pos, opponent_pos, ai, opponent):
        dist = state.distance(ai_pos, opponent_pos)
        score = 0.0
        revive_active = bool(ai.special_state.get("death_immune") or ai.special_state.get("_bone_revive"))
        ai_hp = max(0.0, float(getattr(ai, "hp", 0)))
        opp_hp = max(0.0, float(getattr(opponent, "hp", 0)))
        ai_hp_pct = ai_hp / max(1.0, float(getattr(ai, "max_hp", 1)))
        hp_gap = ai_hp - opp_hp

        if self._hard_bone_explosion_hits(ai_pos, opponent_pos):
            score += 22 if revive_active else 12
            if dist <= 1 and ai_hp_pct <= 0.30 and not revive_active:
                score -= 12
        else:
            # 原本就会因为离骨爆范围太远而扣分；这里略微加大距离因素。
            score -= min(26, dist * 3.0)

        # 额外的绝对血量距离倾向：血量占优或接近时鼓励靠近；
        # 明显劣势时鼓励拉开距离，避免无复活保护时盲目贴脸。
        if hp_gap >= -8:
            score += max(0.0, 6.0 - float(dist)) * 1.7
        elif hp_gap <= -25:
            score += min(6.0, float(dist)) * 1.4 - 5.0
        else:
            score += max(0.0, 5.0 - float(dist)) * 0.6

        # Being on same row improves future piercing shot; being too far from
        # the center makes Bone Explosion pressure easier to dodge.
        if ai_pos[0] == opponent_pos[0]:
            score += 4
        return score

    def _hard_estimate_opponent_threat_at(self, state, ai_pos, opponent_pos, opponent):
        skills = list(state.all_skills.get(opponent, []))
        threat = 0.0
        dist = state.distance(ai_pos, opponent_pos)

        normal = self._skill(skills, "normal_attack")
        if self._usable(normal, opponent) and dist <= 1:
            threat += max(10, getattr(opponent, "attack", 10)) * 0.75

        heavy = self._skill(skills, "heavy_slash")
        if self._usable(heavy, opponent) and 1 <= dist <= 1 + self._hard_range_bonus(opponent):
            threat += 30 * 0.42

        piercing = self._skill(skills, "piercing_shot")
        if self._usable(piercing, opponent) and (ai_pos[0] == opponent_pos[0] or ai_pos[1] == opponent_pos[1]):
            threat += 15 * 0.45

        area = self._skill(skills, "area_blast")
        if self._usable(area, opponent):
            # If some legal center within 2 of opponent can cover the AI, count it.
            can_cover = False
            for center in self._cells_within(state, opponent_pos, 2, include_self=True):
                if ai_pos in self._area_3x3(state, center):
                    can_cover = True
                    break
            if can_cover:
                threat += 14 * 0.45

        # A generic exclusive-skill threat term keeps the AI cautious against
        # characters whose attack skills are not explicitly modeled here.
        if dist <= 2:
            threat += 8
        elif dist <= 4 and (ai_pos[0] == opponent_pos[0] or ai_pos[1] == opponent_pos[1]):
            threat += 5
        return threat

    @staticmethod
    def _hard_incoming_damage_multiplier(skill_id):
        if skill_id == "roll":
            return 0.55
        if skill_id == "dash":
            return 0.80
        return 1.0

    def _cells_within(self, state, origin, max_dist, include_self=False):
        cells = []
        for r in range(state.rows):
            for c in range(state.cols):
                cell = (r, c)
                dist = state.distance(origin, cell)
                if dist > max_dist:
                    continue
                if not include_self and dist == 0:
                    continue
                cells.append(cell)
        return cells

    # ── normal AI ──────────────────────────────────────────────────────

    def _choose_normal(self, state, ai, opponent, skills):
        attack = self._best_normal_attack(state, ai, opponent, skills)
        in_attack_range = attack is not None
        escape_mode = opponent.hp - ai.hp > 28

        heal = self._choice_if_usable(skills, ai, "minor_heal", lambda: None)
        move_closer = self._normal_movement_choice(state, ai, opponent, skills, closer=True)
        move_random = self._normal_movement_choice(state, ai, opponent, skills, closer=False)
        counter = self._choice_if_usable(skills, ai, "counter_stance", lambda: None)

        if not in_attack_range:
            # Out of range: movement : heal ≈ 75 : 25.  If one side is impossible,
            # the other side receives all probability.
            choice = self._redistributed_pick([
                (move_closer, 75, move_closer is not None),
                (heal, 25, heal is not None),
            ])
            return choice or counter or (None, None, None)

        if escape_mode:
            if heal is None:
                choice = self._redistributed_pick([
                    (attack, 20, attack is not None),
                    (move_random, 80, move_random is not None),
                ])
            else:
                choice = self._redistributed_pick([
                    (attack, 20, attack is not None),
                    (heal, 50, heal is not None),
                    (move_random, 30, move_random is not None),
                ])
            return choice or counter or (None, None, None)

        choice = self._redistributed_pick([
            (attack, 60, attack is not None),
            (heal, 10, heal is not None),
            (move_random, 30, move_random is not None),
        ])
        return choice or counter or (None, None, None)

    def _best_normal_attack(self, state, ai, opponent, skills):
        options = []
        for skill_id, damage in [
            ("fire_tornado", 30),
            ("flame_sweep", 30),
            ("area_blast", 14),
            ("normal_attack", 10),
        ]:
            skill = self._skill(skills, skill_id)
            if not self._usable(skill, ai):
                continue
            target = self._normal_attack_target(state, ai, opponent, skill_id)
            if target is INVALID_TARGET:
                continue
            if not self._normal_attack_can_hit(state, ai, opponent, skill_id):
                continue
            options.append((damage, skill_id, skill, target))

        if not options:
            return None

        max_damage = max(damage for damage, *_ in options)
        top = [(skill, target) for damage, _, skill, target in options if damage == max_damage]
        skill, target = random.choice(top)
        return (ai, skill, target)

    def _normal_attack_can_hit(self, state, ai, opponent, skill_id: str) -> bool:
        if skill_id == "normal_attack":
            return state.distance(ai.pos, opponent.pos) == 1
        if skill_id == "area_blast":
            # There must be at least one center within 2 cells of the AI whose 3×3
            # area contains the opponent.
            for r in range(state.rows):
                for c in range(state.cols):
                    center = (r, c)
                    if state.distance(ai.pos, center) <= 2 and opponent.pos in self._area_3x3(state, center):
                        return True
            return False
        if skill_id == "fire_tornado":
            middle_row = state.rows // 2
            for col in range(1, state.cols - 1):
                if opponent.pos in self._area_3x3(state, (middle_row, col)):
                    return True
            return False
        if skill_id == "flame_sweep":
            return opponent.pos[0] == ai.pos[0]
        return False

    def _normal_attack_target(self, state, ai, opponent, skill_id: str):
        near_cells = self._near_opponent_cells(state, opponent.pos)
        legal = []
        for cell, weight in near_cells:
            if self._is_legal_attack_target(state, ai, skill_id, cell):
                legal.append((cell, weight))
        if not legal:
            return INVALID_TARGET
        return self._weighted_pick(legal)

    def _is_legal_attack_target(self, state, ai, skill_id: str, target) -> bool:
        if target is None or not state.in_bounds(*target):
            return False
        if skill_id == "normal_attack":
            return state.distance(ai.pos, target) == 1
        if skill_id == "area_blast":
            return state.distance(ai.pos, target) <= 2
        if skill_id == "fire_tornado":
            row, col = target
            return row == state.rows // 2 and 0 < col < state.cols - 1
        if skill_id == "flame_sweep":
            return target[0] == ai.pos[0]
        return False

    def _normal_movement_choice(self, state, ai, opponent, skills, closer: bool):
        dash = self._choice_if_usable(skills, ai, "dash", lambda: self._dash_target(state, ai, opponent, closer=closer))
        roll = self._choice_if_usable(skills, ai, "roll", lambda: self._roll_target(state, ai, opponent, closer=closer))
        return self._redistributed_pick([
            (dash, 50, dash is not None),
            (roll, 50, roll is not None),
        ])

    def _dash_target(self, state, ai, opponent, closer: bool):
        row, col = ai.pos
        candidates = []
        for direction in (-1, 1):
            target_col = col + direction
            if not state.in_bounds(row, target_col):
                continue
            final_col = state.clamp_pos(row, col + direction * 3)[1]
            final_pos = (row, final_col)
            score = state.distance(final_pos, opponent.pos)
            candidates.append(((row, target_col), score))
        if not candidates:
            return INVALID_TARGET
        if closer:
            best_score = min(score for _, score in candidates)
            best = [cell for cell, score in candidates if score == best_score]
            return random.choice(best)
        return random.choice([cell for cell, _ in candidates])

    def _roll_target(self, state, ai, opponent, closer: bool):
        row, col = ai.pos
        candidates = []
        for dist in (1, 2):
            for dr, dc in [(-dist, 0), (dist, 0), (0, -dist), (0, dist)]:
                cell = (row + dr, col + dc)
                if not state.in_bounds(*cell):
                    continue
                if state.is_occupied(*cell):
                    continue
                if cell in getattr(state, "mud_cells", set()):
                    continue
                candidates.append((cell, state.distance(cell, opponent.pos)))
        if not candidates:
            return INVALID_TARGET
        if closer:
            best_score = min(score for _, score in candidates)
            best = [cell for cell, score in candidates if score == best_score]
            return random.choice(best)
        return random.choice([cell for cell, _ in candidates])
