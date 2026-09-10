# lunar-python API Notes & Pitfalls

This reference document consolidates findings from developing the `metaphysics-steward` skill using the `lunar-python` library.

### 1. Bazi (EightChar) API
- **Da Yun (Great Cycles)**: The method `eight_char.getDaYun()` might be absent. Use the `getYun` proxy:
  ```python
  yun = eight_char.getYun(sex) # sex: 1=Male, 0=Female
  da_yun_list = yun.getDaYun()
  ```
- **Hidden Stems**: Use `getYearHideGan()`, `getMonthHideGan()`, etc.
- **Ten Gods (Shi Shen)**:
  - Heavenly Stems: `getYearShiShenGan()`
  - Earthly Branches: `getYearShiShenZhi()` (returns list)

### 2. Meihua & Qimen
- **Native Support**: The installed version of `lunar_python` may not include `MeiHua` or `QiMenJu`.
- **Manual Calculation**:
  - **Meihua**: `(YearZhiIdx + Month + Day) % 8` for Upper, `(+ HourZhiIdx) % 8` for Lower.
  - **Qimen**: Uses the "Chai Bu" (拆补) method. Ju (局) is determined by the nearest Jieqi and the "Fu Tou" (符头) of the day.

### 3. Longitude & True Solar Time
- **Offset**: 4 minutes per degree longitude from 120°E.
- **Equation of Time**: Significant variance throughout the year (up to ±16 mins).
- **Formula**: `TrueSolar = CivilTime + (4 * (LocalLongitude - 120)) + EquationOfTime`.

### 4. Code Workarounds
- **Index matching**:
  ```python
  def get_day_index(lunar):
      g = lunar.getDayGanIndex()
      z = lunar.getDayZhiIndex()
      for i in range(60):
          if i % 10 == g and i % 12 == z:
              return i
      return 0
  ```
