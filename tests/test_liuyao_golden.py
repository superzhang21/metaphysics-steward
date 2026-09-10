# -*- coding: utf-8 -*-
"""六爻黄金案例自动回归：对照 实测结果"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from core.liuyao import LiuyaoEngine
from core.calendar import get_true_solar_time, get_lunar
from datetime import datetime

def cast(dt_str, vals):
    dt = get_true_solar_time(datetime.strptime(dt_str, "%Y-%m-%d %H:%M"), 120.0)
    lunar = get_lunar(dt)
    return LiuyaoEngine(lunar=lunar, line_values=vals).analyze()

def check(name, got, expect):
    ok = got == expect
    print(f"{'OK ' if ok else 'FAIL'} {name}: got={got} expect={expect}")
    return ok

def run():
    passed = True
    # 案例A: 乾为天 静卦 (2026-09-12 己丑日), 全7
    r = cast("2026-09-12 12:00", [7, 7, 7, 7, 7, 7])
    passed &= check("A 卦名", r['ben_gua']['name'], "乾为天")
    passed &= check("A 宫", r['ben_gua']['gong'], "乾")
    passed &= check("A 世应", (r['ben_gua']['shi'], r['ben_gua']['ying']), (6, 3))
    passed &= check("A 纳甲", r['ben_gua']['najia'], ["甲子", "甲寅", "甲辰", "壬午", "壬申", "壬戌"])
    passed &= check("A 六亲", r['ben_gua']['liuqin'], ["子孙", "妻财", "父母", "官鬼", "兄弟", "父母"])
    passed &= check("A 六神(初->上)", r['ben_gua']['liushen'], ["螣蛇", "白虎", "玄武", "青龙", "朱雀", "勾陈"])
    passed &= check("A 无变卦", r['bian_gua'] is None, True)

    # 案例B: 乾为天 初爻动 -> 天风姤 (2026-09-09 丙戌日)
    r = cast("2026-09-09 14:30", [9, 7, 7, 7, 7, 7])
    passed &= check("B 主卦", r['ben_gua']['name'], "乾为天")
    passed &= check("B 动爻", r['moving'], [1])
    passed &= check("B 变卦名", r['bian_gua']['name'], "天风姤")
    passed &= check("B 变卦宫", r['bian_gua']['gong'], "乾")
    passed &= check("B 变卦世应", (r['bian_gua']['shi'], r['bian_gua']['ying']), (1, 4))
    passed &= check("B 变卦纳甲", r['bian_gua']['najia'], ["辛丑", "辛亥", "辛酉", "壬午", "壬申", "壬戌"])
    passed &= check("B 变卦六亲", r['bian_gua']['liuqin'], ["父母", "子孙", "兄弟", "官鬼", "兄弟", "父母"])

    # 案例C: 地天泰 初爻动 -> 地风升 (跨宫, 2026-09-12 己丑日)
    r = cast("2026-09-12 12:00", [9, 7, 7, 8, 8, 8])
    passed &= check("C 主卦", r['ben_gua']['name'], "地天泰")
    passed &= check("C 主卦宫", r['ben_gua']['gong'], "坤")
    passed &= check("C 主卦世应", (r['ben_gua']['shi'], r['ben_gua']['ying']), (3, 6))
    passed &= check("C 变卦", r['bian_gua']['name'], "地风升")
    passed &= check("C 变卦宫", r['bian_gua']['gong'], "震")
    passed &= check("C 变卦世应", (r['bian_gua']['shi'], r['bian_gua']['ying']), (4, 1))
    passed &= check("C 变卦六亲(坤土)", r['bian_gua']['liuqin'], ["兄弟", "妻财", "子孙", "兄弟", "妻财", "子孙"])

    print("\n结果:", "全部通过" if passed else "存在失败")
    return passed


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
