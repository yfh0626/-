from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class EarthMage(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="大地法师",
            max_hp=80,
            attack=5,
            max_energy=150,
            pos=pos,
            exclusive_skill_ids=[
                "mud_eruption",
                "rock_spike",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "earth_mage.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "mud_eruption": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "earth_mage" / "mud_chain.png"
            ),
            "rock_spike": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "earth_mage" / "rock_spike_shock.png"
            ),
        }
        return image_map.get(skill_id)
