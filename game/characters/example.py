from pathlib import Path

from characters.character import Character


BASE_DIR = Path(__file__).resolve().parent.parent


class NewHero(Character):
    def __init__(self, pos, basic_skill_ids):
        super().__init__(
            # =================================================
            # 角色基础信息
            # =================================================
            name="示例角色",

            # =================================================
            # 五个基础属性
            # =================================================
            max_hp=100,
            defense=0,
            attack=10,
            max_energy=100,
            move_power=1,

            # =================================================
            # 初始位置
            # =================================================
            pos=pos,

            # =================================================
            # 技能列表
            # 前两个是角色专属技能
            # 后六个通用技能由外部传入
            # =================================================
            exclusive_skill_ids=[
                "new_hero_skill_1",
                "new_hero_skill_2",
            ],
            basic_skill_ids=basic_skill_ids,

            # =================================================
            # 战斗界面人物立绘
            # =================================================
            sprite_path=(
                BASE_DIR
                / "assets"
                / "images"
                / "characters"
                / "new_hero.png"
            ),
            sprite_size=(130, 170),
        )

        # =====================================================
        # 角色独有状态
        # 没有特殊状态时可以删除
        # =====================================================
        self.special_state = None

    def get_skill_image_path(self, skill_id):
        """
        返回专属技能图片路径。

        只需要登记本角色的两个专属技能。
        通用技能图片由 main.py 自动读取。
        """
        image_map = {
            "new_hero_skill_1": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "new_hero" / "new_hero_skill_1.png"
            ),
            "new_hero_skill_2": (
                BASE_DIR / "assets" / "images" / "characters_skills" / "new_hero" / "new_hero_skill_2.png"
            ),
        }

        return image_map.get(skill_id)

    def on_round_end(self, state, log):
        """
        每轮结束时自动调用。

        普通角色没有额外效果时，可以直接删除这个方法。
        """
        if self.special_state is None:
            return

        # 在这里编写角色独有的跨回合效果。
        # 示例：
        #
        # enemy = state.get_enemy_of(self)
        # state.push_damage(
        #     target=enemy,
        #     amount=5,
        #     source=self,
        # )
        #
        # log(f"{self.name} 的特殊效果触发。")