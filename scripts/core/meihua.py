# -*- coding: utf-8 -*-
from .utils import BAGUA_NAME, GUA_64, DIZHI

class MeihuaEngine:
    """
    Mei Hua Yi Shu (Plum Blossom Divination) Engine.
    Supports time-based and number-based hexagram generation.
    """
    def __init__(self, lunar=None, numbers=None):
        """
        lunar: Lunar object for time-based divination
        numbers: list of 3 numbers [upper, lower, moving] for interactive
        """
        if numbers:
            self.upper_num = (numbers[0] - 1) % 8 + 1
            self.lower_num = (numbers[1] - 1) % 8 + 1
            self.moving_line = (numbers[2] - 1) % 6 + 1
        elif lunar:
            self.lunar = lunar
            year_idx = DIZHI.index(lunar.getYearZhi()) + 1
            month_idx = abs(lunar.getMonth())
            day_idx = lunar.getDay()
            hour_idx = DIZHI.index(lunar.getTimeZhi()) + 1

            self.upper_num = (year_idx + month_idx + day_idx) % 8
            if self.upper_num == 0: self.upper_num = 8

            self.lower_num = (year_idx + month_idx + day_idx + hour_idx) % 8
            if self.lower_num == 0: self.lower_num = 8

            self.moving_line = (year_idx + month_idx + day_idx + hour_idx) % 6
            if self.moving_line == 0: self.moving_line = 6
        else:
            raise ValueError("Either lunar or numbers must be provided")

    def get_bits(self, num):
        """Xiantian Bagua bit representation (Top, Mid, Bottom)."""
        m = {
            1: (1, 1, 1), 2: (0, 1, 1), 3: (1, 0, 1), 4: (0, 0, 1),
            5: (1, 1, 0), 6: (0, 1, 0), 7: (1, 0, 0), 8: (0, 0, 0)
        }
        return m[num]

    def bits_to_num(self, bits):
        m = {
            (1, 1, 1): 1, (0, 1, 1): 2, (1, 0, 1): 3, (0, 0, 1): 4,
            (1, 1, 0): 5, (0, 1, 0): 6, (1, 0, 0): 7, (0, 0, 0): 8
        }
        return m[bits]

    def get_gua_name(self, upper, lower):
        return GUA_64.get((upper, lower), f"{BAGUA_NAME[upper]}{BAGUA_NAME[lower]}")

    def analyze(self):
        u_t, u_m, u_b = self.get_bits(self.upper_num)
        l_t, l_m, l_b = self.get_bits(self.lower_num)

        # Line 1 (bottom) to 6 (top)
        original_lines = [l_b, l_m, l_t, u_b, u_m, u_t]

        # Mutual Hexagram (Hu Gua)
        # Lower: Lines 2, 3, 4
        # Upper: Lines 3, 4, 5
        mutual_lower_bits = (original_lines[3], original_lines[2], original_lines[1])
        mutual_upper_bits = (original_lines[4], original_lines[3], original_lines[2])

        mutual_upper_num = self.bits_to_num(mutual_upper_bits)
        mutual_lower_num = self.bits_to_num(mutual_lower_bits)

        # Changed Hexagram (Bian Gua)
        changed_lines = list(original_lines)
        changed_lines[self.moving_line - 1] = 1 - changed_lines[self.moving_line - 1]

        changed_lower_bits = (changed_lines[2], changed_lines[1], changed_lines[0])
        changed_upper_bits = (changed_lines[5], changed_lines[4], changed_lines[3])

        changed_upper_num = self.bits_to_num(changed_upper_bits)
        changed_lower_num = self.bits_to_num(changed_lower_bits)

        # Ti vs Yong
        if self.moving_line <= 3:
            ti_num, yong_num = self.upper_num, self.lower_num
            ti_pos, yong_pos = "上", "下"
        else:
            ti_num, yong_num = self.lower_num, self.upper_num
            ti_pos, yong_pos = "下", "上"

        res = {
            "original": {"name": self.get_gua_name(self.upper_num, self.lower_num), "upper": BAGUA_NAME[self.upper_num], "lower": BAGUA_NAME[self.lower_num]},
            "mutual": {"name": self.get_gua_name(mutual_upper_num, mutual_lower_num), "upper": BAGUA_NAME[mutual_upper_num], "lower": BAGUA_NAME[mutual_lower_num]},
            "changed": {"name": self.get_gua_name(changed_upper_num, changed_lower_num), "upper": BAGUA_NAME[changed_upper_num], "lower": BAGUA_NAME[changed_lower_num]},
            "moving_line": self.moving_line,
            "ti": BAGUA_NAME[ti_num],
            "yong": BAGUA_NAME[yong_num]
        }

        render = f"梅花易数卦象\n"
        render += "-" * 30 + "\n"
        render += f"本卦：{res['original']['name']} ({res['original']['upper']}上{res['original']['lower']}下)\n"
        render += f"互卦：{res['mutual']['name']} ({res['mutual']['upper']}上{res['mutual']['lower']}下)\n"
        render += f"变卦：{res['changed']['name']} ({res['changed']['upper']}上{res['changed']['lower']}下)\n"
        render += f"动爻：{self.moving_line}爻 (体卦在{ti_pos}，用卦在{yong_pos})\n"
        render += "-" * 30 + "\n"

        # ASCII visualization
        lines_viz = []
        for i in range(5, -1, -1):
            char = "━━━  ━━━" if original_lines[i] == 0 else "━━━━━━━━"
            marker = " (动)" if i == self.moving_line - 1 else ""
            lines_viz.append(f"{char}{marker}")
        render += "\n".join(lines_viz)

        res["render"] = render
        return res
