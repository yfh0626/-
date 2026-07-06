from pathlib import Path

from characters.character import Character

BASE_DIR = Path(__file__).resolve().parent.parent


class ChainGladiator(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            name="铁链角斗士",
            max_hp=110,
            defense=0,
            attack=15,
            max_energy=120,
            move_power=1,
            pos=pos,
            exclusive_skill_ids=[
                "judgment_chain",
                "gallows_dance",
            ],
            basic_skill_ids=basic_skill_ids,
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "chain_gladiator.png"
            ),
            sprite_size=(130, 170),
        )

    def get_skill_image_path(self, skill_id):
        image_map = {
            "judgment_chain": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "chain_gladiator" / "chain_gladiator_guilty_chain.png"
            ),
            "gallows_dance": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "chain_gladiator" / "chain_gladiator_execution_dance.png"
            ),
        }
        return image_map.get(skill_id)

