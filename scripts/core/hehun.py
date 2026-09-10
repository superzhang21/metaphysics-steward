# -*- coding: utf-8 -*-
"""八字合婚引擎（完整版：双造同排 + 用神互补 + 神煞警示 + 大运同频）。

覆盖合婚维度：
1. 生肖（年支）：六合 / 三合 / 六冲 / 六害 / 相刑
2. 年命纳音：相生 / 相克 / 同气
3. 日干：天干五合（甲己/乙庚/丙辛/丁壬/戊癸）、五行生克
4. 夫妻宫（日支）：六合 / 三合 / 六冲 / 六害 / 相刑
5. 五行互补：双方命局缺失五行是否被对方补足
6. 喜用神互补：依日主强弱断喜用神，看对方命局是否补我方用神
7. 神煞警示：阴差阳错日 / 魁罡 / 孤辰寡宿 / 羊刃 / 桃花(咸池) / 华盖 / 驿马 / 红鸾天喜
8. 大运同频：双方十年大运按公历年份对齐，评估喜用吉运重叠度

评分：基线 60，叠加各维度后截断 [0,100]。
评级：>=85 上等；70-84 中上；55-69 中等；<55 普通。

注意：合婚吉凶须结合双方完整命局、大运流年综合判断，本模块仅供传统文化参考，
不构成婚恋决策建议。
"""

from __future__ import annotations

from .bazi import BaziEngine
from .utils import TIANGAN, DIZHI, WUXING, SHENG, KE, HIDDEN_GANS


# 生肖（年支）关系表
ZHI_LIUHE = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
             "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
ZHI_CHONG = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
             "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
ZHI_HAI = {"子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
           "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}
ZHI_XING_3 = [("寅", "巳", "申"), ("丑", "戌", "未")]
ZHI_XING_2 = {("子", "卯"): "子卯相刑"}
# 三合（含本支）
ZHI_SANHE = {"申": ["子", "辰"], "子": ["申", "辰"], "辰": ["申", "子"],
             "寅": ["午", "戌"], "午": ["寅", "戌"], "戌": ["寅", "午"],
             "巳": ["酉", "丑"], "酉": ["巳", "丑"], "丑": ["巳", "酉"],
             "亥": ["卯", "未"], "卯": ["亥", "未"], "未": ["亥", "卯"]}
# 天干五合
TIANGAN_WUHE = {("甲", "己"): "土", ("己", "甲"): "土",
                ("乙", "庚"): "金", ("庚", "乙"): "金",
                ("丙", "辛"): "水", ("辛", "丙"): "水",
                ("丁", "壬"): "木", ("壬", "丁"): "木",
                ("戊", "癸"): "火", ("癸", "戊"): "火"}

SHENGXIAO = {"子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
             "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪"}

# 神煞速查表
TAOHUA_POS = {"申子辰": "酉", "寅午戌": "卯", "巳酉丑": "午", "亥卯未": "子"}   # 咸池/桃花
HUAGAI_POS = {"申子辰": "辰", "寅午戌": "戌", "巳酉丑": "丑", "亥卯未": "未"}   # 华盖(墓库)
YIMA_POS = {"申子辰": "寅", "寅午戌": "申", "巳酉丑": "亥", "亥卯未": "巳"}     # 驿马
GUCHEN_POS = {"亥子丑": "寅", "寅卯辰": "巳", "巳午未": "申", "申酉戌": "亥"}   # 孤辰
GUASU_POS = {"亥子丑": "戌", "寅卯辰": "丑", "巳午未": "辰", "申酉戌": "未"}    # 寡宿
YANGREN_POS = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}      # 阳刃（阳干）
KUI_GANG_DAYS = {"庚辰", "庚戌", "壬辰", "戊戌"}                                # 魁罡日
YINCHA_YANGCUO_DAYS = {"丙子", "丙午", "丁丑", "丁未", "戊寅", "戊申",
                       "辛卯", "辛酉", "壬辰", "壬戌", "癸巳", "癸亥"}            # 阴差阳错日


def _sheng_me(el):
    """生我之五行（印）。"""
    return {v: k for k, v in SHENG.items()}[el]


def _ke_me(el):
    """克我之五行（官杀）。"""
    return {v: k for k, v in KE.items()}[el]


def _group_of(zhi):
    for g in TAOHUA_POS:
        if zhi in g:
            return g
    return None


class HehunEngine:
    """八字合婚引擎（完整版）。"""

    def __init__(self, male_dt, female_dt, male_sex=1, female_sex=0,
                 male_lon=120.0, female_lon=120.0, use_true_solar=True):
        self.male = BaziEngine(male_dt, male_sex, longitude=male_lon,
                               use_true_solar=use_true_solar).analyze()
        self.female = BaziEngine(female_dt, female_sex, longitude=female_lon,
                                 use_true_solar=use_true_solar).analyze()
        self.use_true_solar = use_true_solar

    # ---------- 五行统计 ----------
    @staticmethod
    def _count_wuxing(analyzed):
        """统计四柱五行出现次数（天干+地支+藏干主气各记，藏干主气 0.5）。"""
        wc = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        for key in ["Year", "Month", "Day", "Hour"]:
            p = analyzed["pillars"][key]
            wc[WUXING[p["gan"]]] += 1
            wc[WUXING[p["zhi"]]] += 1
            if p["hidden"]:
                wc[WUXING[p["hidden"][0]["gan"]]] += 0.5
        return wc

    @staticmethod
    def _nayin(gz):
        from lunar_python.util import LunarUtil
        return LunarUtil.NAYIN.get(gz, "")

    # ---------- 日主强弱与喜用神 ----------
    @staticmethod
    def _strength(analyzed, wc=None):
        """日主强弱：同党（日主+印）占比 >=62% 身强、<=38% 身弱、其余中和。"""
        if wc is None:
            wc = HehunEngine._count_wuxing(analyzed)
        dm = analyzed["pillars"]["Day"]["gan"]
        dm_el = WUXING[dm]
        tong = wc[dm_el] + wc[_sheng_me(dm_el)]
        yi = wc[SHENG[dm_el]] + wc[_ke_me(dm_el)] + wc[KE[dm_el]]
        total = tong + yi
        ratio = tong / total if total else 0.5
        if ratio >= 0.62:
            return "身强", ratio, dm_el
        if ratio <= 0.38:
            return "身弱", ratio, dm_el
        return "中和", ratio, dm_el

    @staticmethod
    def _yongshen(analyzed):
        """断喜用神五行与取用理由。

        身强：需克泄耗，取官杀/食伤/财中命局最弱者先用；
        身弱：需生扶，取印/比劫中命局最弱者先用；
        中和：取全局最缺之五行调候。
        """
        wc = HehunEngine._count_wuxing(analyzed)
        verdict, ratio, dm_el = HehunEngine._strength(analyzed, wc)
        if verdict == "身强":
            cand = {_ke_me(dm_el): "官杀", SHENG[dm_el]: "食伤", KE[dm_el]: "财"}
        elif verdict == "身弱":
            cand = {_sheng_me(dm_el): "印", dm_el: "比劫"}
        else:
            weakest = min(wc, key=wc.get)
            return {"verdict": "中和", "element": weakest,
                    "reason": "日主中和，取全局最缺之" + weakest + "调候"}
        el = min(cand, key=wc.get)
        label = cand[el]
        action = "克泄耗以制身" if verdict == "身强" else "生扶以助身"
        return {"verdict": verdict, "element": el, "label": label,
                "reason": "日主" + verdict + "(占比" + str(round(ratio * 100)) + "%)，用神" + el + "(" + label + ")以" + action}

    # ---------- 神煞 ----------
    @staticmethod
    def _person_shensha(analyzed):
        """单造婚姻相关神煞清单：[{name, at, detail}]。"""
        p = analyzed["pillars"]
        yz = p["Year"]["zhi"]
        day_gz = p["Day"]["gz"]
        dg = day_gz[0]
        dz = day_gz[1]
        zhis = {"年支": yz, "月支": p["Month"]["zhi"],
                "日支": dz, "时支": p["Hour"]["zhi"]}
        out = []
        grp = _group_of(yz)

        def has(z):
            for k, v in zhis.items():
                if v == z:
                    return k
            return None

        if grp:
            tp = has(TAOHUA_POS[grp])
            if tp:
                out.append({"name": "桃花(咸池)", "at": tp,
                            "detail": "年支" + grp + "局之桃花在" + TAOHUA_POS[grp]})
            hg = has(HUAGAI_POS[grp])
            if hg:
                out.append({"name": "华盖", "at": hg,
                            "detail": "年支" + grp + "局之华盖在" + HUAGAI_POS[grp]})
            ym = has(YIMA_POS[grp])
            if ym:
                out.append({"name": "驿马", "at": ym,
                            "detail": "年支" + grp + "局之驿马在" + YIMA_POS[grp]})
        # 孤辰寡宿
        gz_group = None
        for g in GUCHEN_POS:
            if yz in g:
                gz_group = g
                break
        if gz_group:
            at = has(GUCHEN_POS[gz_group])
            if at:
                out.append({"name": "孤辰", "at": at,
                            "detail": "孤辰星现于" + at})
            at2 = has(GUASU_POS[gz_group])
            if at2:
                out.append({"name": "寡宿", "at": at2,
                            "detail": "寡宿星现于" + at2})
        if YANGREN_POS.get(dg):
            at = has(YANGREN_POS[dg])
            if at:
                out.append({"name": "羊刃", "at": at,
                            "detail": "日主" + dg + "羊刃在" + YANGREN_POS[dg]})
        if day_gz in KUI_GANG_DAYS:
            out.append({"name": "魁罡", "at": "日柱",
                        "detail": "魁罡日 " + day_gz + "，性刚果断"})
        if day_gz in YINCHA_YANGCUO_DAYS:
            out.append({"name": "阴差阳错", "at": "日柱",
                        "detail": "阴差阳错日 " + day_gz + "，婚缘多有波折"})
        # 红鸾/天喜：年支起，红鸾=(卯3-年支序)%12，天喜在对宫
        yz_idx = DIZHI.index(yz)
        hl = DIZHI[(3 - yz_idx) % 12]
        tx = DIZHI[(3 - yz_idx + 6) % 12]
        at_hl = has(hl)
        at_tx = has(tx)
        if at_hl:
            out.append({"name": "红鸾", "at": at_hl, "detail": "红鸾入命，主姻缘喜庆"})
        if at_tx:
            out.append({"name": "天喜", "at": at_tx, "detail": "天喜入命，主喜事临门"})
        return out

    # ---------- 单项分析 ----------
    def _year_analysis(self):
        """生肖（六合/三合/冲/害/刑）与年命纳音关系。"""
        my = self.male["pillars"]["Year"]["zhi"]
        fy = self.female["pillars"]["Year"]["zhi"]
        m_sx, f_sx = SHENGXIAO[my], SHENGXIAO[fy]
        notes = []
        score = 0

        def xing(a, b):
            if (a, b) in ZHI_XING_2 or (b, a) in ZHI_XING_2:
                return True
            for g in ZHI_XING_3:
                if a in g and b in g and a != b:
                    return True
            return False

        if ZHI_LIUHE.get(my) == fy:
            notes.append("生肖 " + m_sx + "与" + f_sx + " 六合，主相处和睦、家宅安顺（+10）"); score += 10
        elif ZHI_CHONG.get(my) == fy:
            notes.append("生肖 " + m_sx + "与" + f_sx + " 相冲，易生分歧，宜以日柱/五行调和（-8）"); score -= 8
        elif ZHI_HAI.get(my) == fy:
            notes.append("生肖 " + m_sx + "与" + f_sx + " 相害，易有暗耗口舌，需多包容（-5）"); score -= 5
        elif fy in ZHI_SANHE.get(my, []):
            notes.append("生肖 " + m_sx + "与" + f_sx + " 三合，性情相投、互助（+4）"); score += 4
        elif xing(my, fy):
            notes.append("生肖 " + m_sx + "与" + f_sx + " 相刑，时有磨擦需忍让（-3）"); score -= 3
        else:
            notes.append("生肖 " + m_sx + "与" + f_sx + " 无冲刑害，属平常（+2）"); score += 2

        m_n = self._nayin(self.male["pillars"]["Year"]["gz"])
        f_n = self._nayin(self.female["pillars"]["Year"]["gz"])
        m_el = m_n[-1] if m_n else ""
        f_el = f_n[-1] if f_n else ""
        notes.append("年命纳音：男 " + m_n + " / 女 " + f_n)
        if m_el and f_el:
            if m_el == f_el:
                notes.append("年命同气(" + m_el + ")，性情相类（+3）"); score += 3
            elif SHENG.get(m_el) == f_el:
                notes.append("男命" + m_el + "生女命" + f_el + "，纳音相生（+5）"); score += 5
            elif SHENG.get(f_el) == m_el:
                notes.append("女命" + f_el + "生男命" + m_el + "，纳音相生（+5）"); score += 5
            elif KE.get(m_el) == f_el or KE.get(f_el) == m_el:
                notes.append("年命相克(" + m_el + "x" + f_el + ")，需五行补救（-4）"); score -= 4
        return notes, score

    def _day_analysis(self):
        """日柱（日主与夫妻宫）分析。"""
        md = self.male["pillars"]["Day"]
        fd = self.female["pillars"]["Day"]
        m_gan, f_gan = md["gan"], fd["gan"]
        m_zhi, f_zhi = md["zhi"], fd["zhi"]
        notes = []
        score = 0

        if (m_gan, f_gan) in TIANGAN_WUHE:
            el = TIANGAN_WUHE[(m_gan, f_gan)]
            notes.append("日干五合：" + m_gan + f_gan + "合化" + el + "，主情意相投（+10）"); score += 10
        else:
            mw, fw = WUXING[m_gan], WUXING[f_gan]
            if mw == fw:
                notes.append("日主同气：男" + m_gan + "(" + mw + ") 女" + f_gan + "(" + fw + ")，志趣相合（+5）"); score += 5
            elif SHENG.get(mw) == fw:
                notes.append("男日主" + m_gan + "(" + mw + ")生女日主" + f_gan + "(" + fw + ")，男愿付出（+4）"); score += 4
            elif SHENG.get(fw) == mw:
                notes.append("女日主" + f_gan + "(" + fw + ")生男日主" + m_gan + "(" + mw + ")，女多包容（+4）"); score += 4
            elif KE.get(mw) == fw:
                notes.append("男日主" + m_gan + "(" + mw + ")克女日主" + f_gan + "(" + fw + ")，宜柔化（-4）"); score -= 4
            elif KE.get(fw) == mw:
                notes.append("女日主" + f_gan + "(" + fw + ")克男日主" + m_gan + "(" + mw + ")，需男让（-4）"); score -= 4

        if ZHI_LIUHE.get(m_zhi) == f_zhi:
            notes.append("夫妻宫六合：男" + m_zhi + " 女" + f_zhi + "，姻缘和美（+10）"); score += 10
        elif f_zhi in ZHI_SANHE.get(m_zhi, []):
            notes.append("夫妻宫三合：男" + m_zhi + " 女" + f_zhi + "，相得益彰（+8）"); score += 8
        elif ZHI_CHONG.get(m_zhi) == f_zhi:
            notes.append("夫妻宫相冲：男" + m_zhi + " 女" + f_zhi + "，易冲突，需磨合（-8）"); score -= 8
        elif ZHI_HAI.get(m_zhi) == f_zhi:
            notes.append("夫妻宫相害：男" + m_zhi + " 女" + f_zhi + "，暗中别扭（-5）"); score -= 5
        elif (m_zhi, f_zhi) in ZHI_XING_2 or (f_zhi, m_zhi) in ZHI_XING_2:
            notes.append("夫妻宫相刑：男" + m_zhi + " 女" + f_zhi + "，时有磕绊（-4）"); score -= 4
        else:
            notes.append("夫妻宫 " + m_zhi + "/" + f_zhi + " 关系平常（+2）"); score += 2
        return notes, score

    def _wuxing_complement(self):
        """五行互补：一方命局明显缺失、另一方该行较旺即补益。"""
        mw = self._count_wuxing(self.male)
        fw = self._count_wuxing(self.female)
        notes = []
        score = 0
        weak_m = [k for k, v in mw.items() if v <= 0.5]
        weak_f = [k for k, v in fw.items() if v <= 0.5]
        hit = [w for w in weak_m if fw.get(w, 0) >= 2.0]
        hit2 = [w for w in weak_f if mw.get(w, 0) >= 2.0]
        if hit or hit2:
            notes.append("五行互补：男缺" + ("".join(weak_m) or "无") + "，女缺" + ("".join(weak_f) or "无") + "，互有补益（+6）")
            score += 6
        else:
            notes.append("男缺" + ("".join(weak_m) or "无") + "、女缺" + ("".join(weak_f) or "无") + "，互补一般（+1）")
            score += 1
        notes.append("男五行强度：" + self._fmt_wx(mw))
        notes.append("女五行强度：" + self._fmt_wx(fw))
        return notes, score

    def _yongshen_complement(self):
        """喜用神互补：对方命局是否补我方用神。"""
        m_use = self._yongshen(self.male)
        f_use = self._yongshen(self.female)
        mw = self._count_wuxing(self.male)
        fw = self._count_wuxing(self.female)
        notes = ["男喜用神：" + m_use["reason"],
                 "女喜用神：" + f_use["reason"]]
        score = 0
        me, fe = m_use["element"], f_use["element"]
        f_supply = fw.get(me, 0) >= 2.0
        m_supply = mw.get(fe, 0) >= 2.0
        if f_supply and m_supply:
            notes.append("用神互补：女方补男方" + me + "、男方补女方" + fe + "，互为助益（+8）")
            score += 8
        elif f_supply:
            notes.append("用神互补：女方命局" + me + "较旺，可补男方用神（+4）")
            score += 4
        elif m_supply:
            notes.append("用神互补：男方命局" + fe + "较旺，可补女方用神（+4）")
            score += 4
        else:
            notes.append("用神互补一般：双方需各自调候（+1）")
            score += 1
        fw_min = min(fw, key=fw.get)
        mw_min = min(mw, key=mw.get)
        if me == fw_min and fw[me] <= 0.5:
            notes.append("注意：男方用神" + me + "恰为女方最弱，需双方共同努力补足")
            score -= 1
        if fe == mw_min and mw[fe] <= 0.5:
            notes.append("注意：女方用神" + fe + "恰为男方最弱，需双方共同努力补足")
            score -= 1
        return notes, score

    def _shensha_warning(self):
        """双方神煞警示。"""
        ms = self._person_shensha(self.male)
        fs = self._person_shensha(self.female)
        notes = ["男命神煞：" + ("、".join(s["name"] + "@" + s["at"] for s in ms) or "无明显神煞"),
                 "女命神煞：" + ("、".join(s["name"] + "@" + s["at"] for s in fs) or "无明显神煞")]
        score = 0

        def has(name):
            return any(s["name"] == name for s in ms + fs)

        if has("阴差阳错"):
            notes.append("警示：有阴差阳错日，婚缘多波折、易聚少离多，需多经营（-3）"); score -= 3
        if has("魁罡"):
            notes.append("警示：有魁罡日，个性刚强好胜，相处需多包容退让（-2）"); score -= 2
        if has("孤辰") or has("寡宿"):
            notes.append("警示：有孤辰/寡宿，情感易有疏离感，宜主动维系（-2）"); score -= 2
        n_th = len([s for s in ms + fs if s["name"] == "桃花(咸池)"])
        if n_th >= 2:
            notes.append("提示：双方桃花共" + str(n_th) + "处，异性缘旺，需自律专一")
        elif n_th == 1:
            notes.append("提示：有桃花入命，异性缘佳")
        if has("红鸾") or has("天喜"):
            notes.append("吉庆：红鸾/天喜入命，多主姻缘喜庆之象")
            score += 1
        return notes, score

    def _dayun_sync(self):
        """大运同频：按公历年份对齐双方十年大运，评估喜用吉运重叠。"""
        notes = []
        score = 0
        m_use = self._yongshen(self.male)
        f_use = self._yongshen(self.female)

        def dy_eval(yun, use_el):
            lst = []
            for dy in yun.get("da_yun", []):
                gz = dy["pillar"]
                gan, zhi = gz[0], gz[1]
                ge, ze = WUXING[gan], WUXING[zhi]
                good = (ge == use_el or SHENG[ge] == use_el
                        or ze == use_el or SHENG[ze] == use_el)
                bad = (ge != use_el and KE[ge] == use_el) or (ze != use_el and KE[ze] == use_el)
                if good and not bad:
                    grade = "吉"
                elif bad and not good:
                    grade = "忌"
                else:
                    grade = "平"
                lst.append({"pillar": gz, "start_year": dy["start_year"],
                            "end_year": dy["end_year"], "grade": grade})
            return lst

        my = dy_eval(self.male["yun"], m_use["element"])
        fy = dy_eval(self.female["yun"], f_use["element"])
        notes.append("男大运评估(喜" + m_use["element"] + ")：" +
                     " ".join(d["pillar"] + "(" + d["grade"] + ")" for d in my[:8]))
        notes.append("女大运评估(喜" + f_use["element"] + ")：" +
                     " ".join(d["pillar"] + "(" + d["grade"] + ")" for d in fy[:8]))

        def grade_at(lst, year):
            for d in lst:
                if d["start_year"] <= year <= d["end_year"]:
                    return d["grade"]
            return "平"

        # 共同公历年份
        my_yr = set()
        for d in my:
            my_yr.update(range(d["start_year"], d["end_year"] + 1))
        fy_yr = set()
        for d in fy:
            fy_yr.update(range(d["start_year"], d["end_year"] + 1))
        common = sorted(my_yr & fy_yr)
        if common:
            # 评估窗口：两人都已起运之后，取起运后 50 年（婚姻经营黄金期）
            start = max(my[0]["start_year"], fy[0]["start_year"])
            end = min(max(my_yr), max(fy_yr), start + 49)
            common = [y for y in common if start <= y <= end]
        both_good = [y for y in common if grade_at(my, y) == "吉" and grade_at(fy, y) == "吉"]
        if common:
            ratio = len(both_good) / len(common)
            bonus = round(6 * ratio)
            score += bonus
            txt = ("大运同频：共同年份" + str(len(common)) + "年中双方同入喜用吉运 "
                   + str(len(both_good)) + " 年（占比" + str(round(ratio * 100)) + "%），同频互补 +" + str(bonus))
            if both_good:
                txt += "；约自 " + str(both_good[0]) + " 年步入同频佳期"
            notes.append(txt)
        else:
            notes.append("大运同频：双方起运区间暂无共同可评年份")
        return notes, score

    @staticmethod
    def _fmt_wx(wc):
        return " ".join("{}{:g}".format(k, v) for k, v in wc.items())

    # ---------- 主流程 ----------
    def analyze(self):
        notes_all, score_all = [], 0

        for fn in (self._year_analysis, self._day_analysis, self._wuxing_complement,
                   self._yongshen_complement, self._shensha_warning, self._dayun_sync):
            n, s = fn()
            notes_all += n
            score_all += s

        score = max(0, min(100, 60 + score_all))
        if score >= 85:
            verdict = "上等婚配：总体相合，多主和美。"
        elif score >= 70:
            verdict = "中上婚配：较为相配，注意个别矛盾处磨合。"
        elif score >= 55:
            verdict = "中等婚配：有合有冲，关键在经营与包容。"
        else:
            verdict = "普通婚配：冲刑较多，若结缘需谨慎经营、多行补救。"
        notes_all.append("综合评定：" + str(score) + " 分 —— " + verdict)

        return {
            "male": self._person_summary(self.male, "男"),
            "female": self._person_summary(self.female, "女"),
            "items": notes_all,
            "score": score,
            "verdict": verdict,
            "render": self._render(notes_all, score, verdict),
        }

    def _person_summary(self, a, tag):
        p = a["pillars"]
        gz = [p[k]["gz"] for k in ["Year", "Month", "Day", "Hour"]]
        day_gan = p["Day"]["gan"]
        return {
            "tag": tag,
            "gz": gz,
            "day_master": day_gan,
            "day_master_wx": WUXING[day_gan],
            "nayin_year": HehunEngine._nayin(p["Year"]["gz"]),
            "shengxiao": SHENGXIAO[p["Year"]["zhi"]],
            "pillars": p,
            "yun": a["yun"],
            "yongshen": HehunEngine._yongshen(a),
            "shensha": HehunEngine._person_shensha(a),
        }

    # ---------- 渲染 ----------
    def _person_block(self, analyzed, tag):
        p = analyzed["pillars"]
        keys = ["Year", "Month", "Day", "Hour"]
        lines = [tag + "命  " + " ".join(p[k]["gz"] for k in keys) +
                 "  日主" + p["Day"]["gan"] + "(" + WUXING[p["Day"]["gan"]] + ")"]
        lines.append("      年命 " + self._nayin(p["Year"]["gz"]) +
                     "  生肖 " + SHENGXIAO[p["Year"]["zhi"]])
        shishen = [p[k]["shishen"] for k in keys]
        lines.append("      十神 " + " ".join("{:^2}".format(s) for s in shishen))
        hid = ["".join(h["gan"] for h in p[k]["hidden"]) for k in keys]
        lines.append("      藏干 " + " ".join("{:^2}".format(h) for h in hid))
        ss = HehunEngine._person_shensha(analyzed)
        lines.append("      神煞 " + ("、".join(s["name"] + "@" + s["at"] for s in ss) if ss else "无明显婚姻神煞"))
        us = HehunEngine._yongshen(analyzed)
        lines.append("      喜用 " + us["reason"])
        yun = analyzed["yun"]
        lines.append("      起运 " + yun["start_desc"] + "（" + yun["start_time"][:10] + "）")
        dy = " ".join(d["pillar"] + "(" + str(d["start_age"]) + ")" for d in yun["da_yun"][:8])
        lines.append("      大运 " + dy)
        return "\n".join(lines)

    def _render(self, notes, score, verdict):
        lines = []
        lines.append("八字合婚排盘（完整版）")
        lines.append("-" * 56)
        lines.append(self._person_block(self.male, "男"))
        lines.append(self._person_block(self.female, "女"))
        lines.append("-" * 56)
        lines.append("综合评分: " + str(score) + "/100")
        lines.append("结论: " + verdict)
        lines.append("-" * 56)
        lines.extend("  - " + n for n in notes)
        lines.append("-" * 56)
        lines.append("注：合婚评分供传统文化参考，不构成婚恋决策建议。")
        return "\n".join(lines)
