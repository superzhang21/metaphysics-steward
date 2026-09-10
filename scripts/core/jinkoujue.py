# -*- coding: utf-8 -*-
"""金口诀排盘引擎（口径对照 权威在线排盘参考站点）。

关键口径（2026-09-12 经 权威在线排盘实测收敛：12 日辰 x 12 地分 +
多时辰断面共 100+ 图全量校验，见 references/jinkoujue_权威排盘_calibration.md）：
1. 全部以民用时间（东八区钟表时间）起课———金口诀表单无经纬度字段。
2. 晚子换日：钟表时刻 >= 23:00 日干支顺延一日（实测 2026-09-12 23:30 →
   次日起庚寅日子时），占时=子时。
3. 月将按「节」换将（与八字/六壬的「中气换将」不同——金口诀换将于节）：
   小寒→子、立春→亥、惊蛰→戌、清明→酉、立夏→申、芒种→未、小暑→午、
   立秋→巳、白露→辰、寒露→卯、立冬→寅、大雪→丑。
   实测：1990-02-04 立春 10:14 前仍子将、其后已亥将。
4. 地分：占问方位/任意支（CLI 默认子）。
5. 人元：以日干五鼠遁（甲己起甲子、乙庚丙子、丙辛戊子、丁壬庚子、戊癸壬子），
   于「地分支」位上取遁干。
6. 将神：以月将加占时，天盘支 = (地分 + 月将 - 占时) mod 12；将神支=天盘支，
   神名=十二将（神后/大吉/功曹/太冲/天罡/太乙/胜光/小吉/传送/从魁/河魁/登明），
   天干=五鼠遁(将神支)。
7. 贵神：日干贵神（昼夜贵同六壬；卯~申时=昼），贵支 g0；顺布若 g0 ∈
   {亥,子,丑,寅,卯} 否则逆布；贵神名 = 布圈上地分位之神（贵蛇雀合勾龙空虎常玄阴后），
   贵神支 = 固定「贵神座支」表（贵丑/蛇巳/雀午/合卯/勾辰/龙寅/空戌/虎申/常未/
   玄子/阴酉/后亥），天干=五鼠遁(贵神支)。
8. 日空=日柱旬空；四大空亡：甲子/甲午旬=水、甲寅/甲申旬=金、甲辰/甲戌旬=无。
9. 旺相休囚死/用爻/神煞（月德/驿马/天马…）为站点修饰性标注，其基准算法经
   100+ 图反推仍与标准月将基准部分不合（站点含私有规则），本引擎不输出。

用法：
  JinkoujueEngine.from_civil(dt, difen="午").analyze()
"""
from datetime import datetime, timedelta

from lunar_python import Solar

from .calendar import get_lunar

TIANGAN = list("甲乙丙丁戊己庚辛壬癸")
DIZHI = list("子丑寅卯辰巳午未申酉戌亥")
GAN_ELEM = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
            "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
ZHI_ELEM = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
            "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
# 昼夜贵（昼, 夜）——同大六壬
GUI = {"甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
       "乙": ("子", "申"), "己": ("子", "申"),
       "丙": ("亥", "酉"), "丁": ("亥", "酉"),
       "壬": ("巳", "卯"), "癸": ("巳", "卯"),
       "辛": ("午", "寅")}
# 节 -> 月将（金口诀按节换将，非中气）
JIE_JIANG = [("小寒", "子"), ("立春", "亥"), ("惊蛰", "戌"), ("清明", "酉"),
             ("立夏", "申"), ("芒种", "未"), ("小暑", "午"), ("立秋", "巳"),
             ("白露", "辰"), ("寒露", "卯"), ("立冬", "寅"), ("大雪", "丑")]
# 五鼠遁起干：日干 -> 子时天干 index
WUSHU = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4,
         "丁": 6, "壬": 6, "戊": 8, "癸": 8}
# 十二将名（按支序）
JIANG = ["神后", "大吉", "功曹", "太冲", "天罡", "太乙",
         "胜光", "小吉", "传送", "从魁", "河魁", "登明"]
# 贵神序列（贵蛇雀合勾龙空虎常玄阴后）
GODS = ["贵人", "腾蛇", "朱雀", "六合", "勾陈", "青龙", "天空",
        "白虎", "太常", "玄武", "太阴", "天后"]
# 贵神座支（固定表，实测恒定不随时辰变化）：贵丑蛇巳雀午合卯勾辰龙寅空戌虎申常未玄子阴酉后亥
GUI_ZHI_FIX = [1, 5, 6, 3, 4, 2, 10, 8, 7, 0, 9, 11]


def _hour_zhi_idx(h):
    if h >= 23 or h < 1:
        return 0
    return int((h + 1) // 2) % 12


def _dun(day_gan, zhi_idx):
    return TIANGAN[(WUSHU[day_gan] + zhi_idx) % 10]


def _xun(day_gan, day_zhi):
    """返回 (旬首支idx, [空亡两支idx])。"""
    head = (DIZHI.index(day_zhi) - TIANGAN.index(day_gan)) % 12
    return head, [(head + 10) % 12, (head + 11) % 12]


class JinkoujueEngine:
    """金口诀引擎。

    构造：JinkoujueEngine(lunar, civil_dt=None, difen='子')
    推荐：JinkoujueEngine.from_civil(datetime, difen=...) —— 民用时间直接起课。
    """

    def __init__(self, lunar, civil_dt=None, difen="子"):
        self.lunar = lunar
        self.civil_dt = civil_dt
        self.difen = difen
        if civil_dt is not None:
            h = civil_dt.hour + civil_dt.minute / 60.0
            self.roll = h >= 23
            base = datetime(civil_dt.year, civil_dt.month, civil_dt.day)
            if self.roll:
                base = base + timedelta(days=1)
            lday = Solar.fromYmdHms(base.year, base.month, base.day, 12, 0, 0).getLunar()
            self.day_gan = lday.getDayGan()
            self.day_zhi = lday.getDayZhi()
            self.hour_zhi_idx = _hour_zhi_idx(h)
            ec = self.lunar.getEightChar()
            self.year_gz = ec.getYear()
            self.month_gz = ec.getMonth()
        else:
            self.roll = False
            self.day_gan = lunar.getDayGan()
            self.day_zhi = lunar.getDayZhi()
            self.hour_zhi_idx = DIZHI.index(lunar.getTimeZhi())
            self.year_gz = lunar.getYearInGanZhi()
            self.month_gz = lunar.getMonthInGanZhi()
        self.hour_zhi = DIZHI[self.hour_zhi_idx]
        self.hour_gan = _dun(self.day_gan, self.hour_zhi_idx)
        self.yue_jiang = self._yue_jiang()
        self.df_idx = DIZHI.index(self.difen)
        head, kong = _xun(self.day_gan, self.day_zhi)
        self.kong = [DIZHI[x] for x in kong]
        # 四大空亡：甲子/甲午旬(首支子午)->水，甲寅/甲申旬(首支寅申)->金，甲辰/甲戌旬(首支辰戌)->无
        self.bigkong = {0: "水", 6: "水", 2: "金", 8: "金", 4: "无", 10: "无"}[head % 12]
        # 占时昼/夜（卯~申=昼）
        self.day = self.hour_zhi_idx in (3, 4, 5, 6, 7, 8)
        self.gui_zhi = GUI[self.day_gan][0] if self.day else GUI[self.day_gan][1]

    @classmethod
    def from_civil(cls, dt, difen="子"):
        return cls(get_lunar(dt), civil_dt=dt, difen=difen)

    # ---------- 基础 ----------
    def _yue_jiang(self):
        qi = self.lunar.getPrevJie()
        name = qi.getName() if hasattr(qi, "getName") else qi
        for jn, jiang in JIE_JIANG:
            if jn == name:
                return jiang
        raise ValueError(f"未知节: {name}")

    def _renyuan(self):
        """人元：五鼠遁(日干) 于地分支。"""
        return _dun(self.day_gan, self.df_idx)

    def _jiangshen(self):
        """将神：月将加时天盘支 at 地分。"""
        yj = DIZHI.index(self.yue_jiang)
        js_zhi = (self.df_idx + yj - self.hour_zhi_idx) % 12
        g = _dun(self.day_gan, js_zhi)
        return {"gan": g, "zhi": DIZHI[js_zhi], "star": JIANG[js_zhi],
                "gz": g + DIZHI[js_zhi]}

    def _guishen(self):
        """贵神：贵起支 g0 + 顺/逆布圈取地分位。"""
        g0 = DIZHI.index(self.gui_zhi)
        if g0 in (11, 0, 1, 2, 3):  # 亥子丑寅卯 -> 顺布
            k = (self.df_idx - g0) % 12
        else:                       # 巳午未申酉 -> 逆布
            k = (g0 - self.df_idx) % 12
        star = GODS[k]
        gs_zhi = GUI_ZHI_FIX[k]
        g = _dun(self.day_gan, gs_zhi)
        return {"gan": g, "zhi": DIZHI[gs_zhi], "star": star,
                "gz": g + DIZHI[gs_zhi],
                "dn": "昼贵" if self.day else "夜贵"}

    # ---------- 出口 ----------
    def analyze(self):
        ry = self._renyuan()
        js = self._jiangshen()
        gs = self._guishen()
        ry_el = GAN_ELEM[ry]
        js_el = ZHI_ELEM[js["zhi"]]
        gs_el = ZHI_ELEM[gs["zhi"]]
        df_el = ZHI_ELEM[self.difen]
        return {
            "summary": f"金口诀：{self.difen}方，人元{ry}、贵神{gs['star']}"
                       f"（{gs['gan']}{gs['zhi']}）、将神{js['star']}（{js['gan']}{js['zhi']}）。",
            "render": self._render(ry, ry_el, gs, gs_el, js, js_el, df_el),
            "year_gz": self.year_gz, "month_gz": self.month_gz,
            "day_gan": self.day_gan, "day_zhi": self.day_zhi,
            "hour_gan": self.hour_gan, "hour_zhi": self.hour_zhi,
            "yuejiang": self.yue_jiang,
            "kong": [self.kong[0], self.kong[1]], "bigkong": self.bigkong,
            "difen": self.difen, "difen_el": df_el,
            "renyuan": {"gan": ry, "el": ry_el},
            "guishen": {"gan": gs["gan"], "zhi": gs["zhi"], "star": gs["star"],
                        "el": gs_el, "dn": gs["dn"],
                        "gz": gs["gan"] + gs["zhi"]},
            "jiangshen": {"gan": js["gan"], "zhi": js["zhi"], "star": js["star"],
                          "el": js_el, "gz": js["gan"] + js["zhi"]},
        }

    def _render(self, ry, ry_el, gs, gs_el, js, js_el, df_el):
        L = ["金口诀课式", "-" * 36]
        L.append(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gan}{self.day_zhi}日 "
                 f"{self.hour_gan}{self.hour_zhi}时")
        L.append(f"月将: {self.yue_jiang}   日空({self.kong[0]}、{self.kong[1]})   "
                 f"四大空亡({self.bigkong})")
        L.append(f"人元: {ry} {ry_el}")
        L.append(f"贵神: {gs['gz']}（{gs['star']}）{gs_el}  {gs['dn']}")
        L.append(f"将神: {js['gz']}（{js['star']}）{js_el}")
        L.append(f"地分: {self.difen} {df_el}")
        return "\n".join(L)
