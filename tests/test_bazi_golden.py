# -*- coding: utf-8 -*-
"""八字换柱黄金回归：对照 参考排盘.权威排盘.com 实测四柱。

覆盖：12 节气（含立春换年）交节前后临界、晚子时换日（真太阳时>=23:00）、
跨经度（北京/乌鲁木齐/西安/哈尔滨）真太阳时对日/时柱影响、
zty=0（不用真太阳时）对照。

黄金数据采集时间：2026-09-12，来源 权威在线排盘参考站点
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from core.bazi import BaziEngine

# (输入公历 datetime, 经度, use_true_solar, 权威排盘四柱[年月日时], 标签)
GOLDEN = [
    # ── 2026 节气临界（北京 116.4，真太阳时开启）──
    (datetime(2026, 1, 5, 16, 21), 116.4, True, ["乙巳", "戊子", "己卯", "壬申"], "小寒-2"),
    (datetime(2026, 1, 5, 16, 25), 116.4, True, ["乙巳", "己丑", "己卯", "壬申"], "小寒+2"),
    (datetime(2026, 2, 4, 3, 57), 116.4, True, ["乙巳", "己丑", "己酉", "丙寅"], "立春-5"),
    (datetime(2026, 2, 4, 4, 7), 116.4, True, ["丙午", "庚寅", "己酉", "丙寅"], "立春+5"),
    (datetime(2026, 6, 5, 23, 46), 116.4, True, ["丙午", "癸巳", "辛亥", "戊子"], "芒种-2 晚子时"),
    (datetime(2026, 6, 5, 23, 50), 116.4, True, ["丙午", "甲午", "辛亥", "戊子"], "芒种+2 晚子时"),
    (datetime(2026, 4, 5, 2, 38), 116.4, True, ["丙午", "辛卯", "己酉", "乙丑"], "清明-2"),
    (datetime(2026, 4, 5, 2, 42), 116.4, True, ["丙午", "壬辰", "己酉", "乙丑"], "清明+2"),
    (datetime(2026, 8, 7, 19, 40), 116.4, True, ["丙午", "乙未", "癸丑", "壬戌"], "立秋-2"),
    (datetime(2026, 8, 7, 19, 44), 116.4, True, ["丙午", "丙申", "癸丑", "壬戌"], "立秋+2"),
    (datetime(2026, 11, 7, 17, 51), 116.4, True, ["丙午", "戊戌", "乙酉", "乙酉"], "立冬-1 真太阳越过节"),
    # ── 晚子时换日（北京 2026-02-03 23:30，真太阳 23:02 -> 次日）──
    (datetime(2026, 2, 3, 23, 30), 116.4, True, ["乙巳", "己丑", "己酉", "甲子"], "晚子时换日"),
    (datetime(2026, 2, 3, 23, 10), 116.4, True, ["乙巳", "己丑", "戊申", "癸亥"], "晚子时未到23点不换日"),
    # ── 跨经度真太阳时对日/时柱影响 ──
    (datetime(1990, 6, 6, 12, 30), 87.68, True, ["庚午", "壬午", "壬寅", "乙巳"], "乌市午->巳"),
    (datetime(1990, 6, 6, 23, 30), 87.68, True, ["庚午", "壬午", "壬寅", "辛亥"], "乌市晚亥"),
    (datetime(1990, 6, 6, 7, 0), 87.68, True, ["庚午", "壬午", "壬寅", "壬寅"], "乌市晨"),
    (datetime(1990, 2, 4, 10, 40), 116.4, True, ["庚午", "戊寅", "庚子", "辛巳"], "1990立春后"),
    (datetime(1990, 6, 6, 23, 30), 116.4, True, ["庚午", "壬午", "癸卯", "壬子"], "1990晚子换日"),
    (datetime(1990, 6, 6, 23, 0), 116.4, True, ["庚午", "壬午", "壬寅", "辛亥"], "1990晚亥"),
    # ── zty=0（不使用真太阳时）：全部按输入时间 ──
    (datetime(1990, 6, 6, 12, 30), 87.68, False, ["庚午", "壬午", "壬寅", "丙午"], "zty0乌市午时"),
    (datetime(2026, 2, 4, 3, 57), 116.4, False, ["乙巳", "己丑", "己酉", "丙寅"], "zty0立春前"),
    (datetime(2026, 2, 4, 4, 7), 116.4, False, ["丙午", "庚寅", "己酉", "丙寅"], "zty0立春后"),
]


def main():
    passed = 0
    failed = 0
    for i, (dt, lon, use_true, expect, label) in enumerate(GOLDEN):
        eng = BaziEngine(dt, 1, longitude=lon, use_true_solar=use_true)
        got = [eng.pillars_gz["Year"], eng.pillars_gz["Month"],
               eng.pillars_gz["Day"], eng.pillars_gz["Hour"]]
        ok = got == expect
        if ok:
            passed += 1
            print(f"OK   [{label:<16}] {got}")
        else:
            failed += 1
            print(f"FAIL [{label:<16}] got={got} expect={expect}  (输入{dt} 经度{lon} 真太阳={use_true})")
    print(f"\n结果: {passed} 通过 / {failed} 失败 / 共 {len(GOLDEN)}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
