from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class SpaceMage(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="空间法师",
            max_hp=60,
            attack=15,
            max_energy=150,
            pos=pos,
            exclusive_skill_ids=[
                "astral_protection",
                "dimension_swap",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "space_mage.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "astral_protection": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "space_mage" / "astral_guard.png"
            ),
            "dimension_swap": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "space_mage" / "dimension_swap.png"
            ),
        }
        return image_map.get(skill_id)

