# -*- coding: utf-8 -*-
"""大六壬排盘引擎（口径对照 权威在线排盘参考站点）。

关键口径（2026-09-12 经 权威在线排盘实测收敛：12 日辰 x 12 占时 =
144 行语料全量校验 + 3 条中气边界/晚子探针，见
实测口径）：
1. 全部以民用时间（东八区钟表时间）起课———大六壬表单无经纬度/真太阳时字段。
2. 晚子时换日：钟表时刻 >= 23:00 日干支顺延一日（与八字/紫微口径一致），占时=子时。
3. 月将按「中气换将」：取最近中气定将（大寒→子、雨水→亥、春分→戌、谷雨→酉、
   小满→申、夏至→未、大暑→午、处暑→巳、秋分→辰、霜降→卯、小雪→寅、冬至→丑）。
4. 天盘：月将加占时，天盘支 = (地盘支 + 月将 - 占时) mod 12。
5. 四课：干上（日干寄宫上神）/干阴/支上/支阴；判贼克时一课下位取日干本气五行
   （乙木克辰土、癸水被丑土克 等以干五行为准，非寄宫五行）。
6. 三传九宗门（实测口径）：
   - 伏吟（月将=占时）：四课有克（仅乙/癸日一课上神）取之发用；无克则阳日干上神、
     阴日支上神为初传；中末递三刑（初刑为中、中刑为末）；初传自刑（辰午酉亥）则
     中取另一上神（初发用于干→中支上，初发用于支→中干上）；中又自刑则末取冲。
   - 返吟（offset=6）：有克走常法贼克/比用/涉害；无克（六阴丑未日）为井栏射——
     初传取日支驿马，中传支上神，末传干上神。
   - 常法：下贼上优先于上克下；仅一处即用；多处则比用（上神与日干同阴阳）；
     俱比/俱不比则涉害（不比重克深浅，按上神所临地盘支——K1 之临位为
     日干寄宫支——的孟仲季取浅者：孟=0 级/仲=1 级/季=2 级取最小；平级取阳日干
     上神/阴日支上神，再按课序）。
   - 无贼克：日干寄宫==日支 → 八专（阳日干上神连本位顺数三神，阴日四课上神连本位
     逆数三神；中末皆干上神）。否则遥克——蒿矢（天盘神克日干）先判：候选恰一即用（不论阴阳）；多候选取
     与日干同阴阳之上神支（阳日阳支/阴日阴支）第一个，俱不比则整类弃用转弹射
     （日干克天盘神）对称重试；两类皆无用方落别责/昴星。
     否则四课不全（<4 组）→ 别责（阳日取日干合干寄宫上神，阴日取日支三合前一位；
     中末皆干上神）。否则昴星（阳日仰视酉位之上神，中=支上末=干上；阴日俯视天盘酉
     所临之地盘，中=干上末=支上）。
7. 遁干/空亡：日干支所在旬内配干；旬空之支在三传无遁干并标注「空」。
8. 六亲：按传支五行对日干定（生我=父、我生=子、克我=官、我克=财、同类=比）。
9. 天将：贵人乘天盘贵神支——甲戊庚 昼丑/夜未，乙己 昼子/夜申，丙丁 昼亥/夜酉，
   壬癸 昼巳/夜卯，辛 昼午/夜寅；昼夜按占时（卯~申昼、酉~寅夜）。贵神天盘所临地盘
   P=（贵神支-月将+占时）在 亥子丑寅卯辰 则顺布（沿天盘 贵蛇雀合勾龙空虎常玄阴后），
   在 巳午未申酉戌 则逆布。

用法：
  LiurenEngine(lunar, civil_dt=None).analyze()
  LiurenEngine.from_civil(dt)   # dt 为东八区民用 datetime
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
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # x 生 SHENG[x]
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}  # x 克 KE[x]
# 日干寄宫
LODGE = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳", "己": "未",
         "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}
# 贵神表: 干 -> (昼贵, 夜贵)
GUI = {"甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
       "乙": ("子", "申"), "己": ("子", "申"),
       "丙": ("亥", "酉"), "丁": ("亥", "酉"),
       "壬": ("巳", "卯"), "癸": ("巳", "卯"),
       "辛": ("午", "寅")}
GODS = ["贵", "蛇", "雀", "合", "勾", "龙", "空", "虎", "常", "玄", "阴", "后"]
# 三刑（单向环）：寅刑巳、巳刑申、申刑寅；丑刑戌、戌刑未、未刑丑；子刑卯、卯刑子
XING = {2: 5, 5: 8, 8: 2, 1: 10, 10: 7, 7: 1, 0: 3, 3: 0, 4: 4, 6: 6, 9: 9, 11: 11}
SELF_XING = {4, 6, 9, 11}  # 辰午酉亥
CHONG = {0: 6, 1: 7, 2: 8, 3: 9, 4: 10, 5: 11, 6: 0, 7: 1, 8: 2, 9: 3, 10: 4, 11: 5}
# 驿马: 日支 -> 马支idx
MA = {8: 2, 0: 2, 4: 2, 2: 8, 6: 8, 10: 8, 5: 11, 9: 11, 1: 11, 11: 5, 3: 5, 7: 5}
# 中气换将
QI_JIANG = [("大寒", "子"), ("雨水", "亥"), ("春分", "戌"), ("谷雨", "酉"), ("小满", "申"),
            ("夏至", "未"), ("大暑", "午"), ("处暑", "巳"), ("秋分", "辰"), ("霜降", "卯"),
            ("小雪", "寅"), ("冬至", "丑")]


def _hour_zhi_idx(h):
    if h >= 23 or h < 1:
        return 0
    return int((h + 1) // 2) % 12


def _shi_gan(day_gan, zhi_idx):
    start = TIANGAN[(TIANGAN.index(day_gan) % 5) * 2]
    return TIANGAN[(TIANGAN.index(start) + zhi_idx) % 10]


def _xun(day_gan, day_zhi):
    """日干支所在旬: 返回 (旬首支idx, 空亡两支idx)。"""
    head = (DIZHI.index(day_zhi) - TIANGAN.index(day_gan)) % 12
    return head, [(head + 10) % 12, (head + 11) % 12]


class LiurenEngine:
    """大六壬排盘引擎（九宗门 + 天将 + 遁干/空亡，口径对照权威在线排盘）。"""

    def __init__(self, lunar, civil_dt=None):
        self.lunar = lunar
        self.civil_dt = civil_dt
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
        self.hour_gan = _shi_gan(self.day_gan, self.hour_zhi_idx)
        self.yue_jiang = self._yue_jiang()
        self.offset = (DIZHI.index(self.yue_jiang) - self.hour_zhi_idx) % 12
        self.kong = [DIZHI[x] for x in _xun(self.day_gan, self.day_zhi)[1]]
        self.gui_zhi = self._gui_zhi()

    @classmethod
    def from_civil(cls, dt):
        return cls(get_lunar(dt), civil_dt=dt)

    # ---------- 基础 ----------
    def _yue_jiang(self):
        qi = self.lunar.getPrevQi()
        name = qi.getName() if hasattr(qi, "getName") else qi
        for qn, jiang in QI_JIANG:
            if qn == name:
                return jiang
        raise ValueError(f"未知中气: {name}")

    def _gui_zhi(self):
        day = self.hour_zhi_idx in (3, 4, 5, 6, 7, 8)  # 卯~申 昼
        return GUI[self.day_gan][0] if day else GUI[self.day_gan][1]

    def heaven(self, earth_idx):
        return (earth_idx + self.offset) % 12

    def four_courses(self):
        """4 课: (上神支idx, 下神idx/None, 下为日干?) 一课下为日干。"""
        up1 = self.heaven(DIZHI.index(LODGE[self.day_gan]))
        up2 = self.heaven(up1)
        up3 = self.heaven(DIZHI.index(self.day_zhi))
        up4 = self.heaven(up3)
        return [(up1, None, True), (up2, up1, False), (up3, DIZHI.index(self.day_zhi), False),
                (up4, up3, False)]

    def _up_elem(self, c):
        return ZHI_ELEM[DIZHI[c[0]]]

    def _down_elem(self, c):
        if c[2]:
            return GAN_ELEM[self.day_gan]
        return ZHI_ELEM[DIZHI[c[1]]]

    def _controls(self, a, b):
        """a 五行 克 b 五行。"""
        return KE.get(a) == b

    # ---------- 天将 ----------
    def god_of(self, zhi_idx):
        """天盘支 zhi_idx 所乘天将单字（贵蛇雀合勾龙空虎常玄阴后）。"""
        E = DIZHI.index(self.gui_zhi)
        P = (E - self.offset) % 12  # 贵神天盘所临地盘位
        if P in (11, 0, 1, 2, 3, 4):  # 亥子丑寅卯辰 -> 顺布
            k = (zhi_idx - E) % 12
        else:                         # 巳午未申酉戌 -> 逆布
            k = (E - zhi_idx) % 12
        return GODS[k]

    # ---------- 孟仲季 ----------
    @staticmethod
    def _mzj(down_idx):
        if down_idx in (2, 8, 5, 11):
            return 0  # 孟
        if down_idx in (0, 6, 3, 9):
            return 1  # 仲
        return 2      # 季

    # ---------- 三传解析 ----------
    def _kede_hits(self, courses, zei):
        hits = []
        for i, c in enumerate(courses):
            ue, de = self._up_elem(c), self._down_elem(c)
            if zei and self._controls(de, ue):
                hits.append(i)
            elif not zei and self._controls(ue, de):
                hits.append(i)
        return hits

    def _resolve(self, courses):
        yang = TIANGAN.index(self.day_gan) % 2 == 0
        if self.offset == 0:
            return self._fuyin(courses)
        if self.offset == 6:
            return self._fanyin(courses)
        zei = self._kede_hits(courses, True)
        ke = self._kede_hits(courses, False)
        if zei or ke:
            return self._zhaike_resolve(courses, bool(zei), yang)
        # 八专
        if LODGE[self.day_gan] == self.day_zhi:
            first = (courses[0][0] + 2) % 12 if yang else (courses[3][0] + 10) % 12
            mid = last = courses[0][0]
            return "八专", first, mid, last
        # 遥克：蒿矢(神克日) 先于 弹射(日克神)。
        # 候选恰一即用（不论阴阳）；多候选取与日干同阴阳之上神支（阳日阳支/阴日
        # 阴支）的第一个；俱不比则整类弃用，转另一类对称重试；两类皆无用方落
        # 别责/昴星。
        de = GAN_ELEM[self.day_gan]
        want = 0 if yang else 1  # 阳日取阳支(偶idx)/阴日取阴支(奇idx)

        def _pick_one(cands):
            if len(cands) == 1:
                return cands[0]
            for c in cands:
                if c[0] % 2 == want:
                    return c
            return None

        cand_hs = [c for c in courses if self._controls(ZHI_ELEM[DIZHI[c[0]]], de)]
        picked = _pick_one(cand_hs)
        if picked is None:
            cand_ts = [c for c in courses if self._controls(de, ZHI_ELEM[DIZHI[c[0]]])]
            picked = _pick_one(cand_ts)
        if picked is not None:
            return "遥克", picked[0], self.heaven(picked[0]), self.heaven(self.heaven(picked[0]))
        # 别责：四课不全
        distinct = {(c[0], (c[1] if not c[2] else None)) for c in courses}
        if len(distinct) < 4:
            if yang:
                partner = TIANGAN[(TIANGAN.index(self.day_gan) + 5) % 10]
                first = self.heaven(DIZHI.index(LODGE[partner]))
            else:
                first = (DIZHI.index(self.day_zhi) + 4) % 12
            mid = last = courses[0][0]
            return "别责", first, mid, last
        # 昴星
        if yang:
            first = self.heaven(9)
            return "昴星", first, courses[2][0], courses[0][0]
        first = (9 - self.offset) % 12
        return "昴星", first, courses[0][0], courses[2][0]

    def _zhaike_resolve(self, courses, zei, yang):
        hits = self._kede_hits(courses, zei)
        if len(hits) == 1:
            first = courses[hits[0]][0]
            return "贼克", first, self.heaven(first), self.heaven(self.heaven(first))
        # 比用：上神与日干同阴阳
        bi = [i for i in hits if (courses[i][0] % 2) == (0 if yang else 1)]
        pool = bi if bi else hits
        if len(pool) == 1:
            first = courses[pool[0]][0]
            return "比用", first, self.heaven(first), self.heaven(self.heaven(first))
        # 涉害：不比重克深浅——按上神所临地盘支（下神位，K1 之临位为日干
        # 寄宫支）的孟仲季取浅者（孟=0 级/仲=1 级/季=2 级取最小）；平级再走下面
        # 复等课序规则。
        downs = []
        for i in pool:
            c = courses[i]
            down = DIZHI.index(LODGE[self.day_gan]) if c[2] else c[1]
            downs.append(self._mzj(down))
        best = min(downs)
        pool3 = [pool[k] for k in range(len(pool)) if downs[k] == best]
        if len(pool3) == 1:
            first = courses[pool3[0]][0]
            return "涉害", first, self.heaven(first), self.heaven(self.heaven(first))
        # 复等：阳日取干上神，阴日取支上神
        pref = courses[0][0] if yang else courses[2][0]
        for i in pool3:
            if courses[i][0] == pref:
                return "涉害", pref, self.heaven(pref), self.heaven(self.heaven(pref))
        first = courses[pool3[0]][0]
        return "涉害", first, self.heaven(first), self.heaven(self.heaven(first))

    def _fuyin(self, courses):
        """伏吟：有克取克者上神发用，无克阳干上/阴支上；中末递三刑。"""
        yang = TIANGAN.index(self.day_gan) % 2 == 0
        zei = self._kede_hits(courses, True)
        ke = self._kede_hits(courses, False)
        if zei or ke:
            first = courses[(zei or ke)[0]][0]
        else:
            first = courses[0][0] if yang else courses[2][0]
        up_gan, up_zhi = courses[0][0], courses[2][0]
        if first in SELF_XING:
            # 初自刑：发用于干 → 中取支上；发用于支 → 中取干上
            mid = up_zhi if (first == up_gan and first != up_zhi) else up_gan
        else:
            mid = XING[first]
        if mid in SELF_XING:
            last = CHONG[mid]
        else:
            last = XING[mid]
        return "伏吟", first, mid, last

    def _fanyin(self, courses):
        """返吟：有克走常法；无克井栏射（驿马发用，中=支上，末=干上）。"""
        zei = self._kede_hits(courses, True)
        ke = self._kede_hits(courses, False)
        if zei or ke:
            yang = TIANGAN.index(self.day_gan) % 2 == 0
            typ, first, mid, last = self._zhaike_resolve(courses, bool(zei), yang)
            return "返吟", first, mid, last
        first = MA[DIZHI.index(self.day_zhi)]
        return "井栏", first, courses[2][0], courses[0][0]

    # ---------- 三传标注 ----------
    def _annotate(self, zhi_idx):
        head, _ = _xun(self.day_gan, self.day_zhi)
        q = (zhi_idx - head) % 12
        kong_flag = q >= 10
        gan = "" if kong_flag else TIANGAN[q]
        zhi = DIZHI[zhi_idx]
        de = GAN_ELEM[self.day_gan]
        ze = ZHI_ELEM[zhi]
        if ze == de:
            liuqin = "比"
        elif self._controls(ze, de):
            liuqin = "官"      # 传支克日干
        elif self._controls(de, ze):
            liuqin = "财"      # 日干克传支
        elif SHENG.get(de) == ze:
            liuqin = "子"      # 日干生传支
        else:
            liuqin = "父"      # 传支生日干
        return {"zhi": zhi, "gan": gan, "kong": kong_flag, "liuqin": liuqin,
                "god": self.god_of(zhi_idx)}

    # ---------- 出口 ----------
    def analyze(self):
        courses = self.four_courses()
        typ, first, mid, last = self._resolve(courses)
        sc = [self._annotate(z) for z in (first, mid, last)]
        chuan = "".join(a["zhi"] for a in sc)
        sike = [{"up": DIZHI[c[0]],
                 "down": self.day_gan if c[2] else DIZHI[c[1]]} for c in courses]
        return {
            "summary": f"月将{self.yue_jiang}，占时{self.day_gan}{self.day_zhi}日"
                       f"{self.hour_zhi}时，空亡{self.kong[0]}{self.kong[1]}，"
                       f"三传{chuan}（{typ}）。",
            "render": self._render(typ, sc, chuan, sike),
            "day_gan": self.day_gan, "day_zhi": self.day_zhi,
            "hour_gan": self.hour_gan, "hour_zhi": self.hour_zhi,
            "year_gz": self.year_gz, "month_gz": self.month_gz,
            "yuejiang": self.yue_jiang, "zhanshi": self.hour_zhi,
            "kong": [self.kong[0], self.kong[1]],
            "type": typ, "chuan": chuan,
            "sanchuan": sc, "sike": sike,
        }

    def _render(self, typ, sc, chuan, sike):
        L = ["大六壬盘", "-" * 36]
        L.append(f"干支: {self.year_gz}年 {self.month_gz}月 {self.day_gan}{self.day_zhi}日 "
                 f"{self.hour_gan}{self.hour_zhi}时")
        L.append(f"月将: {self.yue_jiang}   占时: {self.day_gan}{self.day_zhi}日"
                 f"{self.hour_zhi}时   (空亡:{self.kong[0]}、{self.kong[1]})")
        L.append(f"课式: {typ}   三传: {chuan}")
        parts = []
        for i, tag in enumerate(["初传", "中传", "末传"]):
            a = sc[i]
            body = (a["gan"] if a["gan"] else "") + a["zhi"] + ("空" if a["kong"] else "")
            parts.append(f"{a['liuqin']} {body} {a['god']} {tag}")
        L.append("   ".join(parts))
        L.append("")
        L.append("四课:")
        ups = [x["up"] for x in sike][::-1]
        downs = [x["down"] for x in sike][::-1]
        L.append("  ".join(ups))
        L.append("  ".join(downs))
        L.append("")
        L.append("天将(乘天盘):")
        L.append(" ".join(f"{self.god_of(i)}{z}" for i, z in enumerate(DIZHI)))
        dn = "昼贵" if self.hour_zhi_idx in (3, 4, 5, 6, 7, 8) else "夜贵"
        L.append(f"贵神: {self.gui_zhi}({dn})")
        return "\n".join(L)
