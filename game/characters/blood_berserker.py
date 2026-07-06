from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class BloodBerserker(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="血誓狂战",
            max_hp=130,
            defense=0,
            attack=16,
            max_energy=100,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "wound_cleave",
                "undying_blood_oath",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "blood_berserker.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "wound_cleave": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "blood_berserker" / "blood_berserker_rending_slash.png"
            ),
            "undying_blood_oath": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "blood_berserker" / "blood_berserker_undying_oath.png"
            ),
        }
        return image_map.get(skill_id)

