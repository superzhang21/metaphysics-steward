# -*- coding: utf-8 -*-
"""八字合婚引擎（完整版）+ 八字引擎口径回归。

覆盖：
1. 基础四柱口径
2. 合婚基础维度（生肖六合/六冲/日干五合）
3. 完整版维度：双造 JSON 结构（十神/藏干/大运/喜用神/神煞）、
   神煞警示（阴差阳错日/魁罡日）、用神互补文本、大运同频文本
4. 关系表自洽
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
from core.hehun import HehunEngine
from core.hehun import (ZHI_LIUHE, ZHI_CHONG, TIANGAN_WUHE, SHENGXIAO,
                        YINCHA_YANGCUO_DAYS, KUI_GANG_DAYS)
from core.bazi import BaziEngine


def pillars(dt, lon=116.4, sex=1):
    eng = BaziEngine(dt, sex, longitude=lon, use_true_solar=True)
    return [eng.pillars_gz["Year"], eng.pillars_gz["Month"],
            eng.pillars_gz["Day"], eng.pillars_gz["Hour"]]


def test_bazi_basic():
    assert pillars(datetime(1990, 2, 4, 10, 40)) == ["庚午", "戊寅", "庚子", "辛巳"]
    print("OK  八字基础四柱")


def find_day(day_gan, y0=1985, y1=1990):
    for y in range(y0, y1):
        for mo in range(1, 13):
            for d in range(1, 29):
                if pillars(datetime(y, mo, d, 12, 0))[2][0] == day_gan:
                    return datetime(y, mo, d, 12, 0)
    return None


def test_hehun_combos():
    # 男 甲子(鼠) 女 乙丑(牛) -> 子丑六合
    r = HehunEngine(datetime(1984, 6, 1, 10, 0), datetime(1985, 6, 1, 10, 0),
                    male_lon=116.4, female_lon=116.4).analyze()
    assert "六合" in "\n".join(r["items"]), r["items"]
    assert 60 <= r["score"] <= 100
    print(f"OK  生肖六合: {r['score']}分")

    # 男 丙子(鼠) 女 壬午(马) -> 子午冲
    r2 = HehunEngine(datetime(1996, 6, 1, 10, 0), datetime(2002, 6, 1, 10, 0),
                     male_lon=116.4, female_lon=116.4).analyze()
    assert "相冲" in "\n".join(r2["items"]), r2["items"]
    print(f"OK  生肖六冲: {r2['score']}分")

    # 日干五合：甲日男 + 己日女
    male_dt = find_day("甲")
    female_dt = find_day("己")
    if male_dt and female_dt:
        r3 = HehunEngine(male_dt, female_dt, male_lon=116.4, female_lon=116.4).analyze()
        assert "五合" in "\n".join(r3["items"]), r3["items"]
        print(f"OK  日干五合: {r3['score']}分")
    else:
        print("SKIP 日干五合（未找到示例日期）")


def test_full_structure():
    """完整版：双造 JSON 含四柱详情/十神/藏干/大运/喜用神/神煞。"""
    r = HehunEngine(datetime(1990, 2, 4, 10, 40), datetime(1991, 1, 1, 12, 0),
                    male_lon=116.4, female_lon=116.4).analyze()
    for tag, person in (("男", r["male"]), ("女", r["female"])):
        p = person["pillars"]
        assert set(p) == {"Year", "Month", "Day", "Hour"}
        for k in ("Year", "Month", "Day", "Hour"):
            assert "gz" in p[k] and "shishen" in p[k] and "hidden" in p[k] and "nayin" in p[k]
        # 十神第一行含日主
        assert p["Day"]["shishen"] == "日主"
        # 大运
        yun = person["yun"]
        assert "start_desc" in yun and len(yun["da_yun"]) >= 6
        assert all("pillar" in dy and "start_age" in dy for dy in yun["da_yun"])
        # 喜用神与神煞字段
        assert "element" in person["yongshen"] and "reason" in person["yongshen"]
        assert isinstance(person["shensha"], list)
    # 渲染含双造完整信息
    rn = r["render"]
    for kw in ("十神", "藏干", "起运", "大运", "喜用"):
        assert kw in rn, kw
    print("OK  完整版双造 JSON 结构 + render 全量字段")


def test_yongshen_complement_text():
    """用神互补与日主强弱文本出现在分析项。"""
    r = HehunEngine(datetime(1990, 2, 4, 10, 40), datetime(1991, 1, 1, 12, 0),
                    male_lon=116.4, female_lon=116.4).analyze()
    joined = "\n".join(r["items"])
    assert "喜用神" in joined or "用神" in joined
    assert r["male"]["yongshen"]["element"] in "木火土金水"
    print("OK  用神互补文本（" + r["male"]["yongshen"]["reason"] + "）")


def test_shensha_warning():
    """神煞警示：阴差阳错日 / 魁罡日 触发警示文本。"""
    # 1985-01-07 00:00 丙午日（阴差阳错日，羊刃在日支）
    d_yc = datetime(1985, 1, 7, 0, 0)
    assert pillars(d_yc)[2] == "丙午"
    r = HehunEngine(d_yc, datetime(1990, 6, 1, 10, 0),
                    male_lon=116.4, female_lon=116.4).analyze()
    joined = "\n".join(r["items"])
    names = [s["name"] for s in r["male"]["shensha"]]
    assert "阴差阳错" in names, names
    assert "警示" in joined and "阴差阳错" in joined
    print("OK  阴差阳错日警示 (男" + r["male"]["gz"][2] + "日)")

    # 1985-01-11 00:00 庚戌日（魁罡日，甲子年寡宿在戌）
    d_kg = datetime(1985, 1, 11, 0, 0)
    assert pillars(d_kg)[2] == "庚戌"
    r2 = HehunEngine(datetime(1988, 3, 1, 8, 0), d_kg,
                     male_lon=116.4, female_lon=116.4).analyze()
    names2 = [s["name"] for s in r2["female"]["shensha"]]
    assert "魁罡" in names2, names2
    joined2 = "\n".join(r2["items"])
    assert "魁罡" in joined2
    print("OK  魁罡日警示 (女" + r2["female"]["gz"][2] + "日)")


def test_dayun_sync_text():
    """大运同频文本与吉忌标注出现。"""
    r = HehunEngine(datetime(1990, 2, 4, 10, 40), datetime(1991, 1, 1, 12, 0),
                    male_lon=116.4, female_lon=116.4).analyze()
    joined = "\n".join(r["items"])
    assert "大运同频" in joined
    assert "男大运评估" in joined and "女大运评估" in joined
    print("OK  大运同频评估文本")


def test_relation_tables():
    for k, v in ZHI_LIUHE.items():
        assert ZHI_LIUHE[v] == k
    for k, v in ZHI_CHONG.items():
        assert ZHI_CHONG[v] == k
    for (a, b), el in TIANGAN_WUHE.items():
        assert TIANGAN_WUHE[(b, a)] == el
    assert len(SHENGXIAO) == 12
    assert len(YINCHA_YANGCUO_DAYS) == 12
    assert KUI_GANG_DAYS <= {"庚辰", "庚戌", "壬辰", "戊戌"}
    print("OK  地支/天干关系表 + 神煞日表自洽")


if __name__ == "__main__":
    test_bazi_basic()
    test_relation_tables()
    test_hehun_combos()
    test_full_structure()
    test_yongshen_complement_text()
    test_shensha_warning()
    test_dayun_sync_text()
    print("\n== 合婚完整版回归通过 ==")
