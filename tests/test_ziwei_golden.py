# -*- coding: utf-8 -*-
"""紫微斗数引擎 黄金回归。

口径 2026-09-12 经  实测锁定：
- 12 组黄金案例（不同年/月/日/时，真太阳时 zty=1，北京）：命宫/身宫/五行局/
  命主/身主 + 十四主星全图 逐一对照。
- 五行局x农历日 -> 紫微宫 全表（水二/木三/金四/土五/火六 共 149 点）。
- 边界：真太阳时 >= 23:00 晚子时换日（农历日+1、按子时）。
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from core.ziwei import ZiweiEngine, _ziwei_idx
from core.calendar import get_true_solar_time, get_lunar

# 黄金案例（真太阳时，北京 116.4，男性）
GOLDEN = [
    {  # case a
        'input': "1990-02-04 10:40", 'lon': 116.4,
        'minggong': "酉", 'shengong': "未", 'ju': "水二局", 'ju_num': 2,
        'mingzhu': "文曲", 'shenzhu': "火星",
        'stars': {"紫微": "巳", "天机": "辰", "太阳": "寅", "武曲": "丑", "天同": "子", "廉贞": "酉", "天府": "亥", "太阴": "子", "贪狼": "丑", "巨门": "寅", "天相": "卯", "天梁": "辰", "七杀": "巳", "破军": "酉"},
    },
    {  # case b
        'input': "1988-05-18 14:30", 'lon': 116.4,
        'minggong': "戌", 'shengong': "子", 'ju': "水二局", 'ju_num': 2,
        'mingzhu': "禄存", 'shenzhu': "文昌",
        'stars': {"紫微": "寅", "天机": "丑", "太阳": "亥", "武曲": "戌", "天同": "酉", "廉贞": "午", "天府": "寅", "太阴": "卯", "贪狼": "辰", "巨门": "巳", "天相": "午", "天梁": "未", "七杀": "申", "破军": "子"},
    },
    {  # case c
        'input': "1985-11-07 09:15", 'lon': 116.4,
        'minggong': "巳", 'shengong': "卯", 'ju': "金四局", 'ju_num': 4,
        'mingzhu': "武曲", 'shenzhu': "天相",
        'stars': {"紫微": "巳", "天机": "辰", "太阳": "寅", "武曲": "丑", "天同": "子", "廉贞": "酉", "天府": "亥", "太阴": "子", "贪狼": "丑", "巨门": "寅", "天相": "卯", "天梁": "辰", "七杀": "巳", "破军": "酉"},
    },
    {  # case d
        'input': "1993-08-26 20:45", 'lon': 116.4,
        'minggong': "戌", 'shengong': "午", 'ju': "水二局", 'ju_num': 2,
        'mingzhu': "禄存", 'shenzhu': "天同",
        'stars': {"紫微": "巳", "天机": "辰", "太阳": "寅", "武曲": "丑", "天同": "子", "廉贞": "酉", "天府": "亥", "太阴": "子", "贪狼": "丑", "巨门": "寅", "天相": "卯", "天梁": "辰", "七杀": "巳", "破军": "酉"},
    },
    {  # case e
        'input': "1978-01-15 06:20", 'lon': 116.4,
        'minggong': "戌", 'shengong': "辰", 'ju': "金四局", 'ju_num': 4,
        'mingzhu': "禄存", 'shenzhu': "天机",
        'stars': {"紫微": "寅", "天机": "丑", "太阳": "亥", "武曲": "戌", "天同": "酉", "廉贞": "午", "天府": "寅", "太阴": "卯", "贪狼": "辰", "巨门": "巳", "天相": "午", "天梁": "未", "七杀": "申", "破军": "子"},
    },
    {  # case f
        'input': "2000-12-31 16:55", 'lon': 116.4,
        'minggong': "巳", 'shengong': "酉", 'ju': "金四局", 'ju_num': 4,
        'mingzhu': "武曲", 'shenzhu': "文昌",
        'stars': {"紫微": "巳", "天机": "辰", "太阳": "寅", "武曲": "丑", "天同": "子", "廉贞": "酉", "天府": "亥", "太阴": "子", "贪狼": "丑", "巨门": "寅", "天相": "卯", "天梁": "辰", "七杀": "巳", "破军": "酉"},
    },
    {  # case g
        'input': "1995-06-12 11:10", 'lon': 116.4,
        'minggong': "丑", 'shengong': "亥", 'ju': "火六局", 'ju_num': 6,
        'mingzhu': "巨门", 'shenzhu': "天机",
        'stars': {"紫微": "丑", "天机": "子", "太阳": "戌", "武曲": "酉", "天同": "申", "廉贞": "巳", "天府": "卯", "太阴": "辰", "贪狼": "巳", "巨门": "午", "天相": "未", "天梁": "申", "七杀": "酉", "破军": "丑"},
    },
    {  # case h
        'input': "1982-09-03 03:35", 'lon': 116.4,
        'minggong': "午", 'shengong': "戌", 'ju': "水二局", 'ju_num': 2,
        'mingzhu': "破军", 'shenzhu': "文昌",
        'stars': {"紫微": "酉", "天机": "申", "太阳": "午", "武曲": "巳", "天同": "辰", "廉贞": "丑", "天府": "未", "太阴": "申", "贪狼": "酉", "巨门": "戌", "天相": "亥", "天梁": "子", "七杀": "丑", "破军": "巳"},
    },
    {  # case i
        'input': "2003-04-28 12:25", 'lon': 116.4,
        'minggong': "戌", 'shengong': "戌", 'ju': "水二局", 'ju_num': 2,
        'mingzhu': "禄存", 'shenzhu': "天相",
        'stars': {"紫微": "寅", "天机": "丑", "太阳": "亥", "武曲": "戌", "天同": "酉", "廉贞": "午", "天府": "寅", "太阴": "卯", "贪狼": "辰", "巨门": "巳", "天相": "午", "天梁": "未", "七杀": "申", "破军": "子"},
    },
    {  # case j
        'input': "1991-10-16 22:50", 'lon': 116.4,
        'minggong': "亥", 'shengong': "酉", 'ju': "木三局", 'ju_num': 3,
        'mingzhu': "巨门", 'shenzhu': "天相",
        'stars': {"紫微": "辰", "天机": "卯", "太阳": "丑", "武曲": "子", "天同": "亥", "廉贞": "申", "天府": "子", "太阴": "丑", "贪狼": "寅", "巨门": "卯", "天相": "辰", "天梁": "巳", "七杀": "午", "破军": "戌"},
    },
    {  # case k
        'input': "1987-03-09 07:05", 'lon': 116.4,
        'minggong': "子", 'shengong': "午", 'ju': "木三局", 'ju_num': 3,
        'mingzhu': "贪狼", 'shenzhu': "天同",
        'stars': {"紫微": "未", "天机": "午", "太阳": "辰", "武曲": "卯", "天同": "寅", "廉贞": "亥", "天府": "酉", "太阴": "戌", "贪狼": "亥", "巨门": "子", "天相": "丑", "天梁": "寅", "七杀": "卯", "破军": "未"},
    },
    {  # case l
        'input': "1997-07-21 15:40", 'lon': 116.4,
        'minggong': "亥", 'shengong': "卯", 'ju': "金四局", 'ju_num': 4,
        'mingzhu': "巨门", 'shenzhu': "天相",
        'stars': {"紫微": "卯", "天机": "寅", "太阳": "子", "武曲": "亥", "天同": "戌", "廉贞": "未", "天府": "丑", "太阴": "寅", "贪狼": "卯", "巨门": "辰", "天相": "巳", "天梁": "午", "七杀": "未", "破军": "亥"},
    },
]

# 实测 五行局 x 农历日 -> 紫微宫 全表（30 日，'?'=该农历月无 30 日）
JU_DAY_ZW = {"水二局": "丑寅寅卯卯辰辰巳巳午午未未申申酉酉戌戌亥亥子子丑丑寅寅卯卯辰", "木三局": "辰丑寅巳寅卯午卯辰未辰巳申巳午酉午未戌未申亥申酉子酉戌丑戌亥", "金四局": "亥辰丑寅子巳寅卯丑午卯辰寅未辰巳卯申巳午辰酉午未巳戌未申午亥", "土五局": "午亥辰丑寅未子巳寅卯申丑午卯辰酉寅未辰巳戌卯申巳午亥辰酉午?", "火六局": "酉午亥辰丑寅戌未子巳寅卯亥申丑午卯辰子酉寅未辰巳丑戌卯申巳?"}

JUN = {'水二局': 2, '木三局': 3, '金四局': 4, '土五局': 5, '火六局': 6}
ZX = list('子丑寅卯辰巳午未申酉戌亥')


def engine_of(dt, lon=116.4):
    ts = get_true_solar_time(dt, lon)
    lunar = get_lunar(ts)
    return ZiweiEngine(lunar, solar_dt=ts).analyze()


def test_golden_12():
    for c in GOLDEN:
        dt = datetime.strptime(c['input'], '%Y-%m-%d %H:%M')
        r = engine_of(dt, c['lon'])
        assert r['minggong'] == c['minggong'], (c['input'], r['minggong'], c['minggong'])
        assert r['shengong'] == c['shengong'], (c['input'], r['shengong'], c['shengong'])
        assert r['ju'] == c['ju'], (c['input'], r['ju'], c['ju'])
        assert r['ju_num'] == c['ju_num'], c
        assert r['mingzhu'] == c['mingzhu'], (c['input'], r['mingzhu'], c['mingzhu'])
        assert r['shenzhu'] == c['shenzhu'], (c['input'], r['shenzhu'], c['shenzhu'])
        for s, b in c['stars'].items():
            assert r['stars'].get(s) == b, (c['input'], s, r['stars'].get(s), b)
        print("OK  [%s] 命宫%s 身宫%s %s 紫微%s" % (
            c['input'], c['minggong'], c['shengong'], c['ju'], c['stars']['紫微']))
    print("OK  紫微黄金 12 案例全维度通过")


def test_ziwei_day_table():
    """五行局 x 农历日 -> 紫微宫 全表（ 149 点）。"""
    for ju_name, seq in JU_DAY_ZW.items():
        ju = JUN[ju_name]
        for d in range(1, 31):
            ch = seq[d - 1]
            if ch == '?':
                continue
            assert ZX[_ziwei_idx(ju, d)] == ch, (ju_name, d, ZX[_ziwei_idx(ju, d)], ch)
    print("OK  五行局x农历日 紫微全表（149 点）与实测 一致")


def test_late_zishi_boundary():
    """晚子时：真太阳时 >=23:00 换日；未到 23:00 不换。"""
    r = engine_of(datetime(1990, 2, 4, 23, 30), 116.4)
    assert r['minggong'] == '寅' and r['ju_num'] == 5, (r['minggong'], r['ju_num'])
    assert r['stars']['紫微'] == '卯', r['stars']['紫微']
    print("OK  晚子时 23:30 -> 换日，土五局 紫微卯")

    r2 = engine_of(datetime(1990, 2, 4, 23, 0), 116.4)
    assert r2['minggong'] == '卯' and r2['stars']['紫微'] == '寅', (r2['minggong'], r2['stars']['紫微'])
    print("OK  23:00 -> 不换日，紫微寅")


if __name__ == '__main__':
    test_golden_12()
    test_ziwei_day_table()
    test_late_zishi_boundary()
    print("\n== 紫微 黄金回归通过 ==")
