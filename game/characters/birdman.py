from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class Birdman(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="狂翼鸟人",
            max_hp=90,
            defense=0,
            attack=10,
            max_energy=100,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "sky_dive",
                "feather_mark",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR / "assets" / "images" / "characters" / "birdman" / "birdman.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "sky_dive": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "birdman" / "sky_dive.png"
            ),
            "feather_mark": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "birdman" / "feather_mark.png"
            ),
        }
        return image_map.get(skill_id)
