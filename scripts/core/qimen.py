# -*- coding: utf-8 -*-
from .utils import TIANGAN, DIZHI

class QimenEngine:
    """
    Qi Men Dun Jia Engine (Chai Bu Method).
    Calculates the 9-palace grid with Stars, Doors, Gods, and Heaven/Earth Stems.
    """
    def __init__(self, lunar):
        self.lunar = lunar
        self.solar = lunar.getSolar()
        self.day_ganzhi = lunar.getDayInGanZhi()
        self.hour_ganzhi = lunar.getTimeInGanZhi()
        
    def get_ju(self):
        """Determine the current Ju (Pattern) using Chai Bu method.

        分窗（权威排盘实测收敛）：以「最近一个 24 节气」为局窗——节与中气
        均按精确时刻切换，取二者中时间较近者（如 1990-02-04 00:00 立春
        (10:14) 未到，prevQi=大寒(1/20) 晚于 prevJie=小寒(1/5) → 用大寒窗
        三九六→中元 9；元亨利贞实现如此，勿用 getPrevJieQi(True)——其在
        节气日 0 点即误切新节）。
        """
        pj = self.lunar.getPrevJie()
        pq = self.lunar.getPrevQi()
        jq = pj if pj.getSolar().getYear()*10000 + pj.getSolar().getMonth()*100 \
                  + pj.getSolar().getDay() > pq.getSolar().getYear()*10000 \
                  + pq.getSolar().getMonth()*100 + pq.getSolar().getDay() else pq
        jq_name = jq.getName()
        
        ju_map = {
            "冬至": [1, 7, 4], "小寒": [2, 8, 5], "大寒": [3, 9, 6],
            "立春": [8, 5, 2], "雨水": [9, 6, 3], "惊蛰": [1, 4, 7],
            "春分": [3, 9, 6], "清明": [4, 1, 7], "谷雨": [5, 2, 8],
            "立夏": [4, 1, 7], "小满": [5, 2, 8], "芒种": [6, 3, 9],
            "夏至": [-9, -3, -6], "小暑": [-8, -2, -5], "大暑": [-7, -1, -4],
            "立秋": [-2, -5, -8], "处暑": [-1, -4, -7], "白露": [-9, -3, -6],
            "秋分": [-7, -1, -4], "寒露": [-6, -9, -3], "霜降": [-5, -8, -2],
            "立冬": [-6, -9, -3], "小雪": [-5, -8, -2], "大雪": [-4, -7, -1]
        }
        
        if jq_name not in ju_map:
            return 1
            
        base_jus = ju_map[jq_name]
        
        # Determine Yuan (Upper, Middle, Lower) based on day Fu Tou
        temp_lunar = self.lunar
        while temp_lunar.getDayGan() not in ["甲", "己"]:
            temp_lunar = temp_lunar.next(-1)
        
        futou_zhi = temp_lunar.getDayZhi()
        if futou_zhi in ["子", "午", "卯", "酉"]:
            yuan_idx = 0
        elif futou_zhi in ["寅", "申", "巳", "亥"]:
            yuan_idx = 1
        else:
            yuan_idx = 2
            
        return base_jus[yuan_idx]

    def get_di_pan(self, ju):
        """Generate the Earth Plate (Di Pan)."""
        order = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
        grid = {}
        is_yang = ju > 0
        abs_ju = abs(ju)
        path = [1, 2, 3, 4, 5, 6, 7, 8, 9] if is_yang else [9, 8, 7, 6, 5, 4, 3, 2, 1]
        
        start_house = abs_ju
        current_house = start_house
        for stem in order:
            grid[current_house] = stem
            idx = path.index(current_house)
            current_house = path[(idx + 1) % 9]
        return grid

    def analyze(self):
        ju = self.get_ju()
        di_pan = self.get_di_pan(ju)
        
        # Xun Shou (Leader of the 10-hour period)
        xun_shou_map = {"甲子": "戊", "甲戌": "己", "甲申": "庚", "甲午": "辛", "甲辰": "壬", "甲寅": "癸"}
        hg = self.hour_ganzhi[0]
        hz = self.hour_ganzhi[1]
        h_idx = TIANGAN.index(hg)
        z_idx = DIZHI.index(hz)
        
        xun_start_zhi = DIZHI[(z_idx - h_idx) % 12]
        xun_shou_gz = "甲" + xun_start_zhi
        shou_stem = xun_shou_map.get(xun_shou_gz, "戊")
        
        shou_house = [k for k, v in di_pan.items() if v == shou_stem][0]
        
        star_map = {1: "蓬", 2: "芮", 3: "冲", 4: "辅", 5: "禽", 6: "心", 7: "柱", 8: "任", 9: "英"}
        door_map = {1: "休", 2: "死", 3: "伤", 4: "杜", 6: "开", 7: "惊", 8: "生", 9: "景"}
        
        zhi_fu_star = star_map[shou_house]
        zhi_shi_door = door_map.get(shou_house, "死")
        
        # Target house for Zhi Fu
        target_stem = hg if hg != "甲" else shou_stem
        target_house_raw = [k for k, v in di_pan.items() if v == target_stem][0]
        target_house = target_house_raw
        if target_house == 5: target_house = 2
        
        rim = [1, 8, 3, 4, 9, 2, 7, 6]
        try:
            shou_idx = rim.index(shou_house) if shou_house != 5 else rim.index(2)
            target_idx = rim.index(target_house)
            diff = (target_idx - shou_idx) % 8
        except ValueError:
            diff = 0
            
        heaven_pan, stars = {}, {}
        for i, house in enumerate(rim):
            old_house = rim[(i - diff) % 8]
            stars[house] = star_map[old_house]
            heaven_pan[house] = di_pan[old_house]
        
        # Doors rotation
        path = [1, 2, 3, 4, 5, 6, 7, 8, 9] if ju > 0 else [9, 8, 7, 6, 5, 4, 3, 2, 1]
        hour_offset = TIANGAN.index(hg)
        shi_idx = path.index(shou_house)
        shi_target_raw = path[(shi_idx + hour_offset) % 9]
        shi_target_house = shi_target_raw
        if shi_target_house == 5: shi_target_house = 2
        
        door_rim = [1, 8, 3, 4, 9, 2, 7, 6]
        try:
            d_shou_idx = door_rim.index(shou_house) if shou_house != 5 else door_rim.index(2)
            d_target_idx = door_rim.index(shi_target_house)
            d_diff = (d_target_idx - d_shou_idx) % 8
        except:
            d_diff = 0
            
        doors = {}
        for i, house in enumerate(door_rim):
            old_house = door_rim[(i - d_diff) % 8]
            doors[house] = door_map.get(old_house, "  ")
            
        # Gods
        gods_list = ["符", "蛇", "阴", "合", "虎", "武", "地", "天"] if ju > 0 else ["符", "天", "地", "武", "虎", "合", "阴", "蛇"]
        gods = {}
        for i, house in enumerate(rim):
            idx = (i - target_idx) % 8
            gods[house] = gods_list[idx]

        layout = [4, 9, 2, 3, 5, 7, 8, 1, 6]
        grid_data = []
        for h in layout:
            if h == 5:
                grid_data.append(f"  {di_pan[5]}  ")
            else:
                g, s, d = gods.get(h, " "), stars.get(h, " "), doors.get(h, " ")
                tp, dp = heaven_pan.get(h, " "), di_pan.get(h, " ")
                grid_data.append(f"{g}{s}{d}\n{tp}{dp}")

        render = f"奇门遁甲 [{ '阳' if ju > 0 else '阴' }遁 {abs(ju)}局]\n"
        render += f"值符: {zhi_fu_star}星  值使: {zhi_shi_door}门\n"
        render += "┌────┬────┬────┐\n"
        for i in range(0, 9, 3):
            r1, r2 = "│", "│"
            for j in range(3):
                cell = grid_data[i+j].split('\n')
                if len(cell) == 1:
                    r1 += f" {cell[0]} │"
                    r2 += "      │"
                else:
                    r1 += f" {cell[0]} │"
                    r2 += f"  {cell[1]}  │"
            render += r1 + "\n" + r2 + "\n"
            if i < 6: render += "├────┼────┼────┤\n"
        render += "└────┴────┴────┘"

        # —— 结构化对齐字段 ——
        G_FULL = {"符": "直符", "蛇": "螣蛇", "阴": "太阴", "合": "六合",
                  "虎": "白虎", "武": "玄武", "地": "九地", "天": "九天"}
        god_full = {h: G_FULL[gods[h]] for h in gods}
        grid = {}
        for h in layout:
            if h == 5:
                grid[5] = {"god": "", "star": "", "door": "",
                           "tgan": "", "dgan": di_pan[5]}
            else:
                grid[h] = {"god": god_full[h], "star": stars[h], "door": doors[h],
                           "tgan": heaven_pan[h], "dgan": di_pan[h]}
        # 值符/值使落宫：以旬首宫计（中五记 5），直符神实际寄坤二
        return {
            "ju": ju,
            "yang": ju > 0,
            "xun_shou": shou_stem,
            "zhifu": {"star": zhi_fu_star, "house": target_house_raw},
            "zhishi": {"door": zhi_shi_door, "house": shi_target_raw},
            "di_pan": {h: di_pan[h] for h in layout},
            "grid": grid,
            "render": render,
        }
