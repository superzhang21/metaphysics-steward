# -*- coding: utf-8 -*-
"""梅花易数回归：经典时间起卦/数字起卦 + 本卦/互卦/变卦/体用 推导。

说明： 无独立「梅花体用」模块（其"六爻梅花排盘"页为纳甲六爻，已由
test_liuyao_golden 锁定）；本引擎按经典《梅花易数》规则实现，测试锁定：
- 时间起卦：上卦=(年支序+农历月+农历日)%8、下卦=再+时辰支序%8、动爻=再%6（0 记 8/6）。
- 数字起卦：三数 (上,下,动) 取余。
- 本卦/互卦（二三四爻为下互、三四五爻为上互）/变卦（动爻变阴阳）/体用（动爻在
  下卦则体在下，在上卦则体在上）。
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from core.calendar import get_lunar
from core.meihua import MeihuaEngine

GUA = {"乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8}
DIZHI = list("子丑寅卯辰巳午未申酉戌亥")

def time_bits(dt):
    lu = get_lunar(dt)
    y = DIZHI.index(lu.getYearZhi()) + 1
    mo = abs(lu.getMonth())
    dd = lu.getDay()
    h = DIZHI.index(lu.getTimeZhi()) + 1
    upper = (y + mo + dd) % 8 or 8
    lower = (y + mo + dd + h) % 8 or 8
    mv = (y + mo + dd + h) % 6 or 6
    return upper, lower, mv

def run():
    ok = fail = 0
    def check(name, got, exp):
        nonlocal ok, fail
        if got == exp:
            ok += 1
        else:
            fail += 1
            print(f"FAIL {name}: got={got} expect={exp}")

    # 案例1: 时间起卦 2026-09-12 12:00 = 丙午年八月初二午时 (午7/月8/日2/午7)
    dt = datetime(2026, 9, 12, 12, 0)
    up, lo, mv = time_bits(dt)
    check("T1 上卦数", up, 1)      # 乾
    check("T1 下卦数", lo, 8)      # 坤
    check("T1 动爻", mv, 6)
    a = MeihuaEngine(lunar=get_lunar(dt)).analyze()
    check("T1 本卦", a["original"]["name"], "天地否")
    check("T1 互卦", a["mutual"]["name"], "风山渐")
    check("T1 变卦", a["changed"]["name"], "泽地萃")
    check("T1 动爻", a["moving_line"], 6)
    check("T1 体用", (a["ti"], a["yong"]), ("坤", "乾"))

    # 案例2: 数字起卦 上乾下坤动6 -> 天地否/风山渐/泽地萃（同案例1）
    a = MeihuaEngine(numbers=[1, 8, 6]).analyze()
    check("N1 本卦", a["original"]["name"], "天地否")
    check("N1 互卦", a["mutual"]["name"], "风山渐")
    check("N1 变卦", a["changed"]["name"], "泽地萃")
    check("N1 体用", (a["ti"], a["yong"]), ("坤", "乾"))

    # 案例3: 数字起卦 上火下泽动2 -> 睽
    a = MeihuaEngine(numbers=[3, 2, 2]).analyze()   # 离上兑下 = 火泽睽
    check("N2 本卦", a["original"]["name"], "火泽睽")
    check("N2 动爻", a["moving_line"], 2)
    check("N2 体用(动2在下->用为兑,体离)", (a["ti"], a["yong"]), ("离", "兑"))
    # 互卦: 睽 线: 兑(0,1,1) 下, 离(1,0,1) 上 -> 全 [1,1,0, 1,0,1] bottom..top
    # lines bottom->top = 兑底0,兑中1,兑上1, 离底1,离中0,离上1 = [0,1,1,1,0,1]
    # 互下 = lines2,3,4 = (1,1,1)? 实际引擎取 original[3],original[2],original[1]
    check("N2 互卦", a["mutual"]["name"], "水火既济")

    # 案例4: 时间起卦 1990-05-08 12:00（庚午年四月十四午时; 午7/月4/日14/午7）
    up, lo, mv = time_bits(datetime(1990, 5, 8, 12, 0))
    a = MeihuaEngine(lunar=get_lunar(datetime(1990, 5, 8, 12, 0))).analyze()
    # 上=(7+4+14)%8=25%8=1 乾; 下=(25+7)%8=32%8=0->8 坤; 动=(32)%6=2
    check("T2 上卦数", up, 1)
    check("T2 下卦数", lo, 8)
    check("T2 动爻", mv, 2)
    check("T2 本卦", a["original"]["name"], "天地否")
    check("T2 体用(动2->用为坤,体乾)", (a["ti"], a["yong"]), ("乾", "坤"))

    print(f"\n梅花易数回归: {ok} 通过 / {fail} 失败")
    return fail == 0

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
