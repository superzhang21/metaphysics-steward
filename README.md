# 玄学管家 Metaphysics Steward

专业中文玄学排盘引擎，覆盖 7 种传统术数 + 八字合婚，强调天文精度与交叉验证。

## 能力

| 术数 | 说明 |
|---|---|
| 八字四柱 | 节气换柱、十神/藏干/纳音、大运起运 |
| 紫微斗数 | 12 宫 14 主星、年系四化、五行局 |
| 大六壬 | 中气月将、四课三传、九宗门全口径 |
| 奇门遁甲 | 时家拆补转盘、八神/九星/八门 |
| 梅花易数 | 时间/数字起卦、本卦/互卦/变卦/体用 |
| 金口诀 | 四层课式（人元/贵神/月将/地分） |
| 六爻纳甲 | 铜钱/数字/时间三法起卦、京房八宫装卦 |
| 八字合婚 | 双造同排、生肖/纳音/五合/互补综合评分 |

## 排盘口径

- 八字/紫微/六爻以 **真太阳时**（经度 + 均时差修正）为排盘基准
- 大六壬/金口诀/奇门以 **民用时间** 起课
- 口径对照 权威在线排盘参考站点 （已 golden 锁定）

## 快速开始

```bash
pip install -r requirements.txt

cd scripts

# 七法全排
python3 steward.py --birthdate "1990-02-04 10:40" --sex 1 --birthplace 116.4 --mode all

# 单法
python3 steward.py --birthdate "1990-02-04 10:40" --sex 1 --mode bazi
python3 steward.py --mode meihua --numbers "123,456,7"

# 六爻
python3 steward.py --mode liuyao --yao "7,7,7,7,7,7"

# 八字合婚
python3 steward.py --mode hehun --male "1990-02-04 10:40" --female "1991-01-01 12:00"

# JSON 输出
python3 steward.py --birthdate "1990-02-04 10:40" --mode json
```

## 参数

| 参数 | 说明 |
|---|---|
| `--birthdate` | `YYYY-MM-DD HH:MM`，缺省当前时间 |
| `--sex` | 1 男/乾造，0 女/坤造 |
| `--birthplace` | 经度或城市名，用于真太阳时 |
| `--mode` | bazi/ziwei/liuren/qimen/meihua/jinkoujue/liuyao/hehun/all/json |
| `--numbers` | 梅花/六爻三数起卦 |
| `--yao` | 六爻手工指定 6 个爻值 (6/7/8/9) |
| `--coin` | 六爻铜钱 6 个背数 (0-3) |
| `--difen` | 金口诀地分（地支），默认 子 |
| `--male` / `--female` | 合婚：男/女命出生时间 |
| `--no-true-solar` | 八字日/时柱不校正真太阳时 |

## 测试

```bash
# 全量回归（含六爻 2000 次 fuzz + 八宫校验）
python3 tests/test_full_regression.py

# 各引擎黄金案例回归
python3 tests/test_bazi_权威排盘_golden.py
python3 tests/test_liuren_权威排盘_golden.py
python3 tests/test_liuyao_golden.py
python3 tests/test_jinkoujue_权威排盘_golden.py
python3 tests/test_qimen_权威排盘_golden.py
python3 tests/test_ziwei_权威排盘_golden.py
python3 tests/test_meihua_regression.py
python3 tests/test_hehun.py

# 或用 pytest
pytest tests/
```

## 依赖

- [lunar-python](https://github.com/6tail/lunar-python) >= 1.4：公农历、干支、节气

## 参考资料

- `references/bazi_权威排盘_calibration.md` — 八字换柱口径与 权威排盘 校准
- `references/liuren_权威排盘_calibration.md` — 大六壬九宗门 权威排盘实测口径
- `references/jinkoujue_权威排盘_calibration.md` — 金口诀 权威排盘实测口径
- `references/qimen_权威排盘_calibration.md` — 奇门拆补转盘 权威排盘实测口径
- `references/liuyao_najia.md` — 六爻纳甲装卦规则
- `references/hehun_rules.md` — 八字合婚要则
- `references/权威排盘_verification.md` — 权威站点核对方法
- `references/LUNAR_PYTHON_REFERENCE.md` — lunar-python API 笔记

## License

MIT
