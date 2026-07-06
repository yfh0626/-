from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class LizardRogue(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="幻鳞蜥客",
            max_hp=100,
            defense=0,
            attack=15,
            max_energy=120,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "chameleon_cloak",
                "tongue_strike",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR / "assets" / "images" / "characters" / "lizard_rogue" / "lizard_rogue.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "tongue_strike": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "lizard_rogue" / "tongue_strike.png"
            ),
            "chameleon_cloak": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "lizard_rogue" / "chameleon_cloak.png"
            ),
        }
        return image_map.get(skill_id)
