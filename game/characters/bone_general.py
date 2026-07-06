from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class BoneGeneral(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="殉爆骨将",
            max_hp=120,
            defense=0,
            attack=13,
            max_energy=110,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "bone_explosion",
                "bone_rebuild",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR / "assets" / "images" / "characters" / "bone_general" / "bone_general.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "bone_explosion": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "bone_general" / "bone_explosion.png"
            ),
            "bone_rebuild": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "bone_general" / "bone_rebuild.png"
            ),
        }
        return image_map.get(skill_id)
