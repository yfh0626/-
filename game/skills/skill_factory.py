from skills.basic_skills import (
    NormalAttack,
    Guard,
    Dash,
    Blink,
    Focus,
    MinorHeal,
    HeavySlash,
    PiercingShot,
    AreaBlast,
    Roll,
    HookStep,
    ShieldWall,
    CounterStance,
    EnergyCharge,
    Silence,
)

from skills.fire_mage_skills import (
    FireTornado,
    FlameSweep,
)

from skills.space_mage_skills import (
    AstralProtection,
    DimensionSwap,
)

from skills.earth_mage_skills import (
    MudEruption,
    RockSpike,
)

from skills.vine_mage_skills import (
    LifeDrain,
    VineSeal,
)

from skills.birdman_skills import (
    SkyDive,
    FeatherMark,
)

from skills.lizard_rogue_skills import (
    TongueStrike,
    ChameleonCloak,
)

from skills.bone_general_skills import (
    BoneExplosion,
    BoneRebuild,
)

from skills.witch_doctor_skills import (
    FrenzyCurse,
    ChaosBackfire,
)

from skills.war_lord_skills import (
    WarCommandForms,
    KingMightFormation,
)

from skills.chain_gladiator_skills import (
    JudgmentChain,
    GallowsDance,
)

from skills.shadow_assassin_skills import (
    PoisonShadowDart,
    BoneErodingPoison,
)

from skills.blood_berserker_skills import (
    WoundCleave,
    UndyingBloodOath,
)


def create_skill(skill_id):
    skill_map = {
        "normal_attack": NormalAttack,
        "guard": Guard,
        "dash": Dash,
        "blink": Blink,
        "focus": Focus,
        "minor_heal": MinorHeal,

        "heavy_slash": HeavySlash,
        "piercing_shot": PiercingShot,
        "area_blast": AreaBlast,
        "roll": Roll,
        "hook_step": HookStep,
        "shield_wall": ShieldWall,
        "counter_stance": CounterStance,
        "energy_charge": EnergyCharge,
        "silence": Silence,

        "fire_tornado": FireTornado,
        "flame_sweep": FlameSweep,

        "astral_protection": AstralProtection,
        "dimension_swap": DimensionSwap,

        "mud_eruption": MudEruption,
        "rock_spike": RockSpike,

        "life_drain": LifeDrain,
        "vine_seal": VineSeal,

        "sky_dive": SkyDive,
        "feather_mark": FeatherMark,

        "tongue_strike": TongueStrike,
        "chameleon_cloak": ChameleonCloak,

        "bone_explosion": BoneExplosion,
        "bone_rebuild": BoneRebuild,

        "frenzy_curse": FrenzyCurse,
        "chaos_backfire": ChaosBackfire,

        "war_command_forms": WarCommandForms,
        "king_might_formation": KingMightFormation,

        "judgment_chain": JudgmentChain,
        "gallows_dance": GallowsDance,

        "poison_shadow_dart": PoisonShadowDart,
        "bone_eroding_poison": BoneErodingPoison,

        "wound_cleave": WoundCleave,
        "undying_blood_oath": UndyingBloodOath,
    }

    if skill_id not in skill_map:
        raise ValueError(f"未知技能 ID：{skill_id}")

    return skill_map[skill_id]()


def create_skills(skill_ids):
    return [create_skill(skill_id) for skill_id in skill_ids]
