import flet as ft
import requests
import sqlite3
from datetime import datetime

# URL定義
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL_BASE = "https://www.jma.go.jp/bosai/forecast/data/forecast/"
DB_NAME = "weather_forecast.db"

# 天気コード変換辞書
WEATHER_CODES = {
    "100": "晴れ", "101": "晴れ時々曇り", "102": "晴れ一時雨", "103": "晴れ時々雨",
    "104": "晴れ一時雪", "105": "晴れ時々雪", "111": "晴れのち曇り", "112": "晴れのち一時雨",
    "113": "晴れのち時々雨", "114": "晴れのち雨", "115": "晴れのち一時雪", "116": "晴れのち時々雪",
    "117": "晴れのち雪", "118": "晴れのち雨か雪", "119": "晴れのち雨か雷雨",
    "200": "曇り", "201": "曇り時々晴れ", "202": "曇り一時雨", "203": "曇り時々雨",
    "204": "曇り一時雪", "205": "曇り時々雪", "209": "霧", "211": "曇りのち晴れ",
    "212": "曇りのち一時雨", "213": "曇りのち時々雨", "214": "曇りのち雨",
    "215": "曇りのち一時雪", "216": "曇りのち時々雪", "217": "曇りのち雪",
    "300": "雨", "301": "雨時々晴れ", "302": "雨時々止む", "303": "雨時々雪",
    "311": "雨のち晴れ", "313": "雨のち曇り", "314": "雨のち時々雪", "315": "雨のち雪",
    "400": "雪", "401": "雪時々晴れ", "402": "雪時々止む", "403": "雪時々雨",
    "411": "雪のち晴れ", "413": "雪のち曇り", "414": "雪のち雨",
}

def get_weather_text(code):
    return WEATHER_CODES.get(str(code), f"不明({code})")

# データベース初期化
def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_code TEXT,
            forecast_date TEXT,
            fetched_at TEXT,
            weather TEXT,
            max_temp TEXT,
            min_temp TEXT,
            pop TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_forecast(region_code, date, weather, max_t, min_t, pop):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO forecasts (region_code, forecast_date, fetched_at, weather, max_temp, min_temp, pop)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (region_code, date, now, weather, max_t, min_t, pop))
    conn.commit()
    conn.close()

def get_forecasts(region_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT forecast_date, weather, max_temp, min_temp, pop, fetched_at
        FROM forecasts
        WHERE region_code = ? 
        AND fetched_at = (SELECT MAX(fetched_at) FROM forecasts WHERE region_code = ?)
        ORDER BY forecast_date
    ''', (region_code, region_code))
    results = cursor.fetchall()
    conn.close()
    return results

def main(page: ft.Page):
    init_database()
    page.title = "天気予報アプリ"
    page.window_width = 900
    page.window_height = 700
    page.padding = 20

    current_region = {"code": None, "office": None, "name": None}
    display = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    region_dropdown = ft.Dropdown(label="地域を選択", width=400)
    
    def load_regions():
        try:
            res = requests.get(AREA_URL).json()
            options = []
            for center_code, center_info in res["centers"].items():
                for office_code in center_info.get("children", []):
                    office_name = res["offices"][office_code]["name"]
                    for region_code in res["offices"][office_code].get("children", []):
                        if region_code in res["class10s"]:
                            region_name = res["class10s"][region_code]["name"]
                            options.append(ft.dropdown.Option(
                                key=f"{office_code}|{region_code}|{region_name}",
                                text=f"{office_name} - {region_name}"
                            ))
            region_dropdown.options = options
            page.update()
        except Exception as e:
            display.controls = [ft.Text(f"エラー: {e}", color="red")]
            page.update()
    
    def on_region_select(e):
        if not e.control.value:
            return
        parts = e.control.value.split("|")
        current_region["office"] = parts[0]
        current_region["code"] = parts[1]
        current_region["name"] = parts[2]
        show_forecasts()
    
    region_dropdown.on_change = on_region_select
    
    def fetch_weather():
        if not current_region["code"]:
            display.controls = [ft.Text("地域を選択してください")]
            page.update()
            return
        
        display.controls = [ft.ProgressRing()]
        page.update()
        
        try:
            url = f"{FORECAST_URL_BASE}{current_region['office']}.json"
            data = requests.get(url).json()
            
            # 短期予報と週間予報を統合
            all_dates = {}  # {日付: {weather, max_temp, min_temp, pop}}
            
            # 短期予報（data[0]）
            if len(data) > 0:
                ts = data[0]["timeSeries"]
                
                # 天気
                weather_ts = ts[0]
                weather_area = next((a for a in weather_ts["areas"] if a["area"]["code"] == current_region["code"]), None)
                if weather_area:
                    for i, time_str in enumerate(weather_ts["timeDefines"]):
                        date = time_str.split("T")[0]
                        if date not in all_dates:
                            all_dates[date] = {}
                        all_dates[date]["weather"] = weather_area["weathers"][i] if i < len(weather_area["weathers"]) else ""
                
                # 降水確率
                pop_ts = ts[1]
                pop_area = next((a for a in pop_ts["areas"] if a["area"]["code"] == current_region["code"]), None)
                if pop_area:
                    for i, time_str in enumerate(pop_ts["timeDefines"]):
                        date = time_str.split("T")[0]
                        if date not in all_dates:
                            all_dates[date] = {}
                        if "pops" in pop_area and i < len(pop_area["pops"]) and pop_area["pops"][i]:
                            if "pop" not in all_dates[date]:
                                all_dates[date]["pop"] = pop_area["pops"][i]
                
                # 気温
                temp_ts = ts[2]
                temp_area = temp_ts["areas"][0] if len(temp_ts["areas"]) > 0 else None
                if temp_area:
                    for i, time_str in enumerate(temp_ts["timeDefines"]):
                        date = time_str.split("T")[0]
                        hour = time_str.split("T")[1].split(":")[0]
                        if date not in all_dates:
                            all_dates[date] = {}
                        if i < len(temp_area["temps"]):
                            if hour == "09":
                                all_dates[date]["max_temp"] = temp_area["temps"][i]
                            elif hour == "00":
                                all_dates[date]["min_temp"] = temp_area["temps"][i]
            
            # 週間予報（data[1]）
            if len(data) > 1:
                ws = data[1]["timeSeries"]
                
                # 天気・降水確率
                if len(ws) > 0:
                    weather_weekly = ws[0]
                    weekly_area = None
                    for area in weather_weekly["areas"]:
                        if area["area"]["code"] in [current_region["code"], current_region["office"]]:
                            weekly_area = area
                            break
                    
                    if weekly_area:
                        for i, time_str in enumerate(weather_weekly["timeDefines"]):
                            date = time_str.split("T")[0]
                            if date not in all_dates:
                                all_dates[date] = {}
                            
                            # 天気コードを変換
                            if "weatherCodes" in weekly_area and i < len(weekly_area["weatherCodes"]):
                                all_dates[date]["weather"] = get_weather_text(weekly_area["weatherCodes"][i])
                            
                            # 降水確率
                            if "pops" in weekly_area and i < len(weekly_area["pops"]) and weekly_area["pops"][i]:
                                all_dates[date]["pop"] = weekly_area["pops"][i]
                
                # 気温
                if len(ws) > 1:
                    temp_weekly = ws[1]["areas"][0] if len(ws[1]["areas"]) > 0 else None
                    if temp_weekly:
                        for i, time_str in enumerate(ws[1]["timeDefines"]):
                            date = time_str.split("T")[0]
                            if date not in all_dates:
                                all_dates[date] = {}
                            
                            if "tempsMax" in temp_weekly and i < len(temp_weekly["tempsMax"]):
                                all_dates[date]["max_temp"] = temp_weekly["tempsMax"][i]
                            
                            if "tempsMin" in temp_weekly and i < len(temp_weekly["tempsMin"]):
                                all_dates[date]["min_temp"] = temp_weekly["tempsMin"][i]
            
            # データベースに保存
            for date in sorted(all_dates.keys()):
                d = all_dates[date]
                save_forecast(
                    current_region["code"],
                    date,
                    d.get("weather", ""),
                    d.get("max_temp", ""),
                    d.get("min_temp", ""),
                    d.get("pop", "")
                )
            
            page.snack_bar = ft.SnackBar(ft.Text("✅ 取得完了"))
            page.snack_bar.open = True
            show_forecasts()
            
        except Exception as e:
            display.controls = [ft.Text(f"エラー: {e}", color="red")]
            page.update()
    
    def show_forecasts():
        forecasts = get_forecasts(current_region["code"])
        
        if not forecasts:
            display.controls = [ft.Text("データがありません")]
            page.update()
            return
        
        cards = []
        for fc in forecasts:
            date_obj = datetime.strptime(fc[0], '%Y-%m-%d')
            date_text = date_obj.strftime('%m月%d日(%a)')
            
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(date_text, size=16, weight="bold", color=ft.Colors.BLUE_900),
                        ft.Divider(height=1),
                        ft.Text(f"☀️ {fc[1] if fc[1] else '--'}", size=14),
                        ft.Text(f"🌡️ 最高: {fc[2]}°C / 最低: {fc[3]}°C" if fc[2] or fc[3] else "🌡️ --", size=13),
                        ft.Text(f"💧 降水確率: {fc[4]}%" if fc[4] else "💧 --", size=13),
                    ], spacing=5),
                    padding=15,
                )
            )
            cards.append(card)
        
        display.controls = [
            ft.Text(f"📍 {current_region['name']}", size=20, weight="bold"),
            ft.Column(cards, spacing=10)
        ]
        page.update()
    
    fetch_btn = ft.ElevatedButton(
        "天気予報を取得",
        icon=ft.Icons.CLOUD_DOWNLOAD,
        on_click=lambda e: fetch_weather(),
        bgcolor=ft.Colors.BLUE_600,
        color=ft.Colors.WHITE
    )
    
    page.add(
        ft.Column([
            ft.Text("天気予報アプリ", size=24, weight="bold"),
            ft.Divider(),
            region_dropdown,
            fetch_btn,
            ft.Divider(),
            ft.Container(content=display, expand=True)
        ], spacing=15, expand=True)
    )
    
    load_regions()

ft.app(target=main)