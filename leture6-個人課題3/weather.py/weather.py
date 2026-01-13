import flet as ft
import requests
import sqlite3
from datetime import datetime

AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/"

WEATHER_CODES = {
    "100": "晴れ","101": "晴れ時々曇り","102": "晴れ一時雨","103": "晴れ時々雨","104": "晴れ一時雪","105": "晴れ時々雪",
    "106": "晴れ一時雨か雪","107": "晴れ時々雨か雪","108": "晴れ一時雨か雷雨","110": "晴れのち時々曇り",
    "111": "晴れのち曇り","112": "晴れのち一時雨","113": "晴れのち時々雨","114": "晴れのち雨","115": "晴れのち一時雪",
    "116": "晴れのち時々雪","117": "晴れのち雪","118": "晴れのち雨か雪","119": "晴れのち雨か雷雨","120": "晴れ朝夕一時雨",
    "121": "晴れ朝の内一時雨","122": "晴れ夕方一時雨","123": "晴れ山沿い雷雨","124": "晴れ山沿い雪","125": "晴れ午後は雷雨",
    "126": "晴れ昼頃から雨","127": "晴れ夕方から雨","128": "晴れ夜は雨","130": "朝の内霧後晴れ",
    "131": "晴れ明け方霧","132": "晴れ朝夕曇り","140": "晴れ時々雨で雷を伴う","160": "晴れ一時雪か雨","170": "晴れ時々雪か雨",
    "181": "晴れのち雪か雨",
    "200": "曇り","201": "曇り時々晴れ","202": "曇り一時雨","203": "曇り時々雨","204": "曇り一時雪",
    "205": "曇り時々雪","206": "曇り一時雨か雪","207": "曇り時々雨か雪","208": "曇り一時雨か雷雨","209": "霧",
    "210": "曇りのち時々晴れ","211": "曇りのち晴れ","212": "曇りのち一時雨","213": "曇りのち時々雨","214": "曇りのち雨",
    "215": "曇りのち一時雪","216": "曇りのち時々雪","217": "曇りのち雪","218": "曇りのち雨か雪","219": "曇りのち雨か雷雨",
    "220": "曇り朝夕一時雨","221": "曇り朝の内一時雨","222": "曇り夕方一時雨","223": "曇り日中時々晴れ","224": "曇り昼頃から雨",
    "225": "曇り夕方から雨","226": "曇り夜は雨","228": "曇り昼頃から雪","229": "曇り夕方から雪","230": "曇り夜は雪",
    "231": "曇り海上海岸は霧か霧雨","240": "曇り時々雨で雷を伴う","250": "曇り時々雪で雷を伴う","260": "曇り一時雪か雨",
    "270": "曇り時々雪か雨","281": "曇りのち雪か雨",
    "300": "雨","301": "雨時々晴れ","302": "雨時々止む","303": "雨時々雪","304": "雨か雪",
    "306": "大雨","308": "雨で暴風を伴う","309": "雨一時雪","311": "雨のち晴れ","313": "雨のち曇り",
    "314": "雨のち時々雪","315": "雨のち雪","316": "雨か雪のち晴れ","317": "雨か雪のち曇り","320": "朝の内雨のち晴れ",
    "321": "朝の内雨のち曇り","322": "雨朝晩一時雪","323": "雨昼頃から晴れ","324": "雨夕方から晴れ","325": "雨夜は晴れ",
    "326": "雨夕方から雪","327": "雨夜は雪","328": "雨一時強く降る","329": "雨一時みぞれ","340": "雪か雨",
    "350": "雨で雷を伴う","361": "雪か雨のち晴れ","371": "雪か雨のち曇り",
    "400": "雪","401": "雪時々晴れ","402": "雪時々止む","403": "雪時々雨","405": "大雪",
    "406": "風雪強い","407": "暴風雪","409": "雪一時雨","411": "雪のち晴れ","413": "雪のち曇り",
    "414": "雪のち雨","420": "朝の内雪のち晴れ","421": "朝の内雪のち曇り","422": "雪昼頃から雨",
    "423": "雪夕方から雨","425": "雪一時強く降る","426": "雪のち みぞれ","427": "雪一時みぞれ",
    "450": "雪で雷を伴う",
}

def get_weather_name(code):
    return WEATHER_CODES.get(str(code), "不明")

def init_db():
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS regions (
            region_code TEXT PRIMARY KEY,
            region_name TEXT,
            office_code TEXT,
            office_name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_code TEXT,
            forecast_date TEXT,
            fetched_at TEXT,
            weather TEXT,
            max_temp REAL,
            min_temp REAL,
            pop INTEGER,
            UNIQUE(region_code, forecast_date, fetched_at)
        )
    """)
    conn.commit()
    conn.close()

def save_region(region_code, region_name, office_code, office_name):
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO regions VALUES (?, ?, ?, ?)", 
                (region_code, region_name, office_code, office_name))
    conn.commit()
    conn.close()

def get_regions():
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM regions ORDER BY office_name, region_name")
    results = cur.fetchall()
    conn.close()
    return results

def save_forecast(region_code, date, weather, max_t, min_t, pop):
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    max_temp = float(max_t) if max_t and str(max_t).strip() else None
    min_temp = float(min_t) if min_t and str(min_t).strip() else None
    pop_val = int(pop) if pop and str(pop).strip() else None
    cur.execute("""
        INSERT INTO forecasts (region_code, forecast_date, fetched_at, weather, max_temp, min_temp, pop)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (region_code, date, now, weather, max_temp, min_temp, pop_val))
    conn.commit()
    conn.close()
    return True

def get_forecasts(region_code):
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT forecast_date, weather, max_temp, min_temp, pop, fetched_at
        FROM forecasts
        WHERE region_code = ?
        AND fetched_at = (SELECT MAX(fetched_at) FROM forecasts WHERE region_code = ?)
        ORDER BY forecast_date
    """, (region_code, region_code))
    results = cur.fetchall()
    conn.close()
    return results

def get_history(region_code):
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT fetched_at FROM forecasts
        WHERE region_code = ?
        ORDER BY fetched_at DESC
    """, (region_code,))
    results = [r[0] for r in cur.fetchall()]
    conn.close()
    return results

def main(page: ft.Page):
    init_db()
    page.title = "天気予報アプリ"
    page.window.width = 800
    page.window.height = 700
    page.padding = 20
    
    selected_region = {}
    region_dropdown = ft.Dropdown(label="地域を選択", width=400)
    history_dropdown = ft.Dropdown(label="過去の予報", width=400, visible=False)
    result_area = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
    def load_regions():
        db_regions = get_regions()
        if db_regions:
            options = []
            for r in db_regions:
                options.append(ft.dropdown.Option(key=f"{r[2]}|{r[0]}|{r[1]}", text=f"{r[3]} - {r[1]}"))
            region_dropdown.options = options
            page.update()
        else:
            data = requests.get(AREA_URL).json()
            options = []
            for office_code, office_info in data["offices"].items():
                office_name = office_info["name"]
                for region_code in office_info.get("children", []):
                    if region_code in data["class10s"]:
                        region_name = data["class10s"][region_code]["name"]
                        save_region(region_code, region_name, office_code, office_name)
                        options.append(ft.dropdown.Option(
                            key=f"{office_code}|{region_code}|{region_name}",
                            text=f"{office_name} - {region_name}"
                        ))
            region_dropdown.options = options
            page.update()
    
    def on_region_change(e):
        if not e.control.value:
            return
        parts = e.control.value.split("|")
        selected_region["office"] = parts[0]
        selected_region["code"] = parts[1]
        selected_region["name"] = parts[2]
        history = get_history(selected_region["code"])
        if history:
            history_dropdown.options = [ft.dropdown.Option(key="latest", text="最新の予報")] + \
                [ft.dropdown.Option(key=h, text=f"{h} 取得") for h in history]
            history_dropdown.value = "latest"
            history_dropdown.visible = True
        else:
            history_dropdown.visible = False
        show_forecast()
    
    region_dropdown.on_change = on_region_change
    
    def on_history_change(e):
        if e.control.value == "latest":
            show_forecast()
        else:
            show_forecast(e.control.value)
    
    history_dropdown.on_change = on_history_change
    
    def fetch_forecast(e):
        if not selected_region.get("code"):
            result_area.controls = [ft.Text("地域を選択してください")]
            page.update()
            return
        result_area.controls = [ft.ProgressRing()]
        page.update()
        url = f"{FORECAST_URL}{selected_region['office']}.json"
        data = requests.get(url).json()
        forecasts = {}
        if len(data) > 0 and "timeSeries" in data[0]:
            ts = data[0]["timeSeries"]
            if len(ts) > 0 and "areas" in ts[0]:
                for area in ts[0]["areas"]:
                    if area.get("area", {}).get("code") == selected_region["code"]:
                        time_defines = ts[0].get("timeDefines", [])
                        weathers = area.get("weathers", [])
                        for i, time_str in enumerate(time_defines):
                            date = time_str.split("T")[0]
                            if date not in forecasts:
                                forecasts[date] = {}
                            if i < len(weathers):
                                forecasts[date]["weather"] = weathers[i]
                        if "weatherCodes" in area:
                            codes = area.get("weatherCodes", [])
                            for i, time_str in enumerate(time_defines):
                                date = time_str.split("T")[0]
                                if i < len(codes):
                                    forecasts[date]["weather_code"] = codes[i]
                        break
            if len(ts) > 1 and "areas" in ts[1]:
                for area in ts[1]["areas"]:
                    if area.get("area", {}).get("code") == selected_region["code"]:
                        time_defines = ts[1].get("timeDefines", [])
                        pops = area.get("pops", [])
                        for i, time_str in enumerate(time_defines):
                            date = time_str.split("T")[0]
                            if date not in forecasts:
                                forecasts[date] = {}
                            if i < len(pops) and pops[i] and pops[i] != "":
                                if "pop" not in forecasts[date]:
                                    forecasts[date]["pop"] = pops[i]
                        break
            if len(ts) > 2 and "areas" in ts[2]:
                temp_area = ts[2]["areas"][0] if len(ts[2]["areas"]) > 0 else None
                if temp_area:
                    time_defines = ts[2].get("timeDefines", [])
                    temps = temp_area.get("temps", [])
                    temp_by_date = {}
                    for i, time_str in enumerate(time_defines):
                        if i >= len(temps) or not temps[i] or temps[i] == "":
                            continue
                        date = time_str.split("T")[0]
                        if date not in temp_by_date:
                            temp_by_date[date] = []
                        if "T" in time_str:
                            hour = int(time_str.split("T")[1][:2])
                            temp_by_date[date].append({"hour": hour, "temp": temps[i]})
                    for date, temp_list in temp_by_date.items():
                        if date not in forecasts:
                            forecasts[date] = {}
                        if len(temp_list) == 1:
                            hour = temp_list[0]["hour"]
                            temp = temp_list[0]["temp"]
                            if hour >= 9 and hour <= 15:
                                forecasts[date]["max"] = temp
                            elif hour >= 0 and hour <= 6:
                                forecasts[date]["min"] = temp
                            else:
                                forecasts[date]["max"] = temp
                        elif len(temp_list) >= 2:
                            temps_sorted = sorted(temp_list, key=lambda x: float(x["temp"]))
                            morning_temps = [t for t in temp_list if t["hour"] <= 6]
                            if morning_temps:
                                forecasts[date]["min"] = morning_temps[0]["temp"]
                            else:
                                forecasts[date]["min"] = temps_sorted[0]["temp"]
                            daytime_temps = [t for t in temp_list if 9 <= t["hour"] <= 15]
                            if daytime_temps:
                                max_daytime = max(daytime_temps, key=lambda x: float(x["temp"]))
                                forecasts[date]["max"] = max_daytime["temp"]
                            else:
                                forecasts[date]["max"] = temps_sorted[-1]["temp"]
                            if forecasts[date].get("min") == forecasts[date].get("max"):
                                time_sorted = sorted(temp_list, key=lambda x: x["hour"])
                                if len(time_sorted) >= 2:
                                    forecasts[date]["min"] = time_sorted[0]["temp"]
                                    forecasts[date]["max"] = time_sorted[-1]["temp"]
                                else:
                                    forecasts[date]["max"] = time_sorted[0]["temp"]
                                    if "min" in forecasts[date]:
                                        del forecasts[date]["min"]
        if len(data) > 1 and "timeSeries" in data[1]:
            ws = data[1]["timeSeries"]
            if len(ws) > 0 and "areas" in ws[0]:
                found_area = None
                for area in ws[0]["areas"]:
                    area_code = area.get("area", {}).get("code")
                    if area_code == selected_region["code"]:
                        found_area = area
                        break
                if not found_area:
                    for area in ws[0]["areas"]:
                        area_code = area.get("area", {}).get("code")
                        if area_code == selected_region["office"]:
                            found_area = area
                            break
                if found_area:
                    time_defines = ws[0].get("timeDefines", [])
                    weather_codes = found_area.get("weatherCodes", [])
                    pops = found_area.get("pops", [])
                    for i, time_str in enumerate(time_defines):
                        date = time_str.split("T")[0]
                        if date not in forecasts:
                            forecasts[date] = {}
                        if i < len(weather_codes):
                            code = weather_codes[i]
                            if code:
                                forecasts[date]["weather"] = get_weather_name(code)
                                forecasts[date]["weather_code"] = code
                        if i < len(pops) and pops[i] and pops[i] != "":
                            forecasts[date]["pop"] = pops[i]
            if len(ws) > 1 and "areas" in ws[1]:
                temp_area = ws[1]["areas"][0] if len(ws[1]["areas"]) > 0 else None
                if temp_area:
                    time_defines = ws[1].get("timeDefines", [])
                    temps_max = temp_area.get("tempsMax", [])
                    temps_min = temp_area.get("tempsMin", [])
                    temps_max_upper = temp_area.get("tempsMaxUpper", [])
                    temps_max_lower = temp_area.get("tempsMaxLower", [])
                    temps_min_upper = temp_area.get("tempsMinUpper", [])
                    temps_min_lower = temp_area.get("tempsMinLower", [])
                    for i, time_str in enumerate(time_defines):
                        date = time_str.split("T")[0]
                        if date not in forecasts:
                            forecasts[date] = {}
                        max_temp_value = None
                        min_temp_value = None
                        if i < len(temps_max) and temps_max[i] and temps_max[i] != "":
                            max_temp_value = temps_max[i]
                        elif i < len(temps_max_upper) and temps_max_upper[i] and temps_max_upper[i] != "":
                            max_temp_value = temps_max_upper[i]
                        elif i < len(temps_max_lower) and temps_max_lower[i] and temps_max_lower[i] != "":
                            max_temp_value = temps_max_lower[i]
                        if i < len(temps_min) and temps_min[i] and temps_min[i] != "":
                            min_temp_value = temps_min[i]
                        elif i < len(temps_min_lower) and temps_min_lower[i] and temps_min_lower[i] != "":
                            min_temp_value = temps_min_lower[i]
                        elif i < len(temps_min_upper) and temps_min_upper[i] and temps_min_upper[i] != "":
                            min_temp_value = temps_min_upper[i]
                        if max_temp_value and min_temp_value:
                            if max_temp_value == min_temp_value:
                                forecasts[date]["max"] = max_temp_value
                            else:
                                max_val = float(max_temp_value)
                                min_val = float(min_temp_value)
                                if max_val >= min_val:
                                    forecasts[date]["max"] = max_temp_value
                                    forecasts[date]["min"] = min_temp_value
                                else:
                                    forecasts[date]["max"] = min_temp_value
                                    forecasts[date]["min"] = max_temp_value
                        elif max_temp_value:
                            forecasts[date]["max"] = max_temp_value
                        elif min_temp_value:
                            forecasts[date]["min"] = min_temp_value
        saved_count = 0
        for date in sorted(forecasts.keys()):
            fc = forecasts[date]
            if fc.get("weather") or fc.get("max") or fc.get("min"):
                save_forecast(selected_region["code"], date, fc.get("weather", ""), 
                            fc.get("max"), fc.get("min"), fc.get("pop"))
                saved_count += 1
        history = get_history(selected_region["code"])
        if history:
            history_dropdown.options = [ft.dropdown.Option(key="latest", text="最新の予報")] + \
                [ft.dropdown.Option(key=h, text=f"{h} 取得") for h in history]
            history_dropdown.value = "latest"
            history_dropdown.visible = True
        if saved_count > 0:
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ {saved_count}件のデータを保存しました"))
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"⚠️ データが取得できませんでした"))
        page.snack_bar.open = True
        show_forecast()
    
    def show_forecast(fetched_at=None):
        if fetched_at:
            conn = sqlite3.connect("weather.db")
            cur = conn.cursor()
            cur.execute("""
                SELECT forecast_date, weather, max_temp, min_temp, pop, fetched_at
                FROM forecasts
                WHERE region_code = ? AND fetched_at = ?
                ORDER BY forecast_date
            """, (selected_region["code"], fetched_at))
            forecasts = cur.fetchall()
            conn.close()
        else:
            forecasts = get_forecasts(selected_region["code"])
        if not forecasts:
            result_area.controls = [ft.Text("データがありません。「天気予報を取得」ボタンを押してください。")]
            page.update()
            return
        fetch_time = forecasts[0][5] if forecasts else ""
        cards = []
        for fc in forecasts:
            date = datetime.strptime(fc[0], "%Y-%m-%d")
            date_str = date.strftime("%m/%d (%a)")
            weather = fc[1] if fc[1] else "不明"
            max_t = fc[2]
            min_t = fc[3]
            if max_t is not None and min_t is not None:
                if max_t == min_t:
                    temp_display = f"🌡️ 気温 {max_t:.0f}℃"
                else:
                    temp_display = f"🌡️ 最高 {max_t:.0f}℃ / 最低 {min_t:.0f}℃"
            elif max_t is not None:
                temp_display = f"🌡️ 最高 {max_t:.0f}℃"
            elif min_t is not None:
                temp_display = f"🌡️ 最低 {min_t:.0f}℃"
            else:
                temp_display = "🌡️ --"
            pop = f"{fc[4]}" if fc[4] is not None else "--"
            card = ft.Card(content=ft.Container(content=ft.Column([
                ft.Text(date_str, size=16, weight="bold", color=ft.Colors.BLUE_700),
                ft.Divider(height=1),
                ft.Text(f"☀️ 天気: {weather}", size=14),
                ft.Text(temp_display, size=13),
                ft.Text(f"💧 降水確率 {pop}%", size=13),
            ], spacing=5), padding=15, bgcolor=ft.Colors.BLUE_50))
            cards.append(card)
        result_area.controls = [
            ft.Text(f"📍 {selected_region['name']}", size=20, weight="bold"),
            ft.Text(f"🕒 {fetch_time} 取得", size=12, color=ft.Colors.GREY_700),
            ft.Text(f"📊 {len(cards)}日分のデータ", size=12, color=ft.Colors.GREY_700),
            ft.Divider(),
            ft.Column(cards, spacing=10)
        ]
        page.update()
    
    page.add(ft.Column([
        ft.Text("🌤️ 天気予報アプリ", size=28, weight="bold"),
        ft.Divider(),
        region_dropdown,
        history_dropdown,
        ft.ElevatedButton("天気予報を取得", icon=ft.Icons.CLOUD_DOWNLOAD, on_click=fetch_forecast),
        ft.Divider(),
        ft.Container(content=result_area, expand=True)
    ], spacing=15, expand=True))
    
    load_regions()

ft.app(target=main)