from pathlib import Path


class Character:
    def __init__(
        self,
        name,
        max_hp,
        pos,
        exclusive_skill_ids,
        basic_skill_ids,
        defense=0,
        attack=10,
        max_energy=100,
        move_power=1,
        sprite_path=None,
        sprite_size=(130, 170),
    ):
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp

        self.pos = pos
        self.shield = 0

        # 防御值机制已删除：保留属性仅兼容旧代码，实际恒为 0。
        self.defense = 0
        self.attack = attack
        self.max_energy = max_energy
        self.energy = max_energy
        self.move_power = move_power

        self.exclusive_skill_ids = exclusive_skill_ids
        self.basic_skill_ids = basic_skill_ids

        self.sprite_path = sprite_path
        self.sprite_size = sprite_size

        self.status = {}
        self.special_state = {}

    def on_round_end(self, state, log):
        pass

    def all_skill_ids(self):
        return self.exclusive_skill_ids + self.basic_skill_ids

    def get_sprite_path(self):
        if self.sprite_path is None:
            return None
        return Path(self.sprite_path)

    def get_sprite_size(self):
        return self.sprite_size
