from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class VineMage(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="藤蔓法师",
            max_hp=60,
            attack=10,
            max_energy=150,
            pos=pos,
            exclusive_skill_ids=[
                "life_drain",
                "vine_seal",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "vine_mage.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "life_drain": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "vine_mage" / "forest_absorb.png"
            ),
            "vine_seal": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "vine_mage" / "vine_seal.png"
            ),
        }
        return image_map.get(skill_id)
