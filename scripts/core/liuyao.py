# -*- coding: utf-8 -*-
"""六爻排盘引擎（纳甲筮法，对照  六爻盘）。

支持：
- 铜钱起卦（手工指定六个 6/7/8/9 或三个数）
- 时间起卦（农历 年月日时，梅花数法取上卦/下卦/动爻）
- 装卦：定卦名、定宫、安世应、纳甲、配六亲、装六神
- 断卦辅助：动爻变卦、六亲持世、旺衰（月建日辰简评）

实现口径与实测 六爻盘一致（已用其在线盘 3 组黄金案例逐行核对）：
- 爻值：6=老阴(动)，7=少阳，8=少阴，9=老阳(动)
- 六神起例：甲乙青龙、丙丁朱雀、戊勾陈、己螣蛇、庚辛白虎、壬癸玄武
- 纳甲：下卦取纯卦内卦三爻，上卦取纯卦外卦三爻
"""

from __future__ import annotations

from .utils import (
    TIANGAN, DIZHI, WUXING, GUA_64_INFO, GONG_WUXING,
    LIU_SHEN, LIU_SHEN_START, NAJIA, BAGUA_NAME, SHENG, KE,
)

# 先天卦名 -> 先天数
XIANTIAN_NUM = {"乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8}
# 先天数 -> (初,二,三)爻阳值
XIAN_BITS = {
    1: (1, 1, 1), 2: (1, 1, 0), 3: (1, 0, 1), 4: (1, 0, 0),
    5: (0, 1, 1), 6: (0, 1, 0), 7: (0, 0, 1), 8: (0, 0, 0),
}
BITS_TO_NUM = {v: k for k, v in XIAN_BITS.items()}

# 地支六亲关系取地支五行与宫五行关系
YONG_SHEN_HINT = {
    "妻财": "求财/交易/妻事/失物(财物)",
    "官鬼": "事业/官非/疾病/盗贼/夫星",
    "父母": "文书/房产/长辈/车辆/房屋",
    "子孙": "子女/福神/解忧/医药/平安",
    "兄弟": "朋友/同事/竞争/破财/同辈",
}


def _tri_bits_to_num(bits):
    """三爻位(初,二,三) -> 先天卦数。"""
    return BITS_TO_NUM.get(tuple(bits))


def line_to_yinyang(value):
    """爻值 6/7/8/9 -> 阴阳 0/1。6,8 阴；7,9 阳。"""
    return 1 if value in (7, 9) else 0


def is_moving(value):
    return value in (6, 9)


class LiuyaoEngine:
    """六爻排盘引擎。"""

    def __init__(self, lunar=None, line_values=None, numbers=None):
        """
        lunar: lunar_python 的 Lunar 对象（用于时间起卦与时干支）
        line_values: 六个爻值(自初爻至上爻)，铜钱起卦时给出；6/7/8/9
        numbers: 三数起卦（梅花式：上卦/下卦/动爻）
        """
        self.lunar = lunar
        if line_values:
            if len(line_values) != 6:
                raise ValueError("line_values 必须为 6 个爻值")
            self.line_values = [int(v) for v in line_values]
            self.method = "手工指定"
        elif lunar is not None:
            self.line_values = self._cast_by_time(lunar, numbers)
            self.method = "时间起卦"
        elif numbers and len(numbers) == 3:
            self.line_values = self._cast_by_numbers(numbers)
            self.method = "数字起卦"
        else:
            raise ValueError("必须提供 line_values / lunar 或 numbers")

    # ---------- 起卦 ----------
    @staticmethod
    def coin_cast(coin_results):
        """六个铜钱背数(0-3) -> 六爻值(6/7/8/9)。三背=老阳9，两背=少阴8，一背=少阳7，零背=老阴6。"""
        mapping = {3: 9, 2: 8, 1: 7, 0: 6}
        return [mapping[c] for c in coin_results]

    @staticmethod
    def _cast_by_numbers(numbers):
        """三数 -> 六爻（梅花法：数定上下卦与动爻）。"""
        n1, n2, n3 = [int(x) for x in numbers]
        upper = (n1 - 1) % 8 + 1
        lower = (n2 - 1) % 8 + 1
        moving = (n3 - 1) % 6 + 1
        return LiuyaoEngine._lines_from_trigrams(upper, lower, moving)

    @staticmethod
    def _cast_by_time(lunar, numbers=None):
        """农历 年月日时 -> 上下卦与动爻。

        上卦 = (年支序 + 月 + 日) % 8；下卦 = (+时支序) % 8；动爻 = (总和) % 6。
        numbers 可选：额外加数（加数起卦）。
        """
        year_idx = DIZHI.index(lunar.getYearZhi()) + 1
        month = abs(lunar.getMonth())
        day = lunar.getDay()
        hour_idx = DIZHI.index(lunar.getTimeZhi()) + 1
        extra = sum(int(x) for x in (numbers or [])) if numbers else 0

        upper = (year_idx + month + day + extra) % 8
        if upper == 0:
            upper = 8
        lower = (year_idx + month + day + hour_idx + extra) % 8
        if lower == 0:
            lower = 8
        moving = (year_idx + month + day + hour_idx + extra) % 6
        if moving == 0:
            moving = 6
        return LiuyaoEngine._lines_from_trigrams(upper, lower, moving)

    @staticmethod
    def _lines_from_trigrams(upper, lower, moving):
        """由上下卦先天数与动爻 -> 六个爻值(初->上)。动爻按本卦阴阳转为老阴/老阳。"""
        u_bits = XIAN_BITS[upper]
        l_bits = XIAN_BITS[lower]
        # 本卦六爻自下而上：下卦(初二三) + 上卦(四五上)
        yangs = list(l_bits) + list(u_bits)
        values = []
        for i in range(6):
            if i + 1 == moving:
                values.append(6 if yangs[i] == 0 else 9)  # 阴动为6 阳动为9
            else:
                values.append(7 if yangs[i] == 1 else 8)
        return values

    # ---------- 装卦 ----------
    def _to_trigrams(self, yangs):
        """六爻阴阳(初->上) -> (上卦先天数, 下卦先天数)。"""
        lower = _tri_bits_to_num(tuple(yangs[0:3]))
        upper = _tri_bits_to_num(tuple(yangs[3:6]))
        return upper, lower

    def _najia_for(self, yangs):
        """对一组六爻阴阳(初->上)装纳甲干支：下卦取纯卦内卦，上卦取纯卦外卦。"""
        upper_num, lower_num = self._to_trigrams(yangs)
        upper_name = BAGUA_NAME[upper_num]
        lower_name = BAGUA_NAME[lower_num]
        na_upper = NAJIA[upper_name][3:6]
        na_lower = NAJIA[lower_name][0:3]
        return list(na_lower) + list(na_upper)  # 自初爻到上爻

    def _liuqin_for(self, gong, na_list):
        """按宫五行安六亲。"""
        gong_wx = GONG_WUXING[gong]
        liuqin = []
        for gz in na_list:
            zhi = gz[1]
            zhi_wx = WUXING[zhi]
            if zhi_wx == gong_wx:
                qin = "兄弟"
            elif SHENG[gong_wx] == zhi_wx:  # 我生
                qin = "子孙"
            elif SHENG[zhi_wx] == gong_wx:  # 生我
                qin = "父母"
            elif KE[gong_wx] == zhi_wx:  # 我克
                qin = "妻财"
            else:  # 克我
                qin = "官鬼"
            liuqin.append(qin)
        return liuqin

    def _liushen_for(self, day_gan):
        """按日干安六神，自初爻向上循环。"""
        start = LIU_SHEN_START.get(day_gan, 0)
        return [LIU_SHEN[(start + i) % 6] for i in range(6)]

    # ---------- 主流程 ----------
    def analyze(self):
        values = self.line_values
        yangs = [line_to_yinyang(v) for v in values]
        moving_idx = [i + 1 for i, v in enumerate(values) if is_moving(v)]

        # 本卦
        u_num, l_num = self._to_trigrams(yangs)
        name, gong, shi = GUA_64_INFO[(u_num, l_num)]
        ying = (shi + 2) % 6 + 1

        # 变卦（动爻翻转）
        if moving_idx:
            change_yangs = list(yangs)
            for i in moving_idx:
                change_yangs[i - 1] = 1 - change_yangs[i - 1]
            cu_num, cl_num = self._to_trigrams(change_yangs)
            c_name, c_gong, c_shi = GUA_64_INFO[(cu_num, cl_num)]
            c_ying = (c_shi + 2) % 6 + 1
        else:
            change_yangs = None
            cu_num, cl_num, c_name, c_gong, c_shi, c_ying = None, None, None, None, None, None

        # 纳甲 + 六亲
        na = self._najia_for(yangs)
        liuqin = self._liuqin_for(gong, na)
        c_na = self._najia_for(change_yangs) if change_yangs else None
        c_liuqin = self._liuqin_for(gong, c_na) if c_na else None

        # 六神
        day_gan = self.lunar.getDayGan() if self.lunar else "甲"
        liushen = self._liushen_for(day_gan)

        # 日辰月建（旺衰参考）
        month_zhi = self.lunar.getMonthZhi() if self.lunar else None
        day_zhi = self.lunar.getDayZhi() if self.lunar else None

        lines = []
        for i in range(5, -1, -1):  # 上爻到初爻
            pos = i + 1
            yin_yang = "▅▅▅▅▅" if yangs[i] == 1 else "▅▅　▅▅"
            moving_mark = "○" if values[i] in (6, 9) else ""
            shi_ying = ""
            if pos == shi and pos == ying:
                shi_ying = "世应"
            elif pos == shi:
                shi_ying = "世"
            elif pos == ying:
                shi_ying = "应"

            # 变爻
            c_part = ""
            if c_na is not None:
                cy = "▅▅▅▅▅" if change_yangs[i] == 1 else "▅▅　▅▅"
                c_sy = ""
                if pos == c_shi and pos == c_ying:
                    c_sy = "世应"
                elif pos == c_shi:
                    c_sy = "世"
                elif pos == c_ying:
                    c_sy = "应"
                c_part = f"{cy} {c_liuqin[i]}{c_na[i]} {c_sy}".rstrip()

            lines.append(
                f"{liushen[i]:　<2} {yin_yang} {moving_mark} {liuqin[i]}{na[i]} {shi_ying}"
                + (f"　→ {c_part}" if c_part else "")
            )

        head = f"六爻排盘 [{self.method}]"
        render = [head, "-" * 46]
        if self.lunar:
            render.append(
                f"时间: {self.lunar.getSolar().toYmdHms()} (农历{self.lunar.getMonthInChinese()}月{self.lunar.getDayInChinese()})"
            )
            render.append(f"日辰: {self.lunar.getDayInGanZhi()}  月建: {self.lunar.getMonthZhi()}")
        if moving_idx:
            render.append(f"主卦: {name}({gong}宫)  之  变卦: {c_name}({c_gong}宫)  动爻: {','.join(str(x) for x in moving_idx)}")
        else:
            render.append(f"主卦: {name}({gong}宫)  静卦无动爻")
        render.append("")
        render.extend(lines)
        render.append("-" * 46)
        render.append(f"世爻在{['', '初', '二', '三', '四', '五', '上'][shi]}爻 应爻在{['', '初', '二', '三', '四', '五', '上'][ying]}爻")

        # summary
        shi_liuqin = liuqin[shi - 1]
        summary = f"{name}（{gong}宫），世持{shi_liuqin}。"
        if moving_idx:
            summary += f"动爻{','.join(str(x) for x in moving_idx)}，之卦{c_name}。"
        summary += f"用神参考：{YONG_SHEN_HINT.get(shi_liuqin, '')}"

        result = {
            "method": self.method,
            "line_values": values,
            "yangs": yangs,
            "moving": moving_idx,
            "ben_gua": {"name": name, "gong": gong, "shi": shi, "ying": ying,
                        "najia": na, "liuqin": liuqin, "liushen": liushen},
            "bian_gua": ({"name": c_name, "gong": c_gong, "shi": c_shi, "ying": c_ying,
                          "najia": c_na, "liuqin": c_liuqin} if c_na else None),
            "day": {"gan": day_gan, "zhi": day_zhi, "month_zhi": month_zhi},
            "summary": summary,
            "render": "\n".join(render),
        }
        return result

