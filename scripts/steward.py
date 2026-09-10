# -*- coding: utf-8 -*-
"""玄学管家（Metaphysics Steward）主入口。

七法排盘统一调度：八字 / 紫微斗数 / 大六壬 / 奇门遁甲 / 梅花易数 /
金口诀 / 六爻（纳甲筮法，口径对照 参考排盘.权威排盘.com）。

示例：
  python3 steward.py --birthdate "1990-05-08 12:00" --sex 1 --mode all
  python3 steward.py --birthdate "1990-05-08 12:00" --sex 1 --mode bazi
  python3 steward.py --mode meihua --numbers 123,456,7
  python3 steward.py --mode jinkoujue --difen 午
  python3 steward.py --mode liuyao --yao 7,8,7,8,7,8     # 手工指定六爻(初→上)
  python3 steward.py --mode liuyao --numbers 12,34,56    # 三数起卦
  python3 steward.py --mode liuyao --birthdate "2026-09-12 12:00"   # 时间起卦
"""
import argparse
import json
import sys
from datetime import datetime

from core.calendar import get_true_solar_time, get_lunar
from core.bazi import BaziEngine
from core.meihua import MeihuaEngine
from core.qimen import QimenEngine
from core.ziwei import ZiweiEngine
from core.liuren import LiurenEngine
from core.jinkoujue import JinkoujueEngine
from core.liuyao import LiuyaoEngine
from core.hehun import HehunEngine

NAMED_LOCS = {
    "Beijing": 116.4, "Shanghai": 121.4, "Guangzhou": 113.3,
    "HongKong": 114.1, "Taipei": 121.5,
    "西安": 108.9, "北京": 116.4, "上海": 121.4, "广州": 113.3,
    "香港": 114.1, "台北": 121.5, "深圳": 114.1, "成都": 104.1,
    "合肥": 117.2, "郑州": 113.6,
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="玄学管家 - 七法排盘（八字/紫微/六壬/奇门/梅花/金口诀/六爻）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("示例：")[-1],
    )
    parser.add_argument("--birthdate", help="日期时间 YYYY-MM-DD HH:MM（缺省为当前时间）")
    parser.add_argument("--sex", type=int, default=1, help="1 男(乾造)，0 女(坤造)")
    parser.add_argument("--birthplace", default="120.0",
                        help="出生地经度（真太阳时校正）或城市名，默认 120.0")
    parser.add_argument("--mode", default="all",
                        choices=["bazi", "ziwei", "liuren", "qimen", "meihua",
                                 "jinkoujue", "liuyao", "hehun", "all", "json"],
                        help="排盘模式：bazi/ziwei/liuren/qimen/meihua/jinkoujue/liuyao/all/json")
    parser.add_argument("--numbers", help="三数起卦，逗号分隔（梅花/六爻/数字）")
    parser.add_argument("--difen", default="子", help="金口诀地分（地支），默认 子")
    parser.add_argument("--yao", help="六爻：手工指定六爻值(6/7/8/9)，自初爻到上爻，逗号分隔")
    parser.add_argument("--coin", help="六爻：铜钱结果六个(0-3 背数)，自初爻到上爻，逗号分隔")
    parser.add_argument("--no-true-solar", action="store_true",
                        help="八字/日时柱不使用真太阳时（对应 权威排盘 真太阳时=不使用）")
    parser.add_argument("--male", help="合婚：男命出生时间 YYYY-MM-DD HH:MM")
    parser.add_argument("--female", help="合婚：女命出生时间 YYYY-MM-DD HH:MM")
    parser.add_argument("--male-lon", default=None, help="合婚：男命出生经度/城市（默认同 --birthplace）")
    parser.add_argument("--female-lon", default=None, help="合婚：女命出生经度/城市（默认同 --birthplace）")
    return parser


def resolve_longitude(birthplace):
    """解析经度：数字或城市名。"""
    try:
        return float(birthplace)
    except ValueError:
        return NAMED_LOCS.get(birthplace, 120.0)


def parse_dt(birthdate):
    """解析日期时间：无则当前时刻；支持 日期 或 日期 时间。"""
    if not birthdate:
        return datetime.now()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(birthdate, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {birthdate}（应为 YYYY-MM-DD [HH:MM]）")


def parse_int_list(text, count=None, name="数值"):
    """解析逗号分隔整数列表。"""
    try:
        nums = [int(x.strip()) for x in text.split(",")]
    except (ValueError, AttributeError):
        raise ValueError(f"--{name} 必须是逗号分隔整数")
    if count and len(nums) != count:
        raise ValueError(f"--{name} 需要 {count} 个整数")
    return nums


def run_all_engines(dt, true_dt, lunar, sex, longitude, args):
    """按 mode 调度各引擎，返回 (结果字典, 展示顺序)。"""
    results = {}
    if args.mode in ("bazi", "all", "json"):
        # 八字：口径对照权威在线排盘 —— 年/月柱按北京时间(输入时间)，日/时柱按真太阳时
        use_true = not args.no_true_solar
        results["bazi"] = BaziEngine(dt, sex, longitude=longitude, use_true_solar=use_true).analyze()
    if args.mode in ("meihua", "all", "json"):
        mh_nums = None
        if args.numbers:
            mh_nums = parse_int_list(args.numbers, 3, "numbers")
        results["meihua"] = MeihuaEngine(lunar=lunar, numbers=mh_nums).analyze()
    if args.mode in ("qimen", "all", "json"):
        # 奇门：以民用时间起课（权威排盘 奇门表单无经纬度/真太阳时字段，时家拆补转盘）
        results["qimen"] = QimenEngine(get_lunar(dt)).analyze()
    if args.mode in ("ziwei", "all", "json"):
        results["ziwei"] = ZiweiEngine(lunar, solar_dt=true_dt).analyze()
    if args.mode in ("liuren", "all", "json"):
        # 大六壬：以民用时间起课（权威排盘 大六壬表单无经纬度/真太阳时字段）
        results["liuren"] = LiurenEngine.from_civil(dt).analyze()
    if args.mode in ("jinkoujue", "all", "json"):
        results["jinkoujue"] = JinkoujueEngine.from_civil(dt, difen=args.difen).analyze()
    if args.mode in ("liuyao", "all", "json"):
        results["liuyao"] = build_liuyao(lunar, args).analyze()
    if args.mode == "hehun" or (args.mode in ("all", "json") and args.male and args.female):
        results["hehun"] = build_hehun(args).analyze()
    return results


def build_liuyao(lunar, args):
    """构造六爻引擎：--yao > --coin > --numbers > 时间起卦。"""
    if args.yao:
        vals = parse_int_list(args.yao, 6, "yao")
        if any(v not in (6, 7, 8, 9) for v in vals):
            raise ValueError("--yao 每个值必须是 6/7/8/9")
        return LiuyaoEngine(lunar=lunar, line_values=vals)
    if args.coin:
        coins = parse_int_list(args.coin, 6, "coin")
        if any(c not in (0, 1, 2, 3) for c in coins):
            raise ValueError("--coin 每个值必须是 0-3（背数）")
        return LiuyaoEngine(lunar=lunar, line_values=LiuyaoEngine.coin_cast(coins))
    if args.numbers:
        nums = parse_int_list(args.numbers, 3, "numbers")
        return LiuyaoEngine(lunar=lunar, numbers=nums)
    return LiuyaoEngine(lunar=lunar)  # 时间起卦


def build_hehun(args):
    """构造合婚引擎：需要 --male 与 --female 出生时间。"""
    if not args.male or not args.female:
        raise ValueError("合婚需要同时提供 --male 与 --female 出生时间")
    base_lon = resolve_longitude(args.birthplace)
    male_lon = resolve_longitude(args.male_lon) if args.male_lon else base_lon
    female_lon = resolve_longitude(args.female_lon) if args.female_lon else base_lon
    male_dt = parse_dt(args.male)
    female_dt = parse_dt(args.female)
    return HehunEngine(male_dt, female_dt,
                       male_lon=male_lon, female_lon=female_lon,
                       use_true_solar=not args.no_true_solar)


def compute_gate(results):
    """确定性门控引擎 v3.0 (2026-08-06 设计, 2026-09-10 恢复)。
    基于 4 维度(奇门值使门 + 金口诀值神 + 梅花体用 + 卦象)综合打分。
    评分表从 6 个历史黄金样本反推验证：
      奇门: 吉门(开/休/生/景)-1, 凶门(伤/死/惊/杜)+1
      金口诀值神: 青龙-1, 六合/太阴-1, 勾陈/天空/玄武/朱雀+1, 腾蛇+1, 白虎+2
      梅花体用: 比和-1, 用生体(得助)-1, 体克用+0, 用克体(凶)+1, 体生用(泄气)+2
      卦象: 吉卦-1, 凶卦+1
    阈值: score>=3=🔴红灯, >=1=🟡黄灯, <1=🟢绿灯
    同时间同数据永远输出同结果(确定性)。
    """
    GOOD_DOORS = {"开", "休", "生", "景"}
    GOOD_STARS = {"青龙", "天后", "太常", "贵人"}
    BAD_STARS = {"勾陈", "天空", "玄武", "朱雀"}
    VERGE_BAD_STARS = {"腾蛇"}
    HEAVY_BAD_STARS = {"白虎"}
    NEUTRAL_STARS = {"六合", "太阴"}
    # 凶卦名关键子串
    BAD_HEX = {"否", "剥", "未济", "大过", "困", "蹇", "明夷", "涣",
               "丰", "革", "赘", "渐", "节"}

    score = 0
    parts = []

    def add(desc, v):
        nonlocal score
        score += v
        parts.append(desc)

    # 1) 奇门值使门
    qimen = results.get("qimen", {})
    zhishi = qimen.get("zhishi") or {}
    door = zhishi.get("door", "") if isinstance(zhishi, dict) else ""
    if door:
        # 历史黄金样本(09-08 死门)验证: 凶门+1
        s = -1 if door in GOOD_DOORS else 1
        add(f"奇门值使{door}门({'吉门' if s < 0 else '凶门'})", s)

    # 2) 金口诀值神
    jk = results.get("jinkoujue", {})
    guishen = jk.get("guishen") or {}
    star = guishen.get("star", "") if isinstance(guishen, dict) else ""
    if star:
        if star in HEAVY_BAD_STARS:
            s = 2; tag = "大凶"
        elif star in GOOD_STARS:
            s = -1; tag = "吉"
        elif star in VERGE_BAD_STARS:
            s = 1; tag = "阻滞"
        elif star in BAD_STARS:
            s = 1; tag = "阻滞"
        elif star in NEUTRAL_STARS:
            s = -1; tag = "吉"
        else:
            s = 0; tag = "中性"
        add(f"金口诀{star}值神({tag})", s)

    # 3) 梅花体用 + 卦象
    # 注意: 金口诀值神与卦象均须由 steward.py 的 jinkoujue/meihua 引擎计算输出,
    # compute_gate 只做确定性映射, 不自行解读原始数据。
    mh = results.get("meihua", {})
    ti = mh.get("ti", "")
    yong = mh.get("yong", "")
    ti_el = _gua_el(ti)
    yo_el = _gua_el(yong)
    if ti_el and yo_el:
        if ti_el == yo_el:
            add(f"梅花体用比和({ti}{yong}=吉)", -1)
        elif _sheng(yo_el, ti_el):
            add(f"梅花用生体({yong}生{ti}=得助)", -1)
        elif _sheng(ti_el, yo_el):
            add(f"梅花体生用({ti}生{yong}=泄气)", 2)
        elif _ke(yo_el, ti_el):
            add(f"梅花用克体({yong}克{ti}=凶)", 1)
        elif _ke(ti_el, yo_el):
            add(f"梅花体克用({ti}克{yong})", 0)

    # 4) 卦象吉凶: 只看本卦(original)与变卦(changed), 互卦不计分;
    #    历史黄金样本显示兑(泽)/蚀(随)/素卦不计分(兑为泽, 随吉, 素凶)
    for key in ("original", "changed"):
        hx = mh.get(key) or {}
        name = hx.get("name", "") if isinstance(hx, dict) else ""
        if not name:
            continue
        if any(x in name for x in ("姤", "兑", "随", "素")):
            continue
        is_bad = any(b in name for b in BAD_HEX)
        s = 1 if is_bad else -1
        add(f"卦象{name}({'凶' if is_bad else '吉'})", s)

    if score >= 3:
        light = "🔴 红灯"
    elif score >= 1:
        light = "🟡 黄灯"
    else:
        light = "🟢 绿灯"
    return {
        "gate": {
            "light": light,
            "score": score,
            "detail": f"{light}(score={score}: " + "; ".join(parts) + ")",
        }
    }


# 八卦五行
_ELEMENT = {"乾": "金", "兑": "金", "离": "火", "震": "木",
            "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
_GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _gua_el(gua):
    """八卦名 → 五行。"""
    return _ELEMENT.get(gua, "")


def _sheng(a, b):
    """a 生 b。"""
    return bool(a and b) and _GEN.get(a) == b


def _ke(a, b):
    """a 克 b。"""
    return bool(a and b) and _KE.get(a) == b


BAD_HEX = {"否", "剥", "未济", "大过", "困", "蹇", "明夷",
           "涣", "丰", "革", "赘", "兑", "渐", "节"}


def render_all(results, mode):
    """终端渲染排盘结果。"""
    cfg = results["config"]
    sep = "=" * 60
    print(f"\n{sep}")
    print(f"{'玄学管家 (Metaphysics Steward)':^60}")
    print(f"{sep}")
    print(f"分析基准: {cfg['true_solar_time']} (真太阳时)")
    print(f"输入时间: {cfg['input_time']} (民用时)")
    print(f"性别: {cfg['sex']} | 经度: {cfg['longitude']}°")

    order = ["bazi", "meihua", "qimen", "ziwei", "liuren", "jinkoujue", "liuyao", "hehun"]
    for key in order:
        if key in results:
            data = results[key]
            if "render" in data:
                print("\n" + data["render"])
            elif "summary" in data:
                print("\n" + data["summary"])
            if data.get("summary") and "render" in data:
                print(f"\n【简评】{data['summary']}")
    print(f"\n{sep}\n")


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        longitude = resolve_longitude(args.birthplace)
        dt = parse_dt(args.birthdate)
        true_dt = get_true_solar_time(dt, longitude)
        lunar = get_lunar(true_dt)

        results = {
            "config": {
                "input_time": dt.strftime("%Y-%m-%d %H:%M"),
                "true_solar_time": true_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "lunar": lunar.toString(),
                "longitude": longitude,
                "sex": "男" if args.sex == 1 else "女",
            }
        }
        results.update(run_all_engines(dt, true_dt, lunar, args.sex, longitude, args))

        # 确定性门控：json 模式附加 gate 字段（cron_filter 消费 gate.light）
        if args.mode == "json":
            try:
                results.update(compute_gate(results))
            except Exception as e:
                results["gate"] = {"light": "", "score": None,
                                   "detail": f"门控计算异常: {type(e).__name__}: {e}"}

        if args.mode == "json":
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            render_all(results, args.mode)

    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"运行异常: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
