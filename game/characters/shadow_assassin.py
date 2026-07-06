from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class ShadowAssassin(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="幽影刺客",
            max_hp=85,
            defense=0,
            attack=18,
            max_energy=110,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "poison_shadow_dart",
                "bone_eroding_poison",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "shadow_assassin.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "poison_shadow_dart": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "shadow_assassin" / "poison_shadow_dart.png"
            ),
            "bone_eroding_poison": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "shadow_assassin" / "bone_eroding_poison.png"
            ),
        }
        return image_map.get(skill_id)
