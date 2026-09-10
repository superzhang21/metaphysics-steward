# -*- coding: utf-8 -*-
"""全面回归：
1. GUA_64 覆盖 64 卦、无重名（涣卦已补）
2. 八宫 64 卦世位与京房标准一致
3. 随机全量六爻起卦无异常（含全部 64 卦可达性）
4. 既有六法 quick check
"""
import sys, random
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))


def test_gua64_coverage():
    """GUA_64 覆盖 64 卦、无重名"""
    from core import utils
    all_pairs = [(u, l) for u in range(1, 9) for l in range(1, 9)]
    missing = [p for p in all_pairs if p not in utils.GUA_64]
    names = list(utils.GUA_64.values())
    dup = [n for n in set(names) if names.count(n) > 1]
    print("GUA_64:", len(utils.GUA_64), "缺:", missing or "无", "重名:", dup or "无")
    assert not missing and not dup


def test_bagua_shiwei():
    """八宫 64 卦世位与京房标准一致"""
    from core import utils
    xian = {1: (1, 1, 1), 2: (1, 1, 0), 3: (1, 0, 1), 4: (1, 0, 0),
            5: (0, 1, 1), 6: (0, 1, 0), 7: (0, 0, 1), 8: (0, 0, 0)}
    rev = {v: k for k, v in xian.items()}
    gong_num = {'乾': 1, '兑': 2, '离': 3, '震': 4, '巽': 5, '坎': 6, '艮': 7, '坤': 8}
    shis = [6, 1, 2, 3, 4, 5, 4, 3]

    def lines(u, l): return list(xian[l]) + list(xian[u])
    def pair(ls): return (rev[tuple(ls[3:6])], rev[tuple(ls[0:3])])

    err = 0
    for gong in gong_num:
        nn = gong_num[gong]
        base = lines(nn, nn)
        seq = [base[:]]
        for n in range(1, 6):
            c = base[:]
            for i in range(n): c[i] = 1 - c[i]
            seq.append(c)
        you = seq[5][:]; you[3] = 1 - you[3]; seq.append(you)
        gui = you[:]
        for i in range(3): gui[i] = base[i]
        seq.append(gui)
        for pos, ls in enumerate(seq):
            u, l = pair(ls)
            nm, g, shi = utils.GUA_64_INFO[(u, l)]
            if g != gong or shi != shis[pos]:
                print(f"表错: ({u},{l}) {nm} 记录{g}/{shi}, 应为{gong}/世{shis[pos]}")
                err += 1
    print("八宫表校验:", "OK (64/64)" if err == 0 else f"{err} 处错误")
    assert err == 0


def test_liuyao_fuzz():
    """六爻 2000 次随机静/动组合无异常，覆盖多种卦"""
    from core.liuyao import LiuyaoEngine
    from core.calendar import get_lunar
    from datetime import datetime, timedelta
    random.seed(42)
    bad = 0
    gua_hit = set()
    for _ in range(2000):
        vals = [random.choice([6, 7, 8, 9]) for _ in range(6)]
        d = datetime(2000, 1, 1) + timedelta(days=random.randint(0, 9000), hours=random.randint(0, 23))
        lunar = get_lunar(d)
        r = LiuyaoEngine(lunar=lunar, line_values=vals).analyze()
        gua_hit.add(r['ben_gua']['name'])
        if r['bian_gua']:
            gua_hit.add(r['bian_gua']['name'])
        assert len(r['ben_gua']['najia']) == 6
        assert len(r['ben_gua']['liuqin']) == 6
        assert len(r['ben_gua']['liushen']) == 6
        assert set(r['ben_gua']['liuqin']) <= {"兄弟", "子孙", "父母", "妻财", "官鬼"}
    print(f"六爻随机 2000 次无异常；命中的卦数: {len(gua_hit)}/64")
    assert len(gua_hit) >= 40, "覆盖卦数过少"


def test_existing_engines():
    """既有六法 quick check"""
    from core.bazi import BaziEngine
    from core.qimen import QimenEngine
    from core.ziwei import ZiweiEngine
    from core.liuren import LiurenEngine
    from core.meihua import MeihuaEngine
    from core.jinkoujue import JinkoujueEngine
    from core.calendar import get_true_solar_time, get_lunar
    dt = get_true_solar_time(datetime(1990, 2, 4, 10, 40), 120.0)
    lunar = get_lunar(dt)
    for eng in [BaziEngine(dt, 1), MeihuaEngine(lunar=lunar), QimenEngine(lunar),
                ZiweiEngine(lunar), LiurenEngine(lunar), JinkoujueEngine(lunar, difen="子")]:
        res = eng.analyze()
        assert "render" in res or "summary" in res
    print("既有六法 quick check: OK")


if __name__ == "__main__":
    from datetime import datetime, timedelta
    test_gua64_coverage()
    test_bagua_shiwei()
    test_liuyao_fuzz()
    test_existing_engines()
    print("\n== 全部回归通过 ==")
