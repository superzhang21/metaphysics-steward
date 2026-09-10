---
name: metaphysics-steward
description: 玄学管家——专业中文玄学排盘引擎。支持七法+合婚：八字四柱、紫微斗数、大六壬、奇门遁甲、梅花易数、金口诀、六爻纳甲、八字合婚；含真太阳时校正、天干地支历法、起卦装卦、双造合婚。八字排盘口径对照 参考排盘.权威排盘.com。
tags: [divination, bazi, ziwei, liuren, qimen, meihua, jinkoujue, liuyao, 玄学, 排盘]
---

# 玄学管家（Metaphysics Steward）

覆盖 7 种传统中式推演术数的专业排盘工具，强调天文精度与交叉验证。

## 能力清单（七法）

| 术数 | 引擎文件 | 能力 |
|---|---|---|
| 八字 Bazi | `scripts/core/bazi.py` | 四柱精确到节气时刻换柱；十神、藏干、纳音；大运起运（3日=1年）与十年大运 |
| 紫微斗数 Ziwei | `scripts/core/ziwei.py` | 12 宫与 14 主星；年系四化；五行局；宫位渲染 |
| 大六壬 Da Liuren | `scripts/core/liuren.py` | 中气定月将；四课三传九宗门全口径（贼克/比用/涉害·临位孟仲季/遥克·蒿矢先弹射/伏吟/返吟/八专/昴星）；逐传六亲·遁干·空亡·天将 |
| 奇门遁甲 Qimen | `scripts/core/qimen.py` | 3x3 九宫渲染：八神、九星、八门、天地盘；拆补法定局 |
| 梅花易数 Meihua | `scripts/core/meihua.py` | 时间起卦与数字起卦；本卦/互卦/变卦；体用 |
| 金口诀 Jinkoujue | `scripts/core/jinkoujue.py` | 人元、贵神、月将、地分四层课式 |
| **六爻 Liuyao** | `scripts/core/liuyao.py` | **铜钱/数字/时间三法起卦；定卦名定宫；安世应；纳甲；配六亲；装六神；动爻变卦** |
| **八字合婚 Hehun** | `scripts/core/hehun.py` | **双造同排；生肖六合冲害、年命纳音、日干五合、夫妻宫（日支）六合三合冲刑、五行互补；综合评分** |

## 排盘口径

- 八字/紫微/六爻以 **真太阳时**（经度 + 均时差修正）为排盘基准时刻；大六壬/金口诀/奇门
  以 **民用时间（钟表时间）** 起课——权威排盘 对应表单均无经纬度字段，实测一致。
- 节气换柱、奇门拆补、六爻装卦等口径与 权威在线排盘参考站点 一致（已 golden 锁定）。
- **民用时间三法（权威排盘实测收敛）**：
  - 大六壬：晚子 >=23:00 换日；月将按**中气**换将（大寒→子…冬至→丑）；
    涉害=按上神**临位**孟仲季取浅（非受克深度，孟0/仲1/季2 取 min）；遥克=蒿矢
    （神克日）先于弹射（日克神），单候选即用、多候选比日干阴阳、俱不比弃类转另一类；
    八专先于遥克。144 行语料全量校验。
  - 金口诀：月将按**节**换将（小寒→子…立春→亥，与六壬中气换将不同）；
    人元=五鼠遁(地分)；贵神=日干贵支（昼夜卯~申）布圈取地分位，贵支∈{亥子丑寅卯}
    顺布否则逆布，贵神支=固定座支表；将神=月将加时。216 图全量校验。
  - 奇门：时家拆补转盘（站点默认）；局窗=**最近 24 节气**（节中气均精确切换，
    勿用 lunar_python getPrevJieQi(True)——节气日 0 点即误切）；符头定三元。
- 六爻采用京房八宫纳甲：下卦取纯卦内卦三爻纳甲、上卦取纯卦外卦三爻纳甲；六亲以宫五行为体；六神以日干起例（甲乙青龙、丙丁朱雀、戊勾陈、己螣蛇、庚辛白虎、壬癸玄武）；应爻=世爻隔三位。
- **八字换柱口径（实测 权威排盘，22 组黄金案例回归通过）**：
  - 年柱/月柱：按**输入时间（北京时间）**判节气换柱，与出生地经度无关（立春换年、换节换月）。
  - 日柱：真太阳时模式下以真太阳时的公历日期为基准，真太阳时 ≥23:00 顺延一日（晚子时换日）。
  - 时柱：真太阳时模式下按真太阳时定地支、日干五鼠遁定时干。
  - `--no-true-solar` 可切换为全程按输入时间（对应 权威排盘「真太阳时=不使用」）。

## 使用

```bash
cd scripts

# 综合（八字+梅花+奇门+紫微+六壬+金口诀+六爻 时间起卦）
python3 steward.py --birthdate "1990-02-04 10:40" --sex 1 --birthplace 116.4 --mode all

# 单法
python3 steward.py --birthdate "1990-02-04 10:40" --sex 1 --mode bazi
python3 steward.py --birthdate "1990-02-04 10:40" --mode qimen
python3 steward.py --birthdate "1990-02-04 10:40" --mode ziwei
python3 steward.py --birthdate "1990-02-04 10:40" --mode liuren

# 梅花 / 六爻（数字起卦）
python3 steward.py --mode meihua --numbers "123,456,7"
python3 steward.py --mode liuyao --birthdate "2026-09-12 12:00" --numbers "12,34,56"

# 六爻（手工指定爻值 6/7/8/9，自初爻到上爻）
python3 steward.py --mode liuyao --birthdate "2026-09-12 12:00" --yao "7,7,7,7,7,7"
# 六爻（铜钱：每爻背数 0-3，自初爻到上爻；3背=老阳动、0背=老阴动）
python3 steward.py --mode liuyao --birthdate "2026-09-12 12:00" --coin "3,1,2,1,2,1"

# 八字合婚（双造同排）
python3 steward.py --mode hehun --male "1990-02-04 10:40" --female "1991-01-01 12:00" --birthplace 116.4

# JSON 输出（供程序调用；附 --male/--female 则含合婚）
python3 steward.py --birthdate "1990-02-04 10:40" --mode json
```

## 参数

| 参数 | 说明 |
|---|---|
| `--birthdate` | `YYYY-MM-DD HH:MM`，缺省用当前时间 |
| `--sex` | 1 男/乾造，0 女/坤造 |
| `--birthplace` | 经度或城市名（北京/上海/西安/合肥等），用于真太阳时 |
| `--mode` | bazi/ziwei/liuren/qimen/meihua/jinkoujue/liuyao/all/json |
| `--numbers` | 梅花/六爻 三数起卦 |
| `--yao` | 六爻手工指定 6 个爻值 |
| `--coin` | 六爻铜钱 6 个背数 |
| `--difen` | 金口诀地分 |
| `--male` / `--female` | 合婚：男/女命出生时间 |
| `--male-lon` / `--female-lon` | 合婚：双方出生经度/城市 |
| `--no-true-solar` | 八字日/时柱不校正真太阳时 |

## 参考资料

- `references/权威排盘_verification.md` — 权威站点核对方法与基准案例
- `references/liuyao_lost_items.md` — 六爻寻物断法
- `references/liuyao_najia.md` — 六爻纳甲装卦规则与黄金案例
- `references/hehun_rules.md` — 八字合婚要则
- `references/bazi_权威排盘_calibration.md` — 八字换柱口径与 权威排盘 校准
- `references/liuren_权威排盘_calibration.md` — 大六壬涉害/遥克等九宗门 权威排盘实测口径
- `references/jinkoujue_权威排盘_calibration.md` — 金口诀节换将/贵神顺逆 权威排盘实测口径
- `references/qimen_权威排盘_calibration.md` — 奇门拆补转盘 权威排盘实测口径
- `references/LUNAR_PYTHON_REFERENCE.md` — lunar-python API 笔记

## 依赖

- `lunar-python`：公农历、干支、节气、星座基础（>= 1.4）
