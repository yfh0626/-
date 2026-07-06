from characters.fire_mage import FireMage
from characters.space_mage import SpaceMage
from characters.earth_mage import EarthMage
from characters.vine_mage import VineMage
from characters.war_lord import WarLord
from characters.chain_gladiator import ChainGladiator
from characters.shadow_assassin import ShadowAssassin
from characters.blood_berserker import BloodBerserker
from characters.birdman import Birdman
from characters.lizard_rogue import LizardRogue
from characters.bone_general import BoneGeneral
from characters.witch_doctor import WitchDoctor


def create_character(character_id, pos, basic_skill_ids):
    if character_id == "fire_mage":
        return FireMage(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "space_mage":
        return SpaceMage(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "earth_mage":
        return EarthMage(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "vine_mage":
        return VineMage(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "war_lord":
        return WarLord(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "chain_gladiator":
        return ChainGladiator(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "shadow_assassin":
        return ShadowAssassin(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "blood_berserker":
        return BloodBerserker(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "birdman":
        return Birdman(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "lizard_rogue":
        return LizardRogue(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "bone_general":
        return BoneGeneral(pos=pos, basic_skill_ids=basic_skill_ids)

    if character_id == "witch_doctor":
        return WitchDoctor(pos=pos, basic_skill_ids=basic_skill_ids)

    raise ValueError(f"未知角色 ID：{character_id}")
