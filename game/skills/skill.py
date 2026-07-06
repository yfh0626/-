class Skill:
    def __init__(
        self,
        skill_id,
        name,
        description,
        cooldown=0,
        target_required=True,
        range=None,
        energy_cost=0,
    ):
        self.skill_id = skill_id
        self.name = name
        self.description = description

        self.cooldown = cooldown
        self.current_cd = 0

        self.target_required = target_required
        self.range = range  # None=无限制, int=曼哈顿距离上限
        self.energy_cost = energy_cost  # 所有主动技能统一能量消耗；未配置时默认为 0

    def can_use(self, caster=None):
        if self.current_cd > 0:
            return False
        if caster is not None:
            return getattr(caster, "energy", 0) >= self.energy_cost
        return True

    def start_cooldown(self):
        self.current_cd = self.cooldown

    def reduce_cooldown(self):
        if self.current_cd > 0:
            self.current_cd -= 1

    def cast(self, state, caster, target, log):
        raise NotImplementedError

    def on_turn_start(self, state, caster, log):
        pass

    def on_turn_end(self, state, caster, log):
        pass
