from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class WarLord(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="战争领主",
            max_hp=120,
            defense=0,
            attack=15,
            max_energy=110,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "war_command_forms",
                "king_might_formation",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "war_lord.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "war_command_forms": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "war_lord" / "war_lord_three_forms.png"
            ),
            "king_might_formation": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "war_lord" / "war_lord_pressure_field.png"
            ),
        }
        return image_map.get(skill_id)
