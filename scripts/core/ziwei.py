# -*- coding: utf-8 -*-
"""紫微斗数排盘引擎（口径对照 权威在线排盘参考站点）。

口径（2026-09-12 经 权威排盘实测锁定：12 组黄金案例 + 五局×30 日全表）：
1. 以"农历（真太阳时）"为准：年干支按正月初一换年（春节口径，非立春），
   四化以该年干起；月份取农历月；日取农历日；时支取真太阳时之十二时辰。
   真太阳时 >= 23:00 视为晚子时：日柱换入次一日（农历日 +1），时辰按子时。
2. 命宫支  = (2 + 农历月 - 时辰序) % 12   （寅=2 起，顺数生月、逆数生时；
   时辰序 子=1 … 亥=12）。
3. 命宫干  = 寅月干(年干五虎遁) + ((命宫支 - 寅) % 12)，再 % 10。
4. 五行局  = 命宫干支纳音五行：金四局 / 木三局 / 水二局 / 火六局 / 土五局。
5. 紫微宫  = (BASE[局][(农历日-1) % 局] + (农历日-1) // 局) % 12，
   其中 BASE 序列为 [酉午亥辰丑寅] 的尾部切片（对应 火六/土五/金四/木三/水二
   初一之宫）：水二 BASE=[丑寅]、木三=[辰丑寅]、金四=[亥辰丑寅]、
   土五=[午亥辰丑寅]、火六=[酉午亥辰丑寅]。
   实测：五局 30 日全表 149 点与 权威排盘逐一吻合。
6. 身宫支  = (农历月 + 时辰序) % 12（顺数生月再顺数生时）。
7. 命主按命宫支查表；身主按生年支查表。
8. 主星相对布局为固定骨架：紫微系（天机-1/太阳-3/武曲-4/天同-5/廉贞-8，逆）；
   天府与紫微成 (4-紫微) 镜像；天府系（太阴+1/贪狼+2/巨门+3/天相+4/天梁+5/
   七杀+6/破军+10，顺）。

用法：
  ZiweiEngine(lunar, solar_dt=None)
  lunar: Lunar 对象（农历基准）；solar_dt 可给真太阳时 datetime 以处理晚子时。
"""
from datetime import timedelta

from lunar_python import Solar
from lunar_python.util import LunarUtil

from .utils import TIANGAN, DIZHI

# 十二宫名（自命宫起，逆时针）
PALACE_NAMES = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
                "迁移", "交友", "官禄", "田宅", "福德", "父母"]

# 五行局名
JU_NAMES = {2: "水二局", 3: "木三局", 4: "金四局", 5: "土五局", 6: "火六局"}
# 纳音五行 -> 局数
_NAYIN_TO_JU = {"金": 4, "木": 3, "水": 2, "火": 6, "土": 5}

# 紫微定位基准序列（火六局初一组 = 酉午亥辰丑寅），各局取其尾部 j 个
_ZIWEI_BASE = [9, 6, 11, 4, 1, 2]

# 命主表（以命宫支）
MINGZHU = {"子": "贪狼", "丑": "巨门", "寅": "禄存", "卯": "文曲",
           "辰": "廉贞", "巳": "武曲", "午": "破军", "未": "武曲",
           "申": "廉贞", "酉": "文曲", "戌": "禄存", "亥": "巨门"}
# 身主表（以年支）
SHENZHU = {"子": "火星", "丑": "天相", "寅": "天梁", "卯": "天同",
           "辰": "文昌", "巳": "天机", "午": "火星", "未": "天相",
           "申": "天梁", "酉": "天同", "戌": "文昌", "亥": "天机"}

# 年干四化（禄 权 科 忌）
SIHUA = {
    "甲": ["廉贞", "破军", "武曲", "太阳"],
    "乙": ["天机", "天梁", "紫微", "太阴"],
    "丙": ["天同", "天机", "文昌", "廉贞"],
    "丁": ["太阴", "天同", "天机", "巨门"],
    "戊": ["贪狼", "太阴", "右弼", "天机"],
    "己": ["武曲", "贪狼", "天梁", "文曲"],
    "庚": ["太阳", "武曲", "太阴", "天同"],
    "辛": ["巨门", "太阳", "文曲", "文昌"],
    "壬": ["天梁", "紫微", "左辅", "武曲"],
    "癸": ["破军", "巨门", "太阴", "贪狼"],
}


def _wuhu_start(year_gan):
    """年干五虎遁 -> 寅月天干序号（甲己丙寅…戊癸甲寅）。"""
    return (TIANGAN.index(year_gan) % 5) * 2 + 2


def _nayin_ju(gan_zhi):
    """命宫干支纳音 -> 五行局数。"""
    n = LunarUtil.NAYIN.get(gan_zhi, "")
    for el, ju in _NAYIN_TO_JU.items():
        if el in n:
            return ju
    return 2


def _ziwei_idx(ju, day):
    """五行局与农历日 -> 紫微星所在宫支序（子=0）。"""
    base = _ZIWEI_BASE[-ju:]
    return (base[(day - 1) % ju] + (day - 1) // ju) % 12


class ZiweiEngine:
    """紫微斗数排盘引擎（命宫/身宫/五行局/十四主星/四化）。"""

    def __init__(self, lunar, solar_dt=None):
        # 晚子时（真太阳时 >= 23:00）换日，时支取子时
        if solar_dt is not None and solar_dt.hour >= 23:
            base = solar_dt + timedelta(days=1)
            solar = Solar.fromYmdHms(base.year, base.month, base.day, 0, 30, 0)
            self.lunar = solar.getLunar()
        else:
            self.lunar = lunar
        self.month = abs(self.lunar.getMonth())
        self.day = self.lunar.getDay()
        self.hour_idx = self.lunar.getTimeZhiIndex() + 1  # 子=1
        self.year_gan = self.lunar.getYearGan()
        self.year_zhi = self.lunar.getYearZhi()

        # 命宫 / 身宫 / 五行局
        self.minggong_idx = (2 + self.month - self.hour_idx) % 12
        self.shengong_idx = (self.month + self.hour_idx) % 12
        ming_gan = TIANGAN[(_wuhu_start(self.year_gan) + (self.minggong_idx - 2) % 12) % 10]
        self.minggong_gz = ming_gan + DIZHI[self.minggong_idx]
        self.ju = _nayin_ju(self.minggong_gz)

        # 紫微定位与十四主星
        self.ziwei_idx = _ziwei_idx(self.ju, self.day)
        self.star_pos = self._place_stars()

    # ---------- 主星安布 ----------
    def _place_stars(self):
        z = self.ziwei_idx
        stars = {
            "紫微": DIZHI[z],
            "天机": DIZHI[(z - 1) % 12],
            "太阳": DIZHI[(z - 3) % 12],
            "武曲": DIZHI[(z - 4) % 12],
            "天同": DIZHI[(z - 5) % 12],
            "廉贞": DIZHI[(z - 8) % 12],
        }
        t = (4 - z) % 12  # 天府（与紫微镜像）
        stars["天府"] = DIZHI[t]
        for name, off in (("太阴", 1), ("贪狼", 2), ("巨门", 3), ("天相", 4),
                          ("天梁", 5), ("七杀", 6), ("破军", 10)):
            stars[name] = DIZHI[(t + off) % 12]
        return stars

    # ---------- 宫位 ----------
    def get_palace_branches(self):
        """宫名 -> 宫支（自命宫逆时针布十二宫）。"""
        out = {}
        for i, name in enumerate(PALACE_NAMES):
            out[name] = DIZHI[(self.minggong_idx - i) % 12]
        return out

    def get_palace_ganzhi(self):
        """宫支 -> 宫干支（由命宫干支起，逆时针递减一干一支? 用五虎遁顺推）。"""
        # 各宫天干：自寅月干支按宫位顺推（与命宫干算法一致）
        gz = {}
        for name, zhi in self.get_palace_branches().items():
            zi = DIZHI.index(zhi)
            gan = TIANGAN[(_wuhu_start(self.year_gan) + (zi - 2) % 12) % 10]
            gz[zhi] = gan + zhi
        return gz

    def si_hua(self):
        """本命四化：[{star, hua}]。"""
        names = SIHUA.get(self.year_gan, ["", "", "", ""])
        return [{"star": s, "hua": h} for s, h in zip(names, ["禄", "权", "科", "忌"])]

    # ---------- 分析 ----------
    def analyze(self):
        ju_name = JU_NAMES[self.ju]
        palaces = self.get_palace_branches()
        mingzhu = MINGZHU[DIZHI[self.minggong_idx]]
        shenzhu = SHENZHU[self.year_zhi]

        branch_stars = {b: [] for b in DIZHI}
        for s, b in self.star_pos.items():
            branch_stars[b].append(s)

        summary = ("命宫在{mg}（{mgz}），身宫在{sg}，{ju}。命主：{mz}，身主：{sz}。"
                   "紫微在{zw}。四化：{sh}。").format(
            mg=DIZHI[self.minggong_idx], mgz=self.minggong_gz,
            sg=DIZHI[self.shengong_idx], ju=ju_name, mz=mingzhu, sz=shenzhu,
            zw=self.star_pos["紫微"],
            sh=" ".join(x["star"] + x["hua"] for x in self.si_hua()))

        pz_map = self.get_palace_ganzhi()
        lines = ["紫微命盘 [{}{}]".format(self.year_gan + self.year_zhi, ju_name)]
        lines.append("命宫: {} ({})  身宫: {}  命主: {}  身主: {}".format(
            DIZHI[self.minggong_idx], self.minggong_gz,
            DIZHI[self.shengong_idx], mingzhu, shenzhu))
        lines.append("农历: {}年{}月{}日  四化: {}".format(
            self.year_gan + self.year_zhi, self.month, self.day,
            " ".join(x["star"] + x["hua"] for x in self.si_hua())))
        lines.append("-" * 46)
        lines.append("十四主星分布：")
        for b in DIZHI:
            ss = [x for x in self.star_pos if self.star_pos[x] == b]
            if ss:
                lines.append("  {}宫({})：{}".format(
                    palaces.get(b, b), pz_map.get(b, ""), "、".join(sorted(ss, key=lambda x: list(self.star_pos).index(x)))))
        render = "\n".join(lines)

        return {
            "summary": summary,
            "render": render,
            "lunar": self.lunar.toString(),
            "minggong": DIZHI[self.minggong_idx],
            "minggong_gz": self.minggong_gz,
            "shengong": DIZHI[self.shengong_idx],
            "ju": ju_name,
            "ju_num": self.ju,
            "mingzhu": mingzhu,
            "shenzhu": shenzhu,
            "stars": self.star_pos,
            "palaces": palaces,
            "palace_ganzhi": self.get_palace_ganzhi(),
            "sihua": self.si_hua(),
        }
