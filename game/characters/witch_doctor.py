from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class WitchDoctor(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="乱魂巫医",
            max_hp=90,
            defense=0,
            attack=11,
            max_energy=100,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "frenzy_curse",
                "chaos_backfire",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR / "assets" / "images" / "characters" / "witch_doctor" / "witch_doctor.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "frenzy_curse": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "witch_doctor" / "frenzy_curse.png"
            ),
            "chaos_backfire": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "witch_doctor" / "chaos_backfire.png"
            ),
        }
        return image_map.get(skill_id)
