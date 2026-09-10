# -*- coding: utf-8 -*-
"""八字排盘引擎（口径对照 权威在线排盘参考站点）。

关键口径（2026-09-12 经 权威在线排盘 20+ 临界点实测确认）：
1. 年柱/月柱：按输入时间（北京时间/标准时）判节气换柱，与出生地经度无关。
   因此月柱换月、年柱立春换年均以"输入钟表时间"为基准。
2. 日柱：默认（zty=1 真太阳时）以真太阳时的公历日期为准；
   真太阳时 >= 23:00 视为晚子时，日柱顺延一日（与 权威排盘 sect=2 语义一致）。
   zty=0（不用真太阳时）则日柱直接按输入时间。
3. 时柱：zty=1 时按真太阳时时刻定地支时辰，时干由最终日干五鼠遁；
   zty=0 时按输入时刻。
4. 大运/起运：基于输入时间（北京时间）的节气与性别推算。

用法：
  BaziEngine(dt, sex, longitude=120.0, use_true_solar=True)
  dt: datetime（按北京时间解释）；sex: 1男 0女；longitude: 出生地经度
"""
from datetime import datetime, timedelta

from lunar_python import Solar
from lunar_python.util import LunarUtil

from .calendar import get_true_solar_time
from .utils import TIANGAN, DIZHI, HIDDEN_GANS, get_shishen, SHISHEN


def _wushun_start(day_gan):
    """五鼠遁：日干 -> 子时天干（甲己起甲子、乙庚起丙子、丙辛起戊子、丁壬起庚子、戊癸起壬子）。"""
    return TIANGAN[(TIANGAN.index(day_gan) % 5) * 2]


def _hour_zhi_index(hour_float):
    """按时刻(小时, 可含小数)定时辰地支序(0=子,1=丑,...)。23:00-1:00 为子时。"""
    h = hour_float
    if h >= 23 or h < 1:
        return 0
    return int((h - 1) // 2 + 1)


def _shi_gan_for(day_gan, zhi_idx):
    """由日干与时辰地支序推时干。"""
    start = _wushun_start(day_gan)
    return TIANGAN[(TIANGAN.index(start) + zhi_idx) % 10]


class BaziEngine:
    """八字排盘引擎（四柱 + 十神 + 藏干 + 纳音 + 大运）。"""

    def __init__(self, dt, sex, longitude=120.0, use_true_solar=True):
        """
        dt: 输入公历时间 datetime（解释为北京时间/出生地钟表时间）
        sex: 1 男(乾) 0 女(坤)
        longitude: 出生地经度（真太阳时校正用）
        use_true_solar: True=日/时柱用真太阳时(zty=1, 默认)；
                        False=全部按输入时间(zty=0)
        """
        self.dt = dt
        self.sex = sex
        self.longitude = float(longitude)
        self.use_true_solar = use_true_solar

        # 基准（北京时间）Solar/Lunar/EightChar：年柱、月柱、大运由此来
        self.solar_bj = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        self.lunar_bj = self.solar_bj.getLunar()
        self.ec_bj = self.lunar_bj.getEightChar()

        # 真太阳时（若启用）
        if use_true_solar:
            self.true_dt = get_true_solar_time(dt, self.longitude)
        else:
            self.true_dt = dt

        # 组装四柱（同时获得日柱基准公历日期，供农历显示一致）
        self.pillars_gz, self.day_base_date = self._resolve_pillars()

    # ---------- 四柱解析 ----------
    def _resolve_pillars(self):
        """按 权威排盘 口径解析 (年, 月, 日, 时) 四柱干支。"""
        # 年/月柱：输入时间(北京时间) 节气感知
        year_gz = self.ec_bj.getYear()
        month_gz = self.ec_bj.getMonth()

        base_date = datetime(dt.year, dt.month, dt.day) if False else None  # 占位
        if not self.use_true_solar:
            # zty=0：全部按输入时间
            ec = self.ec_bj
            day_gz = ec.getDay()
            hour_gz = ec.getTime()
            base_date = datetime(self.dt.year, self.dt.month, self.dt.day)
        else:
            # 日柱：以真太阳时公历日期为基准，真太阳时 >= 23:00 顺延一日
            ts = self.true_dt
            ts_h = ts.hour + ts.minute / 60.0 + ts.second / 3600.0
            base_date = datetime(ts.year, ts.month, ts.day)
            if ts_h >= 23:
                base_date = base_date + timedelta(days=1)
            day_gz = Solar.fromYmdHms(base_date.year, base_date.month, base_date.day, 12, 0, 0) \
                .getLunar().getDayInGanZhi()
            # 时柱：真太阳时时辰 + 五鼠遁
            zi = _hour_zhi_index(ts_h)
            hour_gz = _shi_gan_for(day_gz[0], zi) + DIZHI[zi]

        return {"Year": year_gz, "Month": month_gz, "Day": day_gz, "Hour": hour_gz}, base_date

    # ---------- 单柱详情 ----------
    def _pillar_detail(self, key, gz):
        gan, zhi = gz[0], gz[1]
        day_gan = self.pillars_gz["Day"][0]
        hidden = []
        for hg in HIDDEN_GANS[zhi]:
            hidden.append({"gan": hg, "shishen": get_shishen(day_gan, hg)})
        return {
            "gan": gan,
            "zhi": zhi,
            "gz": gz,
            "shishen": "日主" if key == "Day" else get_shishen(day_gan, gan),
            "nayin": LunarUtil.NAYIN.get(gz, ""),
            "hidden": hidden,
        }

    def get_all_pillars(self):
        return {k: self._pillar_detail(k, gz) for k, gz in self.pillars_gz.items()}

    # ---------- 大运 ----------
    def get_precise_da_yun(self):
        yun = self.ec_bj.getYun(self.sex)
        start_solar = yun.getStartSolar()

        da_yun_list = []
        dys = yun.getDaYun()
        for i in range(1, min(11, len(dys))):
            dy = dys[i]
            da_yun_list.append({
                "index": i,
                "pillar": dy.getGanZhi(),
                "start_age": dy.getStartAge(),
                "start_year": dy.getStartYear(),
                "end_year": dy.getEndYear(),
            })
        return {
            "start_time": f"{start_solar.toYmdHms()}",
            "start_desc": f"{yun.getStartYear()}年{yun.getStartMonth()}个月{yun.getStartDay()}天起运",
            "da_yun": da_yun_list,
        }

    # ---------- 渲染 ----------
    def render_table(self):
        p = self.get_all_pillars()

        lines = []
        lines.append(f"八字排盘 [{ '乾' if self.sex == 1 else '坤' }造]")
        lines.append(f"公历: {self.solar_bj.toYmdHms()}")
        # 农历随日柱基准日期显示（晚子时换日后保持一致）
        bd = self.day_base_date
        lunar_show = Solar.fromYmdHms(bd.year, bd.month, bd.day, 12, 0, 0).getLunar()
        lines.append(f"农历: {lunar_show.toString()}")
        if self.use_true_solar:
            lines.append(f"真太阳时: {self.true_dt.strftime('%Y-%m-%d %H:%M:%S')} (经度 {self.longitude}°)")
        lines.append("-" * 42)

        headers = ["      ", "年柱", "月柱", "日柱", "时柱"]
        rows = [
            ["十神", p["Year"]["shishen"], p["Month"]["shishen"], "日主", p["Hour"]["shishen"]],
            ["天干", p["Year"]["gan"], p["Month"]["gan"], p["Day"]["gan"], p["Hour"]["gan"]],
            ["地支", p["Year"]["zhi"], p["Month"]["zhi"], p["Day"]["zhi"], p["Hour"]["zhi"]],
            ["纳音", p["Year"]["nayin"][:2], p["Month"]["nayin"][:2], p["Day"]["nayin"][:2], p["Hour"]["nayin"][:2]],
        ]
        lines.append("  ".join(f"{h:^6}" for h in headers))
        for row in rows:
            lines.append("  ".join(f"{item:^6}" for item in row))
        lines.append("-" * 42)

        hidden_row = ["藏干"]
        for key in ["Year", "Month", "Day", "Hour"]:
            hidden_row.append("".join(h["gan"] for h in p[key]["hidden"]))
        lines.append("  ".join(f"{item:^6}" for item in hidden_row))
        lines.append("-" * 42)

        yun_data = self.get_precise_da_yun()
        lines.append(f"起运: {yun_data['start_desc']}")
        lines.append(f"时间: {yun_data['start_time']}")
        dy_line = "大运: "
        for dy in yun_data["da_yun"][:8]:
            dy_line += f"{dy['pillar']}({dy['start_age']}) "
        lines.append(dy_line)
        return "\n".join(lines)

    def analyze(self):
        return {
            "summary": self.render_table(),
            "pillars": self.get_all_pillars(),
            "yun": self.get_precise_da_yun(),
            "true_solar_time": self.true_dt.strftime("%Y-%m-%d %H:%M:%S"),
        }
