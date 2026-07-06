import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QLabel, QPushButton, QTextEdit,
    QStackedWidget, QLineEdit, QCheckBox,
    QGraphicsOpacityEffect, QGraphicsView, QGraphicsScene, QFrame
)

from PySide6.QtGui import QPainter, QPixmap, QPen, QBrush, QColor, QTransform
from PySide6.QtCore import Qt, QRect, Signal, QEvent, QPropertyAnimation, QEasingCurve

from ui.image_page import ImagePage
from login.login_page import LoginPage
from core.battle_state import BattleState
from core.battle_ai import AI_CONFIGS, BattleAIController, get_ai_config
from characters.character_factory import create_character
from skills.skill_factory import create_skill, create_skills
from ui.skill_button import SkillButton

from login.auth_service import AuthService
from crypto.crypto import GameCryptoEngine

HERO_CONFIGS = [
    {
        "id": "fire_mage",
        "name": "火焰法师",
        "role": "法师 / 爆发输出",
        "desc": "高爆发远程法师。当前已接入战斗逻辑，可在战斗中使用火龙卷、烈焰横扫等专属技能。",
        "skills": "火龙卷、烈焰横扫",
        "exclusive_skill_ids": ["fire_tornado", "flame_sweep"],
        "implemented": True,
    },
    {
        "id": "earth_mage",
        "name": "大地法师",
        "role": "法师 / 控场",
        "desc": "依靠泥潭、石柱和岩突限制敌方走位，偏向控场。",
        "skills": "泥潭迸发、岩突震荡",
        "exclusive_skill_ids": ["mud_eruption", "rock_spike"],
        "implemented": True,
    },
    {
        "id": "vine_mage",
        "name": "藤蔓法师",
        "role": "控制 / 吸能型法师",
        "desc": (
            "操控藤蔓与自然能量的控制型法师。"
            "森罗汲取可以对 2×2 区域内的敌人吸取能量；"
            "万藤封禁可以阻止敌方本轮技能生效，"
            "并限制其下一轮使用位移技能。"
        ),
        "skills": "森罗汲取、万藤封禁",
        "exclusive_skill_ids": [
            "life_drain",
            "vine_seal",
        ],
        "implemented": True,
    },
    {
        "id": "space_mage",
        "name": "空间法师",
        "role": "法师 / 反制机动",
        "desc": "通过空间切割和换位制造反制机会。当前已接入战斗逻辑。",
        "skills": "空间切割、空间换位",
        "exclusive_skill_ids": [
            "astral_protection",
            "dimension_swap",
        ],
        "implemented": True,
    },
    {
        "id": "war_lord",
        "name": "战争领主",
        "role": "战士 / 压阵强化",
        "desc": "依靠战令强化位移和攻击，并用压阵削弱敌方行动。",
        "skills": "战令三式、王威压阵",
        "exclusive_skill_ids":[
            "war_command_forms",
            "king_might_formation",
        ],
        "implemented": True,
    },
    {
        "id": "chain_gladiator",
        "name": "铁链角斗士",
        "role": "战士 / 牵制近战",
        "desc": "使用锁链限制双方距离，距离越远伤害越高。",
        "skills": "断罪锁链、绞刑轮舞",
        "exclusive_skill_ids": [
                "judgment_chain",
                "gallows_dance",
            ],
        "implemented": True,
    },
    {
        "id": "shadow_assassin",
        "name": "幽影刺客",
        "role": "战士 / 毒伤持续",
        "desc": "通过毒影飞镖挂毒，再用催毒提高持续伤害。",
        "skills": "毒影飞镖、蚀骨催毒",
        "exclusive_skill_ids": [
                "poison_shadow_dart",
                "bone_eroding_poison",
            ],
        "implemented": True,
    },
    {
        "id": "blood_berserker",
        "name": "血誓狂战",
        "role": "战士 / 低血爆发",
        "desc": "血量越低爆发越强，血誓状态下短时间内不会死亡。",
        "skills": "裂创斩、血誓不灭",
        "exclusive_skill_ids": [
                    "wound_cleave",
                    "undying_blood_oath",
                ],
        "implemented": True,
    },
    {
        "id": "birdman",
        "name": "狂翼鸟人",
        "role": "兽人 / 飞袭印记",
        "desc": (
            "拥有极强机动能力，可以使用俯天急袭飞往任意格。"
            "坠羽印记会持续攻击敌人所在列，"
            "并在第三轮爆炸；"
            "俯天急袭飞往印记格时还能触发范围更大的飞袭引爆。"
        ),
        "skills": "俯天急袭、坠羽印记",
        "exclusive_skill_ids": [
            "sky_dive",
            "feather_mark",
        ],
        "implemented": True,
    },
    {
        "id": "lizard_rogue",
        "name": "幻鳞蜥客",
        "role": "兽人 / 隐身奇袭",
        "desc": (
            "擅长利用隐身状态发动突袭。"
            "融影变色会在本轮结束后进入隐身；"
            "断舌奇袭可以攻击三格范围内的敌人，"
            "在隐身或刚刚显形时必定命中，"
            "并将敌人向自身方向拉近一格。"
        ),
        "skills": "融影变色、断舌奇袭",
        "exclusive_skill_ids": [
            "chameleon_cloak",
            "tongue_strike",
        ],
        "implemented": True,
    },
    {
        "id": "bone_general",
        "name": "殉爆骨将",
        "role": "兽人 / 自毁复生",
        "desc": "用骨爆进行高风险换血，并可进入残骨状态复活。当前已接入战斗逻辑。",
        "skills": "同殒骨爆、残骨重组",
        "exclusive_skill_ids": [
            "bone_explosion",
            "bone_rebuild",
        ],
        "implemented": True,
    },
    {
        "id": "witch_doctor",
        "name": "乱魂巫医",
        "role": "兽人 / 随机诅咒",
        "desc": "通过锁定诅咒让敌方在后续回合随机移动并损失能量，再用失控反噬打出控制或斩血效果。当前已接入战斗逻辑。",
        "skills": "疯咒乱魂、失控反噬",
        "exclusive_skill_ids": [
            "frenzy_curse",
            "chaos_backfire",
        ],
        "implemented": True,
    },
]

RESULT_IMAGE_FILES = {
    "birdman": "birdman_win.png",
    "blood_berserker": "blood_berserker_win.png",
    "bone_general": "bone_general_win.png",
    "chain_gladiator": "chain_gladiator_win.png",
    "earth_mage": "earth_mage_win.png",
    "fire_mage": "fire_mage_win.png",
    "lizard_rogue": "lizard_rogue_win.png",
    "shadow_assassin": "shadow_assassin_win.png",
    "space_mage": "space_mage_win.png",
    "vine_mage": "vine_mage_win.png",
    "war_lord": "war_lord_win.png",
    "witch_doctor": "witch_doctor_win.png",
}

DRAW_RESULT_IMAGE = "draw.png"

def get_hero_config(hero_id):
    for hero in HERO_CONFIGS:
        if hero["id"] == hero_id:
            return hero
    return HERO_CONFIGS[0]


HERO_SKILL_DETAIL_OVERRIDES = {
    "fire_tornado": "选择中间行非边缘格，命中目标周围 3x3，造成 30 点范围伤害。",
    "flame_sweep": "攻击自己所在整行，造成 30 点伤害。",
    "mud_eruption": "首次放置泥潭；场上已有泥潭时引爆十字范围，造成 20 点无视防御范围伤害。",
    "rock_spike": "选择同行或同列格，造成 20 点无视防御范围伤害。",
    "life_drain": "选择 2x2 区域左上角；敌人在区域内时造成 20 点伤害，并附加吸能标记。",
    "vine_seal": "必定阻止敌方本轮技能生效。",
    "astral_protection": "本轮蓄势，下一轮获得无敌状态。",
    "dimension_swap": "与敌人交换位置；若敌方本轮攻击，攻击会反弹给自身。",
    "war_command_forms": "启动三段战令：一式位移 +1 并首次受击免疫；二式攻击伤害 +5、范围 +1；三式当前不再提供减伤。",
    "king_might_formation": "获得 1 点战意；战意不足时削弱敌方移动，战意达到 2 点可消耗并相邻追击 15 点伤害。",
    "judgment_chain": "首次选择 3 格内目标格牵制；牵制后再次选择 5 格内目标格，敌人在目标格时造成 5 + 5 x 当前距离伤害，未命中也消耗牵制并进入冷却。",
    "gallows_dance": "以自身上下左右相邻格判定；敌人相邻时无锁链 14 点，有锁链 20 点并缩短链距、削弱敌方攻击；未命中也进入冷却。",
    "poison_shadow_dart": "同线投掷，造成 10 点伤害并中毒 3 回合；毒每回合造成 5 点无视防御伤害。",
    "bone_eroding_poison": "目标已中毒时，使本轮毒伤等量追加一次，通常为 5 点。",
    "wound_cleave": "同线 2 格内攻击，造成 12 + 4 x 血痕层数伤害；血怒时追加 5 点，并叠加 1 层血痕。",
    "undying_blood_oath": "生命不高于 35% 时可用；获得 2 回合不死和 2 层血怒，并转化为横扫形态。横扫伤害为已损生命 50% + 10。",
    "sky_dive": "飞往任意空格；落点距敌人不超过 1 格时造成 18 点伤害。",
    "feather_mark": "选择一列留下 3 回合印记；敌人在该列时前两次 8 点伤害，最后爆炸 20 点伤害。",
    "tongue_strike": "同线 3 格内拉近并攻击；普通 20 点伤害，隐身时 28 点伤害。",
    "chameleon_cloak": "进入隐身 2 回合，强化断舌奇袭。",
    "bone_explosion": "若敌人在 3x7 范围内，双方各受 30 点无视防御伤害；敌人离开范围则自己死亡，可被残骨重组救回。",
    "bone_rebuild": "进入残骨状态；首次死亡时复活并恢复 35 点生命。",
    "frenzy_curse": "锁定敌人，使其从下一回合开始随机移动 2 回合，每回合扣除 8 点能量。",
    "chaos_backfire": "选择 2x2 区域；命中乱魂中的敌人时使当前生命减半，否则使敌人进入 2 回合随机移动。",
}


def format_skill_range(skill):
    skill_range = getattr(skill, "range", None)
    if skill_range is None:
        return "不限/按技能规则"
    return f"{skill_range} 格"


def get_hero_detail_text(hero):
    character = create_character(hero["id"], (0, 0), [])
    stat_text = (
        f"生命：{character.max_hp}  攻击：{character.attack}\n"
        f"能量：{character.max_energy}  移动：{character.move_power}"
    )

    skill_lines = []
    for skill_id in hero.get("exclusive_skill_ids", []):
        skill = create_skill(skill_id)
        summary = HERO_SKILL_DETAIL_OVERRIDES.get(
            skill_id,
            getattr(skill, "description", "")
        )
        skill_lines.append(
            f"{skill.name}：CD {skill.cooldown}，能耗 {skill.energy_cost}，范围 {format_skill_range(skill)}。\n"
            f"{summary}"
        )

    return (
        f"定位：{hero['role']}\n\n"
        f"基础数值：\n{stat_text}\n\n"
        f"专属技能：\n" + "\n\n".join(skill_lines) + "\n\n"
        f"角色说明：\n{hero['desc']}"
    )


# 通用技能选择界面的数据接口。
# 后续如果新增技能，通常只需要：
# 1. 在 skills/basic_skills.py 或其它技能文件中实现 Skill 子类；
# 2. 在 skills/skill_factory.py 的 skill_map 中注册同名 skill_id；
# 3. 在下面 GENERIC_SKILL_CONFIGS 中补充/修改该技能，并把 implemented 设为 True。
DEFAULT_BASIC_SKILL_IDS = [
    "normal_attack",
    "guard",
    "dash",
    "blink",
    "focus",
    "minor_heal",
]

GENERIC_SKILL_CONFIGS = [
    {
        "id": "normal_attack",
        "name": "普通攻击",
        "type": "攻击",
        "desc": "攻击上下左右相邻 1 格内的敌人，造成 10 点伤害，无冷却，目标不能超出棋盘边界。",
        "implemented": True,
    },
    {
        "id": "dash",
        "name": "冲刺",
        "type": "位移",
        "desc": "向左或向右冲刺 3 格；若落点与敌人重合，则按位移规则处理，不取消动作。冷却 2 回合。",
        "implemented": True,
    },
    {
        "id": "blink",
        "name": "闪现",
        "type": "位移",
        "desc": "选择中间行除两边外的格子，并在以该格为中心的 3×3 范围内随机出现在无人格。冷却 3 回合。",
        "implemented": True,
    },
    {
        "id": "guard",
        "name": "格挡",
        "type": "防御",
        "desc": "选择上下左右相邻 1 格作为格挡方向，挡住该方向上的非范围攻击；对范围攻击无效。冷却 2 回合。",
        "implemented": True,
    },
    {
        "id": "focus",
        "name": "蓄势",
        "type": "辅助",
        "desc": "恢复 30 点能量，不超过角色能量上限。无冷却。",
        "implemented": True,
    },
    {
        "id": "minor_heal",
        "name": "小治疗",
        "type": "辅助",
        "desc": "回复少量生命值。当前项目中已有实现，后续可以按正式规则替换。",
        "implemented": True,
    },
    {
        "id": "heavy_slash",
        "name": "重斩",
        "type": "攻击",
        "desc": "预留攻击技能接口：可以设计为近距离高伤害攻击。",
        "implemented": True,
    },
    {
        "id": "piercing_shot",
        "name": "贯穿射击",
        "type": "攻击",
        "desc": "预留攻击技能接口：可以设计为直线穿透攻击。",
        "implemented": True,
    },
    {
        "id": "area_blast",
        "name": "范围爆破",
        "type": "攻击",
        "desc": "预留攻击技能接口：可以设计为小范围区域伤害。",
        "implemented": True,
    },
    {
        "id": "roll",
        "name": "翻滚",
        "type": "位移",
        "desc": "预留位移技能接口：可以设计为短距离位移并获得闪避。",
        "implemented": True,
    },
    {
        "id": "hook_step",
        "name": "钩步",
        "type": "位移",
        "desc": "预留位移技能接口：可以设计为靠近或拉开双方距离。",
        "implemented": True,
    },
    {
        "id": "shield_wall",
        "name": "盾墙",
        "type": "防御",
        "desc": "预留防御技能接口：可以设计为大幅减伤但限制移动。",
        "implemented": True,
    },
    {
        "id": "counter_stance",
        "name": "反击姿态",
        "type": "防御",
        "desc": "预留防御技能接口：可以设计为受击后反击。",
        "implemented": True,
    },
    {
        "id": "energy_charge",
        "name": "能量充盈",
        "type": "辅助",
        "desc": "预留辅助技能接口：可以设计为恢复能量或降低冷却。",
        "implemented": True,
    },
    {
        "id": "silence",
        "name": "沉默",
        "type": "控制",
        "desc": "预留控制技能接口：可以设计为短时间限制敌方技能。",
        "implemented": True,
    },
]


def get_generic_skill_config(skill_id):
    for skill in GENERIC_SKILL_CONFIGS:
        if skill["id"] == skill_id:
            return skill
    return GENERIC_SKILL_CONFIGS[0]


SKILL_DETAIL_OVERRIDES = {
    "normal_attack": "攻击上下左右相邻 1 格内的敌人，伤害等于角色基础伤害。",
    "heavy_slash": "攻击上下左右相邻 1 格内的敌人，造成 30 点伤害。",
    "piercing_shot": "攻击同行或同列的敌人，造成 15 点伤害。",
    "area_blast": "以自己为中心造成 3x5 范围伤害；敌人在上下左右相邻位置时追加 5 点伤害。不需要选择目标格。",
    "roll": "同行或同列移动最多 2 格；若对方本轮使用攻击技能且没有命中你，回合末获得一次闪避状态。",
    "hook_step": "选择 3 格内同行或同列目标；选中敌人则拉近敌人，选中空格则自己移动过去。",
    "shield_wall": "本回合受到的伤害减少 70%。",
    "counter_stance": "本回合受到攻击时返还本次完整伤害，自己只承受 50% 伤害。",
    "energy_charge": "我方所有技能当前冷却减少 2 回合。",
    "silence": "阻止敌人本轮行动。仅对通用技能有效。",
    "minor_heal": "回复自身 15 点生命，不超过最大生命值。",
}


def get_skill_detail_info(skill_id):
    config = get_generic_skill_config(skill_id)
    info = {
        "cooldown": "未接入",
        "energy_cost": "未接入",
        "description": SKILL_DETAIL_OVERRIDES.get(skill_id, config["desc"]),
    }

    if not config["implemented"]:
        return info

    try:
        skill = create_skill(skill_id)
    except Exception:
        return info

    info["cooldown"] = getattr(skill, "cooldown", 0)
    info["energy_cost"] = getattr(skill, "energy_cost", 0)
    info["description"] = SKILL_DETAIL_OVERRIDES.get(
        skill_id,
        getattr(skill, "description", config["desc"]),
    )
    return info

class HomePage(ImagePage):
    enter_battle = Signal()
    enter_card_select = Signal()
    enter_hero_select = Signal()
    enter_ai_select = Signal()
    exit_game = Signal()

    def __init__(self):
        super().__init__("home_bg.png")
        self.current_hero_id = "fire_mage"
        self.selected_skill_ids = DEFAULT_BASIC_SKILL_IDS.copy()
        self.current_ai_difficulty = "normal"

        self.title = QLabel("暗夜竞技场", self)
        self.title.setGeometry(468, 55, 600, 85)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 58px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.subtitle = QLabel("战前准备大厅", self)
        self.subtitle.setGeometry(568, 138, 400, 40)
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("""
            QLabel {
                color: #d6a85f;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.create_player_panel()
        self.create_center_panel()
        self.create_right_panel()
        self.create_bottom_buttons()

    def panel_style(self):
        return """
            QLabel {
                color: #f5e6c8;
                background-color: rgba(10, 8, 6, 180);
                border: 2px solid #8f6a36;
                border-radius: 10px;
                font-size: 20px;
                font-weight: bold;
            }
        """

    def button_style(self, font_size=26):
        return f"""
            QPushButton {{
                color: #f5e6c8;
                background-color: rgba(90, 24, 18, 220);
                border: 2px solid #d6a85f;
                border-radius: 8px;
                font-size: {font_size}px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: rgba(145, 38, 25, 240);
            }}

            QPushButton:pressed {{
                background-color: rgba(60, 18, 12, 240);
            }}
        """

    def create_image_slot(self, geometry, image_path=None):
        label = QLabel(self)
        label.setGeometry(*geometry)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        if image_path is not None:
            base_dir = Path(__file__).resolve().parent
            pixmap = QPixmap(str(base_dir / image_path))
            if not pixmap.isNull():
                label.setPixmap(
                    self.fit_pixmap_to_slot(
                        pixmap,
                        geometry[2],
                        geometry[3]
                    )
                )

        return label

    def fit_pixmap_to_slot(self, pixmap, width, height):
        """
        保持原图比例，放大并居中裁剪。
        最终返回与目标框完全一致大小的图片。
        """
        if pixmap.isNull():
            return pixmap

        scaled = pixmap.scaled(
            width,
            height,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        x = max(0, (scaled.width() - width) // 2)
        y = max(0, (scaled.height() - height) // 2)

        return scaled.copy(x, y, width, height)

    def transparent_button_style(self):
        return """
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                border: none;
            }

            QPushButton:hover {
                background-color: rgba(214, 168, 95, 35);
                border: 1px solid rgba(240, 210, 140, 120);
                border-radius: 6px;
            }

            QPushButton:pressed {
                background-color: rgba(120, 30, 20, 60);
            }
        """

    def get_skill_image_path(self, skill_id):
        """
        获取主页卡牌图片路径。

        查找顺序：
        1. 当前角色专属技能目录；
        2. 通用技能图片目录。

        约定：
        assets/images/characters_skills/<角色 ID>/<技能 ID>.png
        assets/images/skills/<技能 ID>.png
        """
        base_dir = Path(__file__).resolve().parent

        # 当前选择角色的专属技能目录。
        character_skill_path = (
            base_dir
            / "assets"
            / "images"
            / "characters_skills"
            / f"{self.current_hero_id}"
            / f"{skill_id}.png"
        )

        if character_skill_path.exists():
            return character_skill_path

        try:
            hero = create_character(self.current_hero_id, (0, 0), [])
            mapped_path = hero.get_skill_image_path(skill_id)
            if mapped_path is not None and Path(mapped_path).exists():
                return mapped_path
        except Exception:
            pass

        # 通用技能图片目录。
        return (
            base_dir
            / "assets"
            / "images"
            / "skills"
            / f"{skill_id}.png"
        )


    def get_current_display_skill_ids(self):
        hero = get_hero_config(self.current_hero_id)
        exclusive_skill_ids = hero.get("exclusive_skill_ids", [])

        return exclusive_skill_ids + self.selected_skill_ids


    def refresh_card_slots(self):
        if not hasattr(self, "card_slots"):
            return

        display_skill_ids = self.get_current_display_skill_ids()

        for i, slot in enumerate(self.card_slots):
            slot.clear()

            if i >= len(display_skill_ids):
                continue

            skill_id = display_skill_ids[i]
            image_path = self.get_skill_image_path(skill_id)
            pixmap = QPixmap(str(image_path))

            if not pixmap.isNull():
                slot.setPixmap(
                    self.fit_pixmap_to_slot(
                        pixmap,
                        slot.width(),
                        slot.height()
                    )
                )
            else:
                print("主页技能图片加载失败：", image_path)


    def create_player_panel(self):
        # 左侧个人信息区域：上方头像框 + 下方信息框
        self.player_avatar = QLabel(self)
        self.player_avatar.setGeometry(87, 235, 185, 150)
        self.player_avatar.setAlignment(Qt.AlignCenter)
        self.player_avatar.setStyleSheet("background: transparent; border: none;")

        self.player_name_label = QLabel(self)
        self.player_name_label.setGeometry(60, 515, 250, 50)
        self.player_name_label.setAlignment(Qt.AlignCenter)
        self.player_name_label.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 26px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.stats_label = QLabel(self)
        self.stats_label.setGeometry(60, 770, 250, 80)
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 22px;
                font-weight: bold;
                background: transparent;
            }
        """)

    def set_player_info(self, username, avatar_path):
        self.player_name_label.setText(username)
        base_dir = Path(__file__).resolve().parent
        pixmap = QPixmap(str(base_dir / avatar_path))
        if not pixmap.isNull():
            self.player_avatar.setPixmap(
                self.fit_pixmap_to_slot(
                    pixmap,
                    self.player_avatar.width(),
                    self.player_avatar.height()
                )
            )
        else:
            self.player_avatar.clear()

    def set_player_stats(self, stats):
        if stats is None:
            self.stats_label.setText("")
            return
        wins = stats["wins"]
        total = stats["total_games"]
        self.stats_label.setText(f"胜场: {wins} / 总场: {total}")

    def create_center_panel(self):
        # 中间 8 个技能/卡牌图片格子
        self.card_slots = []

        slot_geometries = [
            (380, 253, 150, 240),
            (555, 253, 150, 240),
            (730, 253, 150, 240),
            (900, 253, 150, 240),

            (380, 522, 150, 240),
            (555, 522, 150, 240),
            (730, 522, 150, 240),
            (900, 522, 150, 240),
        ]

        display_skill_ids = self.get_current_display_skill_ids()

        for i, geometry in enumerate(slot_geometries):
            image_path = None
            if i < len(display_skill_ids):
                image_path = self.get_skill_image_path(display_skill_ids[i])

            slot = self.create_image_slot(geometry, image_path)
            self.card_slots.append(slot)

        # 背景图上“进入选技能”的透明点击区域
        self.card_button = QPushButton("", self)
        self.card_button.setGeometry(555, 777, 320, 58)
        self.card_button.setCursor(Qt.PointingHandCursor)
        self.card_button.setStyleSheet(self.transparent_button_style())
        self.card_button.clicked.connect(self.enter_card_select.emit)

    def create_right_panel(self):
        # 右上角角色图片框
        self.hero_panel = self.create_image_slot(
            (1192, 250, 260, 220),
            Path("assets") / "images" / "heroes" / f"{self.current_hero_id if hasattr(self, 'current_hero_id') else 'fire_mage'}.png"
        )

        self.hero_button = QPushButton("", self)
        self.hero_button.setGeometry(1182, 482, 255, 58)
        self.hero_button.setCursor(Qt.PointingHandCursor)
        self.hero_button.setStyleSheet(self.transparent_button_style())
        self.hero_button.clicked.connect(self.enter_hero_select.emit)

        # 右下角 AI 图片框
        self.ai_panel = self.create_image_slot(
            (1192, 638, 260, 190),
            Path("assets") / "images" / "ai" / "ai_normal.png"
        )

        self.ai_button = QPushButton("", self)
        self.ai_button.setGeometry(1180, 813, 255, 58)
        self.ai_button.setCursor(Qt.PointingHandCursor)
        self.ai_button.setStyleSheet(self.transparent_button_style())
        self.ai_button.clicked.connect(self.enter_ai_select.emit)

        self.ai_name_label = QLabel("普通 AI", self)
        self.ai_name_label.setGeometry(1190, 584, 260, 40)
        self.ai_name_label.setAlignment(Qt.AlignCenter)
        self.ai_name_label.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                background: rgba(0, 0, 0, 70);
                border: 1px solid rgba(214, 168, 95, 120);
                border-radius: 6px;
                font-size: 22px;
                font-weight: bold;
            }
        """)

    def create_bottom_buttons(self):
        # 底部“进入战斗”透明点击区域
        self.battle_button = QPushButton("", self)
        self.battle_button.setGeometry(506, 880, 475, 82)
        self.battle_button.setCursor(Qt.PointingHandCursor)
        self.battle_button.setStyleSheet(self.transparent_button_style())
        self.battle_button.clicked.connect(self.enter_battle.emit)

        # 右下角“退出游戏”透明点击区域
        self.exit_button = QPushButton("", self)
        self.exit_button.setGeometry(1370, 946, 130, 45)
        self.exit_button.setCursor(Qt.PointingHandCursor)
        self.exit_button.setStyleSheet(self.transparent_button_style())
        self.exit_button.clicked.connect(self.exit_game.emit)

    def set_current_hero(self, hero):
        self.current_hero_id = hero["id"]

        if hasattr(self, "hero_panel"):
            base_dir = Path(__file__).resolve().parent
            image_path = base_dir / "assets" / "images" / "heroes" / f"{hero['id']}.png"
            pixmap = QPixmap(str(image_path))

            if not pixmap.isNull():
                self.hero_panel.setPixmap(
                    self.fit_pixmap_to_slot(
                        pixmap,
                        self.hero_panel.width(),
                        self.hero_panel.height()
                    )
                )

        self.refresh_card_slots()

    def set_current_skills(self, skill_ids):
        self.selected_skill_ids = list(skill_ids)
        self.refresh_card_slots()

    def set_current_ai(self, difficulty):
        self.current_ai_difficulty = difficulty if difficulty in AI_CONFIGS else "normal"
        config = get_ai_config(self.current_ai_difficulty)
        if hasattr(self, "ai_name_label"):
            self.ai_name_label.setText(config["name"])

class CardSelectPage(ImagePage):
    back_home = Signal()

    def __init__(self):
        super().__init__("card_pool_bg.png")

        self.title = QLabel("暗夜竞技场", self)
        self.title.setGeometry(468, 55, 600, 85)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 58px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.panel = QLabel(
            "卡池图鉴 / 选卡界面\n\n"
            "这里后面放：\n"
            "1. 左侧筛选条件\n"
            "2. 中间卡池网格\n"
            "3. 右侧卡牌详情\n"
            "4. 加入卡组 / 确认选择按钮",
            self
        )
        self.panel.setGeometry(180, 180, 1176, 650)
        self.panel.setAlignment(Qt.AlignCenter)
        self.panel.setStyleSheet("""
            QLabel {
                color: #f5e6c8;
                background-color: rgba(10, 8, 6, 185);
                border: 2px solid #d6a85f;
                border-radius: 12px;
                font-size: 30px;
                font-weight: bold;
            }
        """)

        self.back_button = QPushButton("返回主页", self)
        self.back_button.setGeometry(1180, 870, 220, 60)
        self.back_button.setStyleSheet(self.button_style())
        self.back_button.clicked.connect(self.back_home.emit)

    def button_style(self):
        return """
            QPushButton {
                color: #f5e6c8;
                background-color: rgba(90, 24, 18, 220);
                border: 2px solid #d6a85f;
                border-radius: 8px;
                font-size: 26px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(145, 38, 25, 240);
            }
        """

class SkillSelectPage(ImagePage):
    back_home = Signal()
    skills_confirmed = Signal(list)

    def __init__(self):
        super().__init__("skill_select_bg.png")

        self.max_select_count = 6
        self.selected_skill_ids = DEFAULT_BASIC_SKILL_IDS.copy()
        self.current_detail_skill_id = self.selected_skill_ids[0]
        self.skill_buttons = {}
        self.skill_image_labels = {}

        self.create_skill_buttons()
        self.create_detail_panel()
        self.create_action_buttons()
        self.refresh_skill_buttons()
        self.show_skill_detail(self.current_detail_skill_id)

    def create_skill_buttons(self):
        # 15 个技能槽位的点击区域。
        # 这一版按你提供的“通用技能选择”背景图重新对齐，
        # 让透明按钮尽量落在每个金色方框的内部可点击区域。
        # 如果你后面还想自己微调，只需要改下面这些 (x, y, w, h) 坐标即可。
        slot_geometries = [
            (117, 294, 152, 179),
            (303, 294, 152, 179),
            (491, 294, 152, 179),
            (678, 294, 152, 179),
            (866, 294, 152, 179),
            (117, 508, 152, 179),
            (303, 508, 152, 179),
            (491, 508, 152, 179),
            (678, 508, 152, 179),
            (866, 508, 152, 179),
            (117, 723, 152, 179),
            (303, 723, 152, 179),
            (491, 723, 152, 179),
            (678, 723, 152, 179),
            (866, 723, 152, 179),
        ]

        for skill, geometry in zip(GENERIC_SKILL_CONFIGS, slot_geometries):
            # 图片标签放在按钮下层，按钮本身保持透明/半透明，
            # 这样既能看到技能图，也不影响点击区域。
            image_label = self.create_skill_image_label(skill["id"], geometry)
            self.skill_image_labels[skill["id"]] = image_label

            btn = QPushButton(self)
            btn.setGeometry(*geometry)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, s=skill: self.on_skill_clicked(s["id"]))
            self.skill_buttons[skill["id"]] = btn

    def get_skill_image_path(self, skill_id):
        return Path(__file__).resolve().parent / "assets" / "images" / "skills" / f"{skill_id}.png"

    def has_skill_image(self, skill_id):
        return self.get_skill_image_path(skill_id).exists()

    def create_skill_image_label(self, skill_id, geometry):
        x, y, w, h = geometry

        label = QLabel(self)
        # 技能图尽量铺满金色小方框，不再给按钮文字预留底部空间。
        label.setGeometry(x + 4, y + 5, w - 8, h - 10)
        label.setAlignment(Qt.AlignCenter)
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        pixmap = QPixmap(str(self.get_skill_image_path(skill_id)))
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaled(
                    label.width(),
                    label.height(),
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        else:
            label.hide()

        return label

    def set_detail_image(self, skill_id):
        if not hasattr(self, "detail_image"):
            return

        pixmap = QPixmap(str(self.get_skill_image_path(skill_id)))
        if pixmap.isNull():
            self.detail_image.clear()
            self.detail_image.hide()
            self.detail_text.setGeometry(1188, 285, 272, 445)
            return

        self.detail_image.show()
        self.detail_image.setPixmap(
            pixmap.scaled(
                self.detail_image.width(),
                self.detail_image.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
        self.detail_text.setGeometry(1188, 450, 272, 280)

    def create_detail_panel(self):
        self.detail_title = QLabel(self)
        self.detail_title.setGeometry(1190, 210, 270, 48)
        self.detail_title.setAlignment(Qt.AlignCenter)
        self.detail_title.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.detail_image = QLabel(self)
        self.detail_image.setGeometry(1216, 285, 216, 154)
        self.detail_image.setAlignment(Qt.AlignCenter)
        self.detail_image.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.detail_image.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        self.detail_text = QLabel(self)
        self.detail_text.setGeometry(1188, 450, 272, 280)
        self.detail_text.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detail_text.setWordWrap(True)
        self.detail_text.setStyleSheet("""
            QLabel {
                color: #f5e6c8;
                font-size: 18px;
                font-weight: bold;
                line-height: 150%;
                background: transparent;
            }
        """)

        self.detail_hint = QLabel(self)
        self.detail_hint.setGeometry(1188, 730, 272, 40)
        self.detail_hint.setAlignment(Qt.AlignCenter)
        self.detail_hint.setStyleSheet("""
            QLabel {
                color: #d6a85f;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)

    def create_action_buttons(self):
        # 右下角两个透明按钮覆盖在背景图自带按钮上。
        # 这一版重新按你给的背景图位置下移并微调，让实际点击区域更贴合视觉位置。
        # setGeometry(x, y, w, h) 分别是：左上角 x、左上角 y、宽度、高度。
        self.confirm_button = QPushButton("", self)
        self.confirm_button.setGeometry(1179, 784, 274, 60)
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.confirm_skills)
        self.confirm_button.setStyleSheet(self.transparent_action_button_style())

        self.back_button = QPushButton("", self)
        self.back_button.setGeometry(1179, 860, 272, 52)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_home.emit)
        self.back_button.setStyleSheet(self.transparent_action_button_style())

    def set_selected_skills(self, skill_ids):
        valid_ids = {skill["id"] for skill in GENERIC_SKILL_CONFIGS}
        self.selected_skill_ids = [skill_id for skill_id in skill_ids if skill_id in valid_ids]
        if not self.selected_skill_ids:
            self.selected_skill_ids = DEFAULT_BASIC_SKILL_IDS.copy()
        self.current_detail_skill_id = self.selected_skill_ids[0]
        self.refresh_skill_buttons()
        self.show_skill_detail(self.current_detail_skill_id)

    def on_skill_clicked(self, skill_id):
        self.current_detail_skill_id = skill_id
        skill = get_generic_skill_config(skill_id)

        if skill["implemented"]:
            if skill_id in self.selected_skill_ids:
                self.selected_skill_ids.remove(skill_id)
            elif len(self.selected_skill_ids) < self.max_select_count:
                self.selected_skill_ids.append(skill_id)
            else:
                self.detail_hint.setText("最多选择 6 个通用技能")
                self.show_skill_detail(skill_id, keep_hint=True)
                return

        self.refresh_skill_buttons()
        self.show_skill_detail(skill_id)

    def show_skill_detail(self, skill_id, keep_hint=False):
        skill = get_generic_skill_config(skill_id)
        detail = get_skill_detail_info(skill_id)
        selected_text = "已选择" if skill_id in self.selected_skill_ids else "未选择"
        status_text = "已接入战斗逻辑" if skill["implemented"] else "预留接口，暂未接入战斗逻辑"

        self.detail_title.setText(skill["name"])
        self.set_detail_image(skill_id)
        self.detail_text.setText(
            f"\u7c7b\u578b\uff1a{skill['type']}\n\n"
            f"CD\uff1a{detail['cooldown']} \u56de\u5408\n"
            f"\u80fd\u8017\uff1a{detail['energy_cost']} \u70b9\n\n"
            f"\u72b6\u6001\uff1a{status_text}\n\n"
            f"\u4ecb\u7ecd\uff1a\n{detail['description']}\n\n"
            f"\u9009\u62e9\u72b6\u6001\uff1a{selected_text}"
        )

        if not keep_hint:
            if skill["implemented"]:
                self.detail_hint.setText(f"已选择 {len(self.selected_skill_ids)} / {self.max_select_count}")
            else:
                self.detail_hint.setText("这里已留好后续实现接口")

    def refresh_skill_buttons(self):
        for skill in GENERIC_SKILL_CONFIGS:
            skill_id = skill["id"]
            btn = self.skill_buttons[skill_id]
            selected = skill_id in self.selected_skill_ids
            has_image = self.has_skill_image(skill_id)

            if skill_id in self.skill_image_labels:
                self.skill_image_labels[skill_id].setVisible(has_image)

            btn.setText(self.skill_button_text(skill, selected))
            btn.setStyleSheet(self.skill_button_style(selected, skill["implemented"], has_image))

    def skill_button_text(self, skill, selected):
        mark = "✓" if selected else ""
        status = "" if skill["implemented"] else "待接入"

        if self.has_skill_image(skill["id"]):
            # 有技能图时不再叠加说明文字，让图片尽量完整显示。
            return mark

        return f"{mark}{skill['name']}\n{skill['type']}\n{status}"

    def confirm_skills(self):
        if len(self.selected_skill_ids) != self.max_select_count:
            self.detail_hint.setText(f"需要选择 {self.max_select_count} 个通用技能")
            return

        # 只把已经在 skill_factory 中注册的技能传入战斗页，避免未实现技能导致报错。
        selected = [
            skill_id for skill_id in self.selected_skill_ids
            if get_generic_skill_config(skill_id)["implemented"]
        ]
        self.skills_confirmed.emit(selected)

    def skill_button_style(self, selected=False, implemented=True, has_image=False):
        border_color = "#f0d28c" if selected else "rgba(214, 168, 95, 70)"
        if selected:
            background_color = "rgba(130, 30, 20, 45)" if has_image else "rgba(130, 30, 20, 80)"
        else:
            background_alpha = 2 if has_image else 18
            background_color = f"rgba(0, 0, 0, {background_alpha})"

        text_color = "#ffffff" if implemented else "#9d8a67"
        font_size = 22 if has_image else 18
        padding_top = 0

        return f"""
            QPushButton {{
                color: {text_color};
                background-color: {background_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                font-size: {font_size}px;
                font-weight: bold;
                text-align: center;
                padding-top: {padding_top}px;
                padding-left: 4px;
                padding-right: 4px;
                padding-bottom: 4px;
            }}

            QPushButton:hover {{
                color: #ffffff;
                background-color: rgba(120, 30, 20, 40);
                border: 2px solid #d6a85f;
            }}
        """

    def transparent_action_button_style(self):
        return """
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                border: none;
            }

            QPushButton:hover {
                background-color: rgba(214, 168, 95, 35);
                border: 1px solid rgba(240, 210, 140, 160);
                border-radius: 6px;
            }
        """


class HeroSelectPage(ImagePage):
    back_home = Signal()
    hero_confirmed = Signal(str)

    def __init__(self):
        super().__init__("hero_select_bg.png")

        self.selected_hero_id = "fire_mage"
        self.hero_buttons = {}
        self.hero_image_labels = {}

        self.create_hero_buttons()
        self.create_detail_panel()
        self.create_action_buttons()
        self.select_hero(self.selected_hero_id)

    def create_hero_buttons(self):
        slot_geometries = [
            (148, 304, 170, 236),
            (320, 304, 170, 236),
            (492, 304, 170, 236),
            (664, 304, 170, 236),
            (835, 304, 170, 236),
            (999, 304, 170, 236),
            (148, 574, 170, 236),
            (320, 574, 170, 236),
            (492, 574, 170, 236),
            (664, 574, 170, 236),
            (835, 574, 170, 236),
            (999, 574, 170, 236),
        ]

        for hero, geometry in zip(HERO_CONFIGS, slot_geometries):
            image_label = self.create_hero_image_label(hero["id"], geometry)
            self.hero_image_labels[hero["id"]] = image_label

            btn = QPushButton(self)
            btn.setGeometry(*geometry)
            btn.setText(self.hero_button_text(hero))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, h=hero: self.select_hero(h["id"]))
            self.hero_buttons[hero["id"]] = btn

    def get_hero_image_path(self, hero_id):
        return Path(__file__).resolve().parent / "assets" / "images" / "heroes" / f"{hero_id}.png"

    def has_hero_image(self, hero_id):
        return self.get_hero_image_path(hero_id).exists()

    def create_hero_image_label(self, hero_id, geometry):
        x, y, w, h = geometry

        label = QLabel(self)
        # 角色图片尽量填满左侧小方框，同时保留少量边距避免贴边。
        label.setGeometry(x + 5, y + 6, w - 10, h - 12)
        label.setAlignment(Qt.AlignCenter)
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        pixmap = QPixmap(str(self.get_hero_image_path(hero_id)))
        if not pixmap.isNull():
            label.setPixmap(
                pixmap.scaled(
                    label.width(),
                    label.height(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
            )
        else:
            label.hide()

        return label

    def create_detail_panel(self):
        self.detail_title = QLabel(self)
        self.detail_title.setGeometry(1220, 214, 260, 46)
        self.detail_title.setAlignment(Qt.AlignCenter)
        self.detail_title.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.detail_image = QLabel(self)
        self.detail_image.setGeometry(1228, 270, 244, 154)
        self.detail_image.setAlignment(Qt.AlignCenter)
        self.detail_image.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.detail_image.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
            }
        """)

        self.detail_text = QTextEdit(self)
        self.detail_text.setGeometry(1218, 438, 266, 292)
        self.detail_text.setReadOnly(True)
        self.detail_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.detail_text.setStyleSheet("""
            QTextEdit {
                color: #f5e6c8;
                font-size: 15px;
                font-weight: bold;
                line-height: 125%;
                background-color: rgba(0, 0, 0, 0);
                border: none;
                padding: 0px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: rgba(0, 0, 0, 0);
            }
            QScrollBar::handle:vertical {
                background: rgba(214, 168, 95, 120);
                border-radius: 4px;
            }
        """)

        self.detail_hint = QLabel(self)
        self.detail_hint.setGeometry(1218, 740, 266, 36)
        self.detail_hint.setAlignment(Qt.AlignCenter)
        self.detail_hint.setStyleSheet("""
            QLabel {
                color: #d6a85f;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
            }
        """)

    def create_action_buttons(self):
        # 这两个透明按钮覆盖在背景图右侧的按钮图片上。
        # 由于背景图会被拉伸到 1536x1024，这里使用的是窗口坐标，
        # 如果以后替换背景图或改窗口大小，只需要微调下面两个 setGeometry。
        self.confirm_button = QPushButton("", self)
        self.confirm_button.setGeometry(1228, 765, 242, 58)
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self.confirm_hero)
        self.confirm_button.setStyleSheet(self.transparent_action_button_style())

        self.back_button = QPushButton("", self)
        self.back_button.setGeometry(1228, 828, 242, 52)
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.clicked.connect(self.back_home.emit)
        self.back_button.setStyleSheet(self.transparent_action_button_style())

    def set_selected_hero(self, hero_id):
        self.select_hero(hero_id)

    def set_detail_image(self, hero_id):
        pixmap = QPixmap(str(self.get_hero_image_path(hero_id)))
        if pixmap.isNull():
            self.detail_image.clear()
            self.detail_image.hide()
            self.detail_text.setGeometry(1218, 292, 266, 441)
            return

        self.detail_image.show()
        self.detail_image.setPixmap(
            pixmap.scaled(
                self.detail_image.width(),
                self.detail_image.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )
        self.detail_text.setGeometry(1218, 438, 266, 292)

    def select_hero(self, hero_id):
        hero = get_hero_config(hero_id)
        self.selected_hero_id = hero["id"]

        for button_id, btn in self.hero_buttons.items():
            btn.setStyleSheet(
                self.hero_button_style(
                    button_id == self.selected_hero_id,
                    self.has_hero_image(button_id)
                )
            )

        self.detail_title.setText(hero["name"])
        self.set_detail_image(hero_id)
        self.detail_text.setText(get_hero_detail_text(hero))
        self.detail_hint.setText("可选择" if hero["implemented"] else "暂未接入战斗逻辑")
        self.confirm_button.setEnabled(hero["implemented"])

    def confirm_hero(self):
        hero = get_hero_config(self.selected_hero_id)
        if not hero["implemented"]:
            return
        self.hero_confirmed.emit(self.selected_hero_id)

    def hero_button_text(self, hero):
        if self.has_hero_image(hero["id"]):
            return ""
        return f"{hero['name']}\n{hero['role']}"

    def hero_button_style(self, selected=False, has_image=False):
        border_color = "#f0d28c" if selected else "rgba(214, 168, 95, 70)"
        if selected:
            background_color = "rgba(130, 30, 20, 45)" if has_image else "rgba(130, 30, 20, 95)"
        else:
            background_alpha = 2 if has_image else 18
            background_color = f"rgba(0, 0, 0, {background_alpha})"

        hover_background = "rgba(120, 30, 20, 40)" if has_image else "rgba(120, 30, 20, 85)"
        text_color = "#ffffff" if selected else "#f0d28c"
        font_size = 18
        padding_top = 0 if has_image else 150

        return f"""
            QPushButton {{
                color: {text_color};
                background-color: {background_color};
                border: 2px solid {border_color};
                border-radius: 8px;
                font-size: {font_size}px;
                font-weight: bold;
                text-align: center;
                padding-top: {padding_top}px;
                padding-left: 6px;
                padding-right: 6px;
                padding-bottom: 6px;
            }}

            QPushButton:hover {{
                color: #ffffff;
                background-color: {hover_background};
                border: 2px solid #d6a85f;
            }}
        """

    def transparent_action_button_style(self):
        return """
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                border: none;
            }

            QPushButton:hover {
                background-color: rgba(214, 168, 95, 35);
                border: 1px solid rgba(240, 210, 140, 160);
                border-radius: 6px;
            }

            QPushButton:disabled {
                background-color: rgba(0, 0, 0, 80);
                border: 1px solid rgba(110, 90, 60, 120);
                border-radius: 6px;
            }
        """


class AISelectPage(ImagePage):
    back_home = Signal()
    ai_selected = Signal(str)

    def __init__(self):
        super().__init__("home_bg.png")

        self.title = QLabel("选择 AI 难度", self)
        self.title.setGeometry(468, 100, 600, 80)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 50px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.panel = QLabel(
            "AI 难度选择\n\n"
            "简单：藤蔓法师，随机性强，适合练习\n"
            "普通：火焰法师，会判断距离、血量和技能状态\n"
            "困难：殉爆骨将，本地搜索平均收益最优动作",
            self
        )
        self.panel.setGeometry(330, 215, 876, 260)
        self.panel.setAlignment(Qt.AlignCenter)
        self.panel.setWordWrap(True)
        self.panel.setStyleSheet("""
            QLabel {
                color: #f5e6c8;
                background-color: rgba(10, 8, 6, 185);
                border: 2px solid #d6a85f;
                border-radius: 12px;
                font-size: 26px;
                font-weight: bold;
                line-height: 1.5;
            }
        """)

        self.buttons = []
        button_defs = [
            ("easy", "简单 AI\n藤蔓法师"),
            ("normal", "普通 AI\n火焰法师"),
            ("hard", "困难 AI\n殉爆骨将"),
        ]
        for i, (difficulty, text) in enumerate(button_defs):
            btn = QPushButton(text, self)
            btn.setGeometry(330 + i * 292, 540, 250, 105)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self.ai_button_style())
            btn.clicked.connect(lambda checked=False, d=difficulty: self.ai_selected.emit(d))
            self.buttons.append(btn)

        self.hint = QLabel("选择后会返回主页；进入战斗时按所选难度创建敌方 AI。", self)
        self.hint.setGeometry(368, 675, 800, 40)
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setStyleSheet("""
            QLabel {
                color: #d6a85f;
                background: transparent;
                font-size: 20px;
                font-weight: bold;
            }
        """)

        self.back_button = QPushButton("返回主页", self)
        self.back_button.setGeometry(658, 760, 220, 60)
        self.back_button.setStyleSheet("""
            QPushButton {
                color: #f5e6c8;
                background-color: rgba(90, 24, 18, 220);
                border: 2px solid #d6a85f;
                border-radius: 8px;
                font-size: 26px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(145, 38, 25, 240);
            }
        """)
        self.back_button.clicked.connect(self.back_home.emit)

    def ai_button_style(self):
        return """
            QPushButton {
                color: #f5e6c8;
                background-color: rgba(42, 32, 22, 220);
                border: 2px solid #d6a85f;
                border-radius: 12px;
                font-size: 25px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(125, 75, 32, 235);
                border: 2px solid #f0d28c;
            }

            QPushButton:pressed {
                background-color: rgba(90, 24, 18, 240);
            }
        """

class ResultPage(ImagePage):
    back_home = Signal()
    restart_battle = Signal()

    def __init__(self):
        super().__init__(None)

        self.result_image = QLabel(self)
        self.result_image.setGeometry(0, 0, 1536, 1024)
        self.result_image.setScaledContents(True)
        self.result_image.setStyleSheet("""
            QLabel {
                background-color: black;
                border: none;
            }
        """)

        self.opacity_effect = QGraphicsOpacityEffect(self.result_image)
        self.result_image.setGraphicsEffect(self.opacity_effect)

        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_anim.setDuration(700)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.restart_button = QPushButton("再来一局", self)
        self.restart_button.setGeometry(480, 900, 220, 64)
        self.restart_button.setCursor(Qt.PointingHandCursor)
        self.restart_button.setStyleSheet(self.result_button_style())
        self.restart_button.clicked.connect(self.restart_battle.emit)

        self.home_button = QPushButton("返回主页", self)
        self.home_button.setGeometry(836, 900, 220, 64)
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.setStyleSheet(self.result_button_style())
        self.home_button.clicked.connect(self.back_home.emit)

        self.restart_button.raise_()
        self.home_button.raise_()

    def set_result(self, result_data):
        if isinstance(result_data, str):
            result = result_data
            winner_id = None
        else:
            result = result_data.get("result")
            winner_id = result_data.get("winner_id")

        base_dir = Path(__file__).resolve().parent
        result_dir = base_dir / "assets" / "images" / "results"

        if result == "draw":
            image_name = DRAW_RESULT_IMAGE
        else:
            image_name = RESULT_IMAGE_FILES.get(winner_id)

        if image_name is None:
            image_name = RESULT_IMAGE_FILES.get("fire_mage")

        image_path = result_dir / image_name
        pixmap = QPixmap(str(image_path))

        if pixmap.isNull():
            print("结算图片加载失败：", image_path)
            self.result_image.clear()
            self.result_image.setStyleSheet("background-color: black;")
            return

        self.result_image.setPixmap(
            pixmap.scaled(
                self.result_image.width(),
                self.result_image.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
        )

        self.opacity_effect.setOpacity(0.0)
        self.fade_anim.stop()
        self.fade_anim.start()

    def result_button_style(self):
        return """
            QPushButton {
                color: #f5e6c8;
                background-color: rgba(90, 24, 18, 220);
                border: 2px solid #d6a85f;
                border-radius: 8px;
                font-size: 26px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(145, 38, 25, 240);
                border: 2px solid #f0d28c;
            }

            QPushButton:pressed {
                background-color: rgba(60, 18, 12, 240);
            }
        """

class BattleCanvas(QWidget):
    cell_clicked = Signal(int, int)

    def __init__(self):
        super().__init__()

        self.setFixedSize(1536, 1024)

        base_dir = Path(__file__).resolve().parent
        self.bg = QPixmap(str(base_dir / "assets" / "images" / "battle_bg.png"))

        self.rows = 3
        self.cols = 10

        self.grid_x = 220
        self.grid_y = 242
        self.grid_w = 970
        self.grid_h = 374

        self.selected_cell = None
        self.state = None

        self.character_pixmap_cache = {}
        self.character_image_dir = Path(__file__).resolve().parent / "assets" / "images" / "characters"

        self.character_sprite_files = {
            "火焰法师": "fire_mage/fire_mage.png",
            "空间法师": "space_mage/space_mage.png",
            "大地法师": "earth_mage/earth_mage.png",
            "藤蔓法师": "vine_mage/vine_mage.png",
            "战争领主": "war_lord/war_lord.png",
            "铁链角斗士": "chain_gladiator/chain_gladiator.png",
            "幽影刺客": "shadow_assassin/shadow_assassin.png",
            "血誓狂战": "blood_berserker/blood_berserker.png",
            "狂翼鸟人": "birdman/birdman.png",
            "幻鳞蜥客": "lizard_rogue/lizard_rogue.png",
            "殉爆骨将": "bone_general/bone_general.png",
            "乱魂巫医": "witch_doctor/witch_doctor.png",
        }

    def set_state(self, state):
        self.state = state
        self.update()

    def cell_rect(self, row, col):
        cell_w = self.grid_w / self.cols
        cell_h = self.grid_h / self.rows

        x = self.grid_x + col * cell_w
        y = self.grid_y + row * cell_h

        return QRect(int(x), int(y), int(cell_w), int(cell_h))

    def cell_center(self, row, col):
        rect = self.cell_rect(row, col)
        return rect.center().x(), rect.center().y()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.bg.isNull():
            painter.drawPixmap(self.rect(), self.bg)
        else:
            painter.fillRect(self.rect(), QColor("#1f1a17"))

        self.draw_selected_cell(painter)

        if self.state is None:
            return

        self.draw_character_sprite(painter, self.state.player)
        self.draw_character_sprite(painter, self.state.enemy)

    def draw_selected_cell(self, painter):
        if self.selected_cell is None:
            return

        row, col = self.selected_cell
        rect = self.cell_rect(row, col)

        painter.setPen(QPen(QColor(255, 215, 0), 3))
        painter.setBrush(QBrush(QColor(255, 215, 0, 60)))

        skill = getattr(self.state, "selected_skill", None) if self.state is not None else None
        if getattr(skill, "skill_id", None) in ("chaos_backfire", "life_drain"):
            if self.state is not None and self.state.in_bounds(row + 1, col + 1):
                bottom_right = self.cell_rect(row + 1, col + 1)
                area_rect = QRect(rect.topLeft(), bottom_right.bottomRight())
                painter.drawRect(area_rect)
            else:
                painter.drawRect(rect)
        else:
            painter.drawRect(rect)

    def draw_character_sprite(self, painter, character):
        if character is None:
            return

        row, col = character.pos
        cell = self.cell_rect(row, col)
        cx = cell.center().x()
        cy = cell.center().y()

        pixmap = self.get_character_pixmap(character)

        if pixmap.isNull():
            self.draw_character_placeholder(painter, character, cx, cy)
            return

        painter.save()

        # 保持图片比例，但人物不要占满整个格子
        sprite_scale = 0.78

        sprite_h = int(cell.height() * sprite_scale)
        sprite_w = int(sprite_h * pixmap.width() / pixmap.height())

        target_rect = QRect(
            int(cx - sprite_w / 2),
            int(cell.bottom() - sprite_h - 6),
            sprite_w,
            sprite_h
        )

        # 脚下阴影
        shadow_w = int(cell.width() * 0.65)
        shadow_h = max(8, int(cell.height() * 0.10))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 120)))
        painter.drawEllipse(
            int(cx - shadow_w / 2),
            int(cell.bottom() - shadow_h),
            shadow_w,
            shadow_h
        )

        # 统一规定：所有角色原图都是向右看
        # 玩家1在左边：不翻转
        # 玩家2/敌人在右边：自动翻转成向左看
        if self.state is not None and character is self.state.enemy:
            pixmap = pixmap.transformed(QTransform().scale(-1, 1), Qt.SmoothTransformation)

        painter.drawPixmap(target_rect, pixmap)
        painter.restore()

    def get_character_pixmap(self, character):
        character_name = getattr(character, "name", "")

        filename = self.character_sprite_files.get(character_name)

        if filename is not None:
            sprite_path = self.character_image_dir / filename
        else:
            if not hasattr(character, "get_sprite_path"):
                return QPixmap()

            sprite_path = character.get_sprite_path()

            if sprite_path is None:
                return QPixmap()

        sprite_path = str(sprite_path)

        if sprite_path not in self.character_pixmap_cache:
            pixmap = QPixmap(sprite_path)

            if pixmap.isNull():
                print("角色图片加载失败：", sprite_path)

            self.character_pixmap_cache[sprite_path] = pixmap

        return self.character_pixmap_cache[sprite_path]

    def draw_character_placeholder(self, painter, character, cx, cy):
        if self.state is not None and character is self.state.player:
            color = QColor("#3c8dff")
        else:
            color = QColor("#ff4b42")

        painter.setPen(QPen(color, 3))
        painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 80)))
        painter.drawEllipse(cx - 18, cy - 18, 36, 36)

    def mousePressEvent(self, event):
        x = event.position().x()
        y = event.position().y()

        for r in range(self.rows):
            for c in range(self.cols):
                if self.cell_rect(r, c).contains(int(x), int(y)):
                    self.selected_cell = (r, c)
                    self.cell_clicked.emit(r, c)
                    self.update()
                    return


class BattlePage(QWidget):
    battle_finished = Signal(dict)

    def __init__(self, player_character_id="blood_berserker", enemy_character_id=None, basic_skill_ids=None, ai_difficulty="normal"):
        super().__init__()

        self.setFixedSize(1536, 1024)

        self.ai_difficulty = ai_difficulty if ai_difficulty in AI_CONFIGS else "normal"
        self.ai_config = get_ai_config(self.ai_difficulty)

        if enemy_character_id is None:
            enemy_character_id = self.ai_config["character_id"]

        self.player_character_id = player_character_id
        self.enemy_character_id = enemy_character_id

        if basic_skill_ids is None:
            basic_skill_ids = DEFAULT_BASIC_SKILL_IDS.copy()
        else:
            basic_skill_ids = list(basic_skill_ids)

        enemy_basic_skill_ids = list(self.ai_config["basic_skill_ids"])

        self.player = create_character(
            character_id=player_character_id,
            pos=(1, 1),
            basic_skill_ids=basic_skill_ids
        )

        self.enemy = create_character(
            character_id=enemy_character_id,
            pos=(1, 8),
            basic_skill_ids=enemy_basic_skill_ids
        )

        self.player_skills = create_skills(self.player.all_skill_ids())
        self.enemy_skills = create_skills(self.enemy.all_skill_ids())

        self.state = BattleState(
            rows=3,
            cols=10,
            player=self.player,
            enemy=self.enemy,
            characters=[self.player, self.enemy],
            all_skills={
                self.player: self.player_skills,
                self.enemy: self.enemy_skills,
            }
        )

        self.actor_human = self.player
        self.actor_ai = self.enemy
        self.skills_human = self.player_skills
        self.skills_ai = self.enemy_skills
        self.ai_controller = BattleAIController(self.ai_difficulty)

        self.selected_skill = None
        self.selected_cell = None
        self.skill_buttons = []
        self.game_over = False

        # ── 可信对局初始化 ──
        self.crypto = GameCryptoEngine()
        self.crypto_rounds = []       # [{cipher, plain}]
        self._pending_ai_choice = None  # 下一回合 AI 预出招
        self._current_commitment_round = None

        self.canvas = BattleCanvas()
        self.canvas.setParent(self)
        self.canvas.move(0, 0)
        self.canvas.set_state(self.state)

        self.canvas.cell_clicked.connect(self.on_cell_clicked)

        self.init_overlay_ui()
        self.refresh_info()

    def init_overlay_ui(self):
        self.phase_label = QLabel("战斗阶段", self.canvas)
        self.phase_label.setGeometry(470, 25, 600, 70)
        self.phase_label.setAlignment(Qt.AlignCenter)
        self.phase_label.setStyleSheet("""
            QLabel {
                color: #f0d28c;
                font-size: 34px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.status_label = QLabel(self.canvas)
        self.status_label.setGeometry(463, 725, 610, 40)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #f5e6c8;
                font-size: 20px;
                font-weight: bold;
                background: rgba(0, 0, 0, 60);
                border: 1px solid #d6a85f;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        self.status_label.setText("选择技能与目标，然后点击「确认行动」")

        self.info_label = QLabel(self.canvas)
        self.info_label.setGeometry(50, 250, 130, 520)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #f5e6c8;
                font-size: 15px;
                font-weight: bold;
                background: transparent;
            }
        """)

        self.create_skill_buttons()

        self.confirm_button = QPushButton("确认行动", self.canvas)
        self.confirm_button.setGeometry(1260, 790, 226, 72)
        self.confirm_button.clicked.connect(self.confirm_action)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                color: #f5e6c8;
                background-color: rgba(120, 30, 20, 220);
                border: 2px solid #d6a85f;
                border-radius: 8px;
                font-size: 26px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: rgba(160, 45, 30, 240);
            }

            QPushButton:pressed {
                background-color: rgba(80, 20, 15, 240);
            }

            QPushButton:disabled {
                color: #7f6f55;
                background-color: rgba(60, 40, 30, 160);
                border: 2px solid #5f4a2e;
            }
        """)

        self.log_box = QTextEdit(self.canvas)
        self.log_box.setGeometry(463, 770, 610, 180)
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("""
            QTextEdit {
                color: #f5e6c8;
                background-color: rgba(0, 0, 0, 35);
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        self.log_box.append("战斗开始。")
        # 可信对局：生成密钥并公开承诺
        self._crypto_pub_key, self._crypto_enc_aes = self.crypto.start_new_game()
        self.log_box.append("RSA 公钥:")
        for line in self._crypto_pub_key.strip().split("\n"):
            self.log_box.append(f"  {line}")
        self.log_box.append(f"RSA 加密的 AES 密钥: {self._crypto_enc_aes}")
        # 安装日志点击事件
        self.log_box.viewport().installEventFilter(self)
        # AI 预出招（第一回合）
        self._ai_commit_next_round()
        self.set_status("选择技能与目标，然后点击「确认行动」")

    def set_status(self, text):
        self.status_label.setText(text)

    def get_skill_image_path(self, skill):
        if skill is None:
            return None

        skill_id = getattr(skill, "skill_id", None)

        if skill_id is None:
            return None

        if hasattr(self.player, "get_skill_image_path"):
            image_path = self.player.get_skill_image_path(skill_id)
            if image_path is not None and Path(image_path).exists():
                return image_path

        base_dir = Path(__file__).resolve().parent
        common_path = base_dir / "assets" / "images" / "skills" / f"{skill_id}.png"

        if common_path.exists():
            return common_path

        return None

    def create_skill_buttons(self):
        slot_geometries = [
            (1262, 244, 90, 104),
            (1368, 244, 90, 104),

            (1262, 370, 90, 104),
            (1368, 370, 90, 104),

            (1262, 494, 90, 104),
            (1368, 494, 90, 104),

            (1262, 616, 90, 104),
            (1368, 616, 90, 104),
        ]

        self.skill_buttons.clear()

        for i in range(8):
            skill = self.player_skills[i] if i < len(self.player_skills) else None

            image_path = self.get_skill_image_path(skill)
            btn = SkillButton(skill, self.canvas, image_path=image_path)

            x, y, w, h = slot_geometries[i]
            btn.setGeometry(x, y, w, h)

            if skill is not None:
                btn.clicked.connect(lambda checked=False, s=skill: self.select_skill(s))
            else:
                btn.setEnabled(False)

            self.skill_buttons.append(btn)

    def select_skill(self, skill):
        if self.game_over:
            return

        if self._is_actor_forced_random(self.actor_human):
            self.set_confirm_status()
            return

        if not skill.can_use(self.player):
            if skill.current_cd > 0:
                self.set_status(f"{skill.name} 还在冷却中，剩余 {skill.current_cd} 回合")
            else:
                cost = getattr(skill, "energy_cost", 0)
                self.set_status(f"{skill.name} 能量不足，需要 {cost} 点能量")
            return

        self.selected_skill = skill
        self.state.selected_skill = skill

        for btn in self.skill_buttons:
            btn.set_selected(btn.skill == skill)

        self.set_confirm_status()

        self.refresh_info()

    def on_cell_clicked(self, row, col):
        if self.game_over:
            return

        self.selected_cell = (row, col)
        self.state.selected_cell = (row, col)

        self.set_confirm_status()
        self.refresh_info()

    def set_confirm_status(self):
        if self._is_actor_forced_random(self.actor_human):
            turns = self.actor_human.special_state.get("chaos_random_turns", 0)
            self.set_status(f"你处于乱魂随机移动状态，剩余 {turns} 回合。点击确认行动后将随机移动。")
        elif self.selected_skill is None:
            self.set_status("请先选择技能")
        else:
            base = f"{self.selected_skill.name}:{self.selected_skill.description}"
            if self.selected_skill.target_required and self.selected_cell is not None:
                target_str = f"({self.selected_cell[0]},{self.selected_cell[1]})"
                if getattr(self.selected_skill, "skill_id", None) in ("chaos_backfire", "life_drain"):
                    self.set_status(f"{base} 已选择左上角 {target_str}，实际区域为该格向右下扩展的 2×2。")
                else:
                    self.set_status(f"{base} {target_str}")
            else:
                self.set_status(base)

    def confirm_action(self):
        if self.game_over:
            return

        if self._is_actor_forced_random(self.actor_human):
            choice_a = (self.actor_human, None, "__chaos_random__")
            choice_b = self._pending_ai_choice
            result = self._resolve_round(choice_a, choice_b)
            if not result.get("round_resolved", True):
                self._handle_round_not_resolved(result)
                return
            self.log_box.append(f"{self.actor_human.name} {self._choice_to_text(choice_a)}")
            self._pending_ai_choice = None
            self._reveal_current_round()
            self.clear_selection()
            self.refresh_info()
            self.canvas.update()
            self.check_game_over()
            if not self.game_over:
                self._ai_commit_next_round()
            return

        if self.selected_skill is None:
            self.set_status("请先选择技能")
            return

        if self.selected_skill.target_required and self.selected_cell is None:
            self.set_status("请先选择目标格")
            return

        # 距离预检：选中技能范围 ≠ 被选格距离 → 提前拦截
        skill = self.selected_skill
        if skill.range is not None and self.selected_cell is not None:
            if self.state.distance(self.player.pos, self.selected_cell) > skill.range:
                self.set_status(f"{skill.name} 距离不能超过 {skill.range} 格")
                return

        # 能量预检：不够时不进入引擎，也不揭晓 AI 承诺
        energy_cost = getattr(skill, "energy_cost", 0)
        if getattr(self.actor_human, "energy", 0) < energy_cost:
            self.set_status(f"{skill.name} \u80fd\u91cf\u4e0d\u8db3\uff0c\u9700\u8981 {energy_cost} \u70b9\u80fd\u91cf\uff0c\u8bf7\u91cd\u65b0\u9009\u62e9\u6280\u80fd\u3002")
            return

        # 使用 AI 预出招（已在回合开始时承诺）
        choice_a = (self.actor_human, self.selected_skill, self.selected_cell)
        choice_b = self._pending_ai_choice

        result = self._resolve_round(choice_a, choice_b)
        if not result.get("round_resolved", True):
            self._handle_round_not_resolved(result)
            return
            # 玩家释放失败：保留当前 AI 承诺，不揭晓、不清空选择、不进入下一回合。
            self.set_status("技能释放失败，请重新选择目标格或更换技能。")
            self.refresh_info()
            self.canvas.update()
            return

        # 玩家行动成功后再显示明文，避免错误操作污染对局记录。
        self.log_box.append(f"{self.actor_human.name} {self._choice_to_text(choice_a)}")
        self._pending_ai_choice = None

        # 揭晓 AI 行动
        self._reveal_current_round()

        self.clear_selection()
        self.refresh_info()
        self.canvas.update()
        self.check_game_over()
        # 下一回合 AI 预出招
        if not self.game_over:
            self._ai_commit_next_round()

    # ── 可信对局 ──

    def _handle_round_not_resolved(self, result):
        if result.get("failure_reason") == "energy":
            actor = result.get("failed_actor")
            failed_skill = result.get("failed_skill")
            actor_name = getattr(actor, "name", "\u89d2\u8272")
            skill_name = getattr(failed_skill, "name", "\u6280\u80fd")
            required = result.get("required_energy", 0)
            if actor is self.actor_ai:
                self._ai_recommit_current_round()
                self.set_status(f"{actor_name} \u80fd\u91cf\u4e0d\u8db3\uff0c\u5df2\u91cd\u65b0\u9009\u62e9\u672c\u8f6e\u884c\u52a8\u3002\u8bf7\u518d\u6b21\u786e\u8ba4\u884c\u52a8\u3002")
            else:
                self.set_status(f"{actor_name} \u80fd\u91cf\u4e0d\u8db3\uff0c\u65e0\u6cd5\u4f7f\u7528 {skill_name}\uff0c\u9700\u8981 {required} \u70b9\u80fd\u91cf\u3002\u8bf7\u91cd\u65b0\u9009\u62e9\u6280\u80fd\u3002")
        else:
            self.set_status("\u6280\u80fd\u91ca\u653e\u5931\u8d25\uff0c\u8bf7\u5931\u8d25\u65b9\u91cd\u65b0\u9009\u62e9\uff0c\u672c\u56de\u5408\u672a\u63a8\u8fdb\u3002")
        self.refresh_info()
        self.canvas.update()

    def _choice_to_text(self, choice):
        """将 (actor, skill, target) 简化为文本，不包含角色名（角色名由行首提供）"""
        actor, skill, target = choice
        if actor is None:
            return "不行动"
        if target == "__chaos_random__":
            return "乱魂随机移动"
        if skill is None:
            return "不行动"
        target_str = f"({target[0]},{target[1]})" if target else "无目标"
        return f"{skill.name} @ {target_str}"

    def _ai_commitment_text(self, choice):
        """加密承诺中的明文。

        AI 在回合开始立即调用该函数并加密，所以这里记录的玩家位置
        就是上一回合结束后的玩家位置，不可能包含玩家本回合的新行动。
        """
        config = get_ai_config(self.ai_difficulty)
        extra = ""
        if self.ai_difficulty == "hard":
            reason = self.actor_ai.special_state.get("_hard_ai_last_reason")
            score = self.actor_ai.special_state.get("_hard_ai_last_score")
            candidates = self.actor_ai.special_state.get("_hard_ai_candidates")
            depth = self.actor_ai.special_state.get("_hard_ai_depth")
            if reason is not None:
                extra = f" | 搜索深度={depth} | 搜索平均收益={score} | 候选动作={candidates} | 原因={reason}"
        return (
            f"[{config['name']} | 观测玩家位置={self.actor_human.pos} | "
            f"AI位置={self.actor_ai.pos} | AI能量={self.actor_ai.energy}{extra}] "
            f"{self._choice_to_text(choice)}"
        )

    def _ai_commit_next_round(self):
        """回合开始时 AI 预出招并加密承诺"""
        if self.game_over:
            return
        choice = self._ai_decide()
        self._pending_ai_choice = choice
        plain_text = self._ai_commitment_text(choice)
        cipher_text = self.crypto.commit_action(plain_text)
        actor_name = self.actor_ai.name
        round_n = len(self.crypto_rounds)
        self.crypto_rounds.append({
            "cipher": cipher_text,
            "plain": plain_text,
            "actor_name": actor_name,
            "revealed": False,
        })
        self._current_commitment_round = round_n
        # 追加一行，用 userState 存储回合号
        self.log_box.append(f"{actor_name} {cipher_text}")
        self.log_box.document().lastBlock().setUserState(round_n)

    def _ai_recommit_current_round(self):
        if self.game_over:
            return
        choice = self._ai_decide()
        self._pending_ai_choice = choice
        plain_text = self._ai_commitment_text(choice)
        cipher_text = self.crypto.commit_action(plain_text)
        actor_name = self.actor_ai.name

        if self._current_commitment_round is None:
            round_n = len(self.crypto_rounds)
            self.crypto_rounds.append({
                "cipher": cipher_text,
                "plain": plain_text,
                "actor_name": actor_name,
                "revealed": False,
            })
            self._current_commitment_round = round_n
            self.log_box.append(f"{actor_name} {cipher_text}")
            self.log_box.document().lastBlock().setUserState(round_n)
            return

        rd = self.crypto_rounds[self._current_commitment_round]
        rd["cipher"] = cipher_text
        rd["plain"] = plain_text
        rd["actor_name"] = actor_name
        rd["revealed"] = False

        block = self._find_block_by_state(self._current_commitment_round)
        if block is None:
            self.log_box.append(f"{actor_name} {cipher_text}")
            self.log_box.document().lastBlock().setUserState(self._current_commitment_round)
            return

        from PySide6.QtGui import QTextCursor
        cur = QTextCursor(block)
        cur.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                         QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        cur.insertText(f"{actor_name} {cipher_text}")

    def _reveal_current_round(self):
        """结算后立即将密文自动切换为明文"""
        if self._current_commitment_round is None:
            return
        rd = self.crypto_rounds[self._current_commitment_round]
        rd["revealed"] = True
        # 找到该回合的 block 并替换为明文
        block = self._find_block_by_state(self._current_commitment_round)
        if block is None:
            return
        from PySide6.QtGui import QTextCursor
        cur = QTextCursor(block)
        cur.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                         QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        cur.insertText(f"{rd['actor_name']} {rd['plain']}")

    def _find_block_by_state(self, state):
        """遍历文档，找到 userState 等于 state 的 block"""
        block = self.log_box.document().begin()
        while block.isValid():
            if block.userState() == state:
                return block
            block = block.next()
        return None

    def _toggle_commitment_line(self, block):
        """点击切换密文/明文"""
        round_n = block.userState()
        if round_n < 0 or round_n >= len(self.crypto_rounds):
            return
        rd = self.crypto_rounds[round_n]
        if not rd["revealed"]:
            return  # 未揭晓，不切换

        from PySide6.QtGui import QTextCursor
        text = block.text()
        if rd["cipher"] in text:
            new = f"{rd['actor_name']} {rd['plain']}"
        else:
            new = f"{rd['actor_name']} {rd['cipher']}"

        cur = QTextCursor(block)
        cur.movePosition(QTextCursor.MoveOperation.EndOfBlock,
                         QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        cur.insertText(new)

    def eventFilter(self, obj, event):
        """捕获日志点击，切换密文/明文"""
        if obj == self.log_box.viewport() and event.type() == QEvent.MouseButtonRelease:
            from PySide6.QtGui import QTextCursor
            cursor = self.log_box.cursorForPosition(event.position().toPoint())
            block = cursor.block()
            if block.userState() >= 0:
                self._toggle_commitment_line(block)
                return True
        return super().eventFilter(obj, event)

    def _reveal_private_key(self):
        """游戏结束：公布 RSA 私钥"""
        priv_key = self.crypto.reveal_private_key()
        self.log_box.append("")
        self.log_box.append("══════════ 可信对局 · 验证明文 ══════════")
        self.log_box.append("")
        self.log_box.append("RSA 公钥:")
        for line in self._crypto_pub_key.strip().split("\n"):
            self.log_box.append(f"  {line}")
        self.log_box.append("")
        self.log_box.append(f"RSA 加密的 AES 密钥: {self._crypto_enc_aes}")
        self.log_box.append("")
        self.log_box.append("RSA 私钥 (用于解密验证):")
        for line in priv_key.strip().split("\n"):
            self.log_box.append(f"  {line}")
        self.log_box.append("")
        self.log_box.append("对局记录:")
        for i, rd in enumerate(self.crypto_rounds):
            self.log_box.append(f"  第{i+1}回合 | 密文: {rd['cipher']}")
            self.log_box.append(f"           | 明文: {rd['plain']}")
        self.log_box.append("")
        self.log_box.append("验证方法：用 RSA 私钥解密 AES 密钥 → "
                            "用 AES 密钥 + 密文中的 Nonce 解密各回合密文 → 与明文对比")
        self.log_box.append("═══════════════════════════════════════════")

    def clear_selection(self):
        self.selected_skill = None
        self.selected_cell = None

        self.state.selected_skill = None
        self.state.selected_cell = None

        self.canvas.selected_cell = None

        for btn in self.skill_buttons:
            btn.set_selected(False)

        if self._is_actor_forced_random(self.actor_human):
            self.set_confirm_status()
        else:
            self.set_status("选择技能与目标，然后点击「确认行动」")

    def _is_actor_forced_random(self, actor):
        return int(getattr(actor, "special_state", {}).get("chaos_random_turns", 0) or 0) > 0

    def _ai_decide(self):
        # 该函数只在 _ai_commit_next_round/_ai_recommit_current_round 中调用；
        # 调用时玩家尚未进行本回合操作，因此 AI 只能看到上一回合结束后的玩家位置。
        return self.ai_controller.choose(
            state=self.state,
            ai=self.actor_ai,
            opponent=self.actor_human,
            skills=self.skills_ai,
        )

    def _resolve_round(self, choice_a, choice_b):
        state = self.state
        result = state.resolve(choice_a, choice_b, self.log_box.append, abort_if_first_fails=True)
        if result.get("round_resolved", True):
            self._reduce_all_cooldowns()
        return result

    def _tick_turn_end(self):
        state = self.state
        for char, skills in state.all_skills.items():
            for skill in skills:
                skill.on_turn_end(state, char, self.log_box.append)

    def _reduce_all_cooldowns(self):
        for skills in self.state.all_skills.values():
            for skill in skills:
                skill.reduce_cooldown()
        for btn in self.skill_buttons:
            if btn.skill is not None:
                btn.setEnabled(btn.skill.can_use())
                btn.update()

    def _ai_move(self, actor):
        opp = self.actor_human
        s = actor.status
        move_range = 1
        if s.get("shield_wall"):
            move_range = 0
        if s.get("weaken_move"):
            move_range -= 1
        if move_range <= 0:
            return

        ai_row, ai_col = actor.pos
        opp_row, opp_col = opp.pos

        new_row, new_col = ai_row, ai_col
        if opp_col > ai_col:
            new_col += 1
        elif opp_col < ai_col:
            new_col -= 1
        elif opp_row > ai_row:
            new_row += 1
        elif opp_row < ai_row:
            new_row -= 1

        new_row, new_col = self.state.clamp_pos(new_row, new_col)
        if (new_row, new_col) != opp.pos:
            self.state.push_move(actor, (new_row, new_col))
            self.log_box.append(f"{actor.name} 移动到 ({new_row}, {new_col})。")
        else:
            self.log_box.append(f"{actor.name} 想移动，但目标格被占用。")

    def refresh_info(self):
        player = self.state.player
        enemy = self.state.enemy

        skill_name = self.selected_skill.name if self.selected_skill else "无"

        player_random = int(player.special_state.get("chaos_random_turns", 0) or 0)
        enemy_random = int(enemy.special_state.get("chaos_random_turns", 0) or 0)
        player_status = f"\n乱魂随机：{player_random} 回合" if player_random > 0 else ""
        enemy_status = f"\n乱魂随机：{enemy_random} 回合" if enemy_random > 0 else ""

        self.info_label.setText(
            f"【玩家】\n"
            f"{player.name}\n"
            f"HP：{player.hp}/{player.max_hp}\n"
            f"能量：{player.energy}/{player.max_energy}\n"
            f"位置：{player.pos}{player_status}\n\n"
            f"【敌方】\n"
            f"{enemy.name}\n"
            f"HP：{enemy.hp}/{enemy.max_hp}\n"
            f"能量：{enemy.energy}/{enemy.max_energy}\n"
            f"位置：{enemy.pos}{enemy_status}\n\n"
            f"当前技能：{skill_name}\n"
            f"目标格子：{self.selected_cell}"
        )

        forced = self._is_actor_forced_random(self.actor_human)
        for btn in self.skill_buttons:
            if btn.skill is not None:
                btn.setEnabled((not forced) and btn.skill.current_cd <= 0)
            btn.update()
        if forced and self.selected_skill is None:
            self.set_confirm_status()

    def check_game_over(self):
        if self.game_over:
            return

        player_dead = self.state.player.hp <= 0
        enemy_dead = self.state.enemy.hp <= 0

        if self.state.draw:
            self.game_over = True
            self.phase_label.setText("战斗平局")
            self.set_status("双方同时倒下 —— 平局！")
            self.log_box.append("战斗结束：双方同时倒下，平局！")
            self.disable_all_actions()
            self.battle_finished.emit({
                "result": "draw",
                "winner_id": None
            })
        elif player_dead and enemy_dead:
            self.game_over = True
            self.phase_label.setText("战斗平局")
            self.set_status("双方同时倒下 —— 平局！")
            self.log_box.append("战斗结束：双方同时倒下，平局！")
            self.disable_all_actions()
            self.battle_finished.emit({
                "result": "draw",
                "winner_id": None
            })

        elif enemy_dead:
            self.phase_label.setText("战斗胜利")
            self.set_status(f"胜利！{self.state.player.name} 击杀了 {self.state.enemy.name}")
            self.log_box.append(f"战斗结束：{self.state.player.name} 胜利！")
            self.disable_all_actions()
            self.battle_finished.emit({
                "result": "win",
                "winner_id": self.player_character_id
            })

        elif player_dead:
            self.phase_label.setText("战斗失败")
            self.set_status(f"失败！{self.state.player.name} 被 {self.state.enemy.name} 击杀")
            self.log_box.append(f"战斗结束：{self.state.enemy.name} 胜利！")
            self.disable_all_actions()
            self.battle_finished.emit({
                "result": "lose",
                "winner_id": self.enemy_character_id
            })

        # 可信对局：亮出私钥
        if self.game_over:
            self._reveal_private_key()

    def disable_all_actions(self):
        self.game_over = True
        self.confirm_button.setEnabled(False)

        for btn in self.skill_buttons:
            btn.setEnabled(False)



class ScaledGameView(QGraphicsView):
    """Scale the fixed 1536×1024 game UI to any window size.

    The actual pages keep their original coordinates.  The view scales the
    whole widget tree with KeepAspectRatio, so resizing the window never
    stretches the image, never covers UI elements, and uses black letterboxing
    when the window ratio differs from 3:2.
    """

    BASE_W = 1536
    BASE_H = 1024

    def __init__(self, content_widget, parent=None):
        super().__init__(parent)
        self._content_widget = content_widget
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setAlignment(Qt.AlignCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(0, 0, 0)))
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setFrameShape(QFrame.NoFrame)

        self._content_widget.setFixedSize(self.BASE_W, self.BASE_H)
        self._proxy = self._scene.addWidget(self._content_widget)
        self._scene.setSceneRect(0, 0, self.BASE_W, self.BASE_H)
        self._fit_content()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_content()

    def showEvent(self, event):
        super().showEvent(event)
        self._fit_content()

    def _fit_content(self):
        self.fitInView(self._scene.sceneRect(), Qt.KeepAspectRatio)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("暗夜竞技场")
        self.resize(1536, 1024)
        self.setMinimumSize(900, 600)

        self.stack = QStackedWidget()
        self.stack.setFixedSize(1536, 1024)
        self.scaled_view = ScaledGameView(self.stack)
        self.setCentralWidget(self.scaled_view)

        self.selected_character_id = "fire_mage"
        self.selected_basic_skill_ids = DEFAULT_BASIC_SKILL_IDS.copy()
        self.selected_ai_difficulty = "normal"

        self.current_username = None
        self.auth_service = AuthService()
        self.login_page = LoginPage(self.auth_service)
        self.home_page = HomePage()
        self.skill_page = SkillSelectPage()
        self.hero_page = HeroSelectPage()
        self.ai_page = AISelectPage()
        self.result_page = ResultPage()

        self.home_page.set_current_hero(get_hero_config(self.selected_character_id))
        self.home_page.set_current_skills(self.selected_basic_skill_ids)
        self.home_page.set_current_ai(self.selected_ai_difficulty)

        self.battle_page = None

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.skill_page)
        self.stack.addWidget(self.hero_page)
        self.stack.addWidget(self.ai_page)
        self.stack.addWidget(self.result_page)

        self.bind_signals()
        self.show_login()

    def bind_signals(self):
        self.login_page.login_success.connect(self.show_home)

        self.home_page.enter_battle.connect(self.start_battle)
        self.home_page.enter_card_select.connect(self.show_card_select)
        self.home_page.enter_hero_select.connect(self.show_hero_select)
        self.home_page.enter_ai_select.connect(self.show_ai_select)
        self.home_page.exit_game.connect(self.close)

        self.skill_page.back_home.connect(self.show_home)
        self.skill_page.skills_confirmed.connect(self.set_player_skills)
        self.hero_page.back_home.connect(self.show_home)
        self.hero_page.hero_confirmed.connect(self.set_player_character)
        self.ai_page.back_home.connect(self.show_home)
        self.ai_page.ai_selected.connect(self.set_ai_difficulty)

        self.result_page.back_home.connect(self.show_home)
        self.result_page.restart_battle.connect(self.start_battle)

    def show_login(self):
        self.stack.setCurrentWidget(self.login_page)

    def show_home(self, username=""):
        if username:
            self.current_username = username
            stats = self.auth_service.get_user_stats(username)
            avatar = self.auth_service.get_user_avatar(username)
            self.home_page.set_player_info(username, avatar)
            self.home_page.set_player_stats(stats)
            lineup = self.auth_service.get_last_lineup(username)
            if lineup["hero"] is not None:
                self.selected_character_id = lineup["hero"]
            if lineup["skills"] is not None:
                self.selected_basic_skill_ids = lineup["skills"]
            self.home_page.set_current_hero(get_hero_config(self.selected_character_id))
            self.home_page.set_current_skills(self.selected_basic_skill_ids)
        self.home_page.set_current_ai(self.selected_ai_difficulty)
        self.stack.setCurrentWidget(self.home_page)

    def show_card_select(self):
        self.skill_page.set_selected_skills(self.selected_basic_skill_ids)
        self.stack.setCurrentWidget(self.skill_page)

    def show_hero_select(self):
        self.hero_page.set_selected_hero(self.selected_character_id)
        self.stack.setCurrentWidget(self.hero_page)

    def show_ai_select(self):
        self.stack.setCurrentWidget(self.ai_page)

    def save_current_lineup(self):
        if self.current_username:
            self.auth_service.save_last_lineup(
                self.current_username,
                self.selected_character_id,
                self.selected_basic_skill_ids,
            )

    def set_player_character(self, character_id):
        self.selected_character_id = character_id
        self.save_current_lineup()
        self.home_page.set_current_hero(get_hero_config(character_id))
        self.show_home()

    def set_player_skills(self, skill_ids):
        self.selected_basic_skill_ids = list(skill_ids)
        self.save_current_lineup()
        self.home_page.set_current_skills(self.selected_basic_skill_ids)
        self.show_home()

    def set_ai_difficulty(self, difficulty):
        self.selected_ai_difficulty = difficulty if difficulty in AI_CONFIGS else "normal"
        self.home_page.set_current_ai(self.selected_ai_difficulty)
        self.show_home()

    def start_battle(self):
        if self.battle_page is not None:
            self.stack.removeWidget(self.battle_page)
            self.battle_page.deleteLater()
            self.battle_page = None

        self.battle_page = BattlePage(
            player_character_id=self.selected_character_id,
            basic_skill_ids=self.selected_basic_skill_ids,
            ai_difficulty=self.selected_ai_difficulty,
        )
        self.battle_page.battle_finished.connect(self.show_result)

        self.stack.addWidget(self.battle_page)
        self.stack.setCurrentWidget(self.battle_page)

    def show_result(self, result):
        if self.current_username:
            won = result.get("result") == "win"
            self.auth_service.add_game_result(self.current_username, won)
            stats = self.auth_service.get_user_stats(self.current_username)
            self.home_page.set_player_stats(stats)
        self.result_page.set_result(result)
        self.stack.setCurrentWidget(self.result_page)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
