from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class FireMage(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="火焰法师",
            max_hp=50,
            attack=20,
            max_energy=250,
            pos=pos,
            exclusive_skill_ids=[
                "fire_tornado",
                "flame_sweep",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "fire_mage.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "fire_tornado": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "fire_mage" / "fire_tornado.png"
            ),
            "flame_sweep": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "fire_mage" / "flame_sweep.png"
            ),
        }
        return image_map.get(skill_id)
