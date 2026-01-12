import flet as ft
import requests
import sqlite3
import json
from datetime import datetime

# URL定義
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL_BASE = "https://www.jma.go.jp/bosai/forecast/data/forecast/"
DB_NAME = "weather_forecast.db"

# 天気コード変換辞書
WEATHER_CODES = {
    "100": "晴れ",
    "101": "晴れ時々曇り",
    "102": "晴れ一時雨",
    "103": "晴れ時々雨",
    "104": "晴れ一時雪",
    "105": "晴れ時々雪",
    "106": "晴れ一時雨か雪",
    "107": "晴れ時々雨か雪",
    "108": "晴れ一時雨か雷雨",
    "110": "晴れのち時々曇り",
    "111": "晴れのち曇り",
    "112": "晴れのち一時雨",
    "113": "晴れのち時々雨",
    "114": "晴れのち雨",
    "115": "晴れのち一時雪",
    "116": "晴れのち時々雪",
    "117": "晴れのち雪",
    "118": "晴れのち雨か雪",
    "119": "晴れのち雨か雷雨",
    "120": "晴れ朝夕一時雨",
    "121": "晴れ朝の内一時雨",
    "122": "晴れ夕方一時雨",
    "123": "晴れ山沿い雷雨",
    "124": "晴れ山沿い雪",
    "125": "晴れ午後は雷雨",
    "126": "晴れ昼頃から雨",
    "127": "晴れ夕方から雨",
    "128": "晴れ夜は雨",
    "130": "朝の内霧後晴れ",
    "131": "晴れ明け方霧",
    "132": "晴れ朝夕曇り",
    "140": "晴れ時々雨で雷を伴う",
    "160": "晴れ一時雪か雨",
    "170": "晴れ時々雪か雨",
    "181": "晴れのち雪か雨",
    "200": "曇り",
    "201": "曇り時々晴れ",
    "202": "曇り一時雨",
    "203": "曇り時々雨",
    "204": "曇り一時雪",
    "205": "曇り時々雪",
    "206": "曇り一時雨か雪",
    "207": "曇り時々雨か雪",
    "208": "曇り一時雨か雷雨",
    "209": "霧",
    "210": "曇りのち時々晴れ",
    "211": "曇りのち晴れ",
    "212": "曇りのち一時雨",
    "213": "曇りのち時々雨",
    "214": "曇りのち雨",
    "215": "曇りのち一時雪",
    "216": "曇りのち時々雪",
    "217": "曇りのち雪",
    "218": "曇りのち雨か雪",
    "219": "曇りのち雨か雷雨",
    "220": "曇り朝夕一時雨",
    "221": "曇り朝の内一時雨",
    "222": "曇り夕方一時雨",
    "223": "曇り日中時々晴れ",
    "224": "曇り昼頃から雨",
    "225": "曇り夕方から雨",
    "226": "曇り夜は雨",
    "228": "曇り昼頃から雪",
    "229": "曇り夕方から雪",
    "230": "曇り夜は雪",
    "231": "曇り海上海岸は霧か霧雨",
    "240": "曇り時々雨で雷を伴う",
    "250": "曇り時々雪で雷を伴う",
    "260": "曇り一時雪か雨",
    "270": "曇り時々雪か雨",
    "281": "曇りのち雪か雨",
    "300": "雨",
    "301": "雨時々晴れ",
    "302": "雨時々止む",
    "303": "雨時々雪",
    "304": "雨か雪",
    "306": "大雨",
    "308": "雨で暴風を伴う",
    "309": "雨一時雪",
    "311": "雨のち晴れ",
    "313": "雨のち曇り",
    "314": "雨のち時々雪",
    "315": "雨のち雪",
    "316": "雨か雪のち晴れ",
    "317": "雨か雪のち曇り",
    "320": "朝の内雨のち晴れ",
    "321": "朝の内雨のち曇り",
    "322": "雨朝晩一時雪",
    "323": "雨昼頃から晴れ",
    "324": "雨夕方から晴れ",
    "325": "雨夜は晴れ",
    "326": "雨夕方から雪",
    "327": "雨夜は雪",
    "328": "雨一時強く降る",
    "329": "雨一時みぞれ",
    "340": "雪か雨",
    "350": "雨で雷を伴う",
    "361": "雪か雨のち晴れ",
    "371": "雪か雨のち曇り",
    "400": "雪",
    "401": "雪時々晴れ",
    "402": "雪時々止む",
    "403": "雪時々雨",
    "405": "大雪",
    "406": "風雪強い",
    "407": "暴風雪",
    "409": "雪一時雨",
    "411": "雪のち晴れ",
    "413": "雪のち曇り",
    "414": "雪のち雨",
    "420": "朝の内雪のち晴れ",
    "421": "朝の内雪のち曇り",
    "422": "雪昼頃から雨",
    "423": "雪夕方から雨",
    "425": "雪一時強く降る",
    "426": "雪のちみぞれ",
    "427": "雪一時みぞれ",
    "450": "雪で雷を伴う",
}

def get_weather_text(weather_code):
    """天気コードを天気テキストに変換"""
    if not weather_code:
        return "情報なし"
    
    code_str = str(weather_code)
    return WEATHER_CODES.get(code_str, f"不明({code_str})")

# データベース初期化
def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 地域テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regions (
            region_code TEXT PRIMARY KEY,
            region_name TEXT NOT NULL,
            office_code TEXT NOT NULL
        )
    ''')
    
    # 天気予報テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_code TEXT NOT NULL,
            forecast_date TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            weather_text TEXT,
            weather_code TEXT,
            max_temp TEXT,
            min_temp TEXT,
            max_temp_upper TEXT,
            max_temp_lower TEXT,
            min_temp_upper TEXT,
            min_temp_lower TEXT,
            pop TEXT,
            reliability TEXT,
            wind TEXT,
            wave TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# 地域情報をDBに保存
def save_region(region_code, region_name, office_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO regions (region_code, region_name, office_code)
        VALUES (?, ?, ?)
    ''', (region_code, region_name, office_code))
    conn.commit()
    conn.close()

# 天気予報をDBに保存
def save_forecast(region_code, forecast_date, weather_text, max_temp, min_temp, pop):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    fetched_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO forecasts (region_code, forecast_date, fetched_at, weather_text, max_temp, min_temp, pop)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (region_code, forecast_date, fetched_at, weather_text, max_temp, min_temp, pop))
    
    conn.commit()
    conn.close()

# DBから最新の天気予報を取得
def get_latest_forecast(region_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 最新のfetched_atを取得
    cursor.execute('''
        SELECT MAX(fetched_at) FROM forecasts WHERE region_code = ?
    ''', (region_code,))
    
    latest_fetched = cursor.fetchone()[0]
    
    if not latest_fetched:
        conn.close()
        return []
    
    # 最新の取得日時のデータのみを取得（日付でユニーク）
    cursor.execute('''
        SELECT DISTINCT 
            id, region_code, 
            DATE(forecast_date) as forecast_date, 
            fetched_at, weather_text, max_temp, min_temp, pop
        FROM forecasts
        WHERE region_code = ? AND fetched_at = ?
        GROUP BY DATE(forecast_date)
        ORDER BY forecast_date ASC
    ''', (region_code, latest_fetched))
    
    results = cursor.fetchall()
    conn.close()
    return results

# 特定の取得日時の天気予報を取得
def get_forecast_by_time(region_code, fetched_at):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 指定された取得日時のデータのみを取得（日付でユニーク）
    cursor.execute('''
        SELECT DISTINCT 
            id, region_code, 
            DATE(forecast_date) as forecast_date, 
            fetched_at, weather_text, max_temp, min_temp, pop
        FROM forecasts
        WHERE region_code = ? AND fetched_at = ?
        GROUP BY DATE(forecast_date)
        ORDER BY forecast_date ASC
    ''', (region_code, fetched_at))
    
    results = cursor.fetchall()
    conn.close()
    return results

# 取得日時の一覧を取得
def get_fetch_history(region_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT fetched_at FROM forecasts
        WHERE region_code = ?
        ORDER BY fetched_at DESC
    ''', (region_code,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def main(page: ft.Page):
    # データベース初期化
    init_database()
    
    # アプリ設定
    page.title = "天気予報アプリ（SQLite版）"
    page.window_width = 1000
    page.window_height = 700
    page.padding = 20

    # 現在選択中の地域
    current_region = {"code": None, "name": None, "office_code": None}
    current_fetched_at = {"value": None}  # 現在表示中の取得日時
    
    # 表示エリア（スクロール可能に）
    weather_display = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    # 履歴ドロップダウン
    history_dropdown = ft.Dropdown(
        label="過去の予報を選択",
        width=300,
        on_change=lambda e: on_history_select(e.control.value),
        visible=False
    )
    
    # 地域一覧ドロップダウン
    region_dropdown = ft.Dropdown(
        label="地域を選択",
        width=300,
        on_change=lambda e: on_region_select(e.control.value)
    )
    
    def load_regions():
        """地域一覧をAPIから取得してドロップダウンに設定"""
        try:
            res = requests.get(AREA_URL).json()
            options = []
            
            # 全国の地域を取得
            # センター（地方）ごとにループ
            for center_code, center_info in res["centers"].items():
                # その地方に属する県（オフィス）をループ
                for office_code in center_info.get("children", []):
                    office_info = res["offices"][office_code]
                    office_name = office_info["name"]
                    
                    # その県に属する地域（class10s）をループ
                    for region_code in office_info.get("children", []):
                        if region_code in res["class10s"]:
                            region_name = res["class10s"][region_code]["name"]
                            
                            # ドロップダウンに追加
                            options.append(
                                ft.dropdown.Option(
                                    key=f"{office_code}|{region_code}|{region_name}",
                                    text=f"{office_name} - {region_name}"
                                )
                            )
                            
                            # DBに地域情報を保存
                            save_region(region_code, region_name, office_code)
            
            region_dropdown.options = options
            page.update()
            
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"エラー: {e}"))
            page.snack_bar.open = True
            page.update()
    
    def on_region_select(value):
        """地域選択時の処理"""
        if not value:
            return
        
        parts = value.split("|")
        current_region["office_code"] = parts[0]
        current_region["code"] = parts[1]
        current_region["name"] = parts[2]
        current_fetched_at["value"] = None
        
        # 履歴を更新
        update_history_dropdown()
        
        # DBから表示
        display_from_db()
    
    def on_history_select(value):
        """履歴選択時の処理"""
        if not value:
            return
        
        current_fetched_at["value"] = value
        display_from_db()
    
    def update_history_dropdown():
        """履歴ドロップダウンを更新"""
        if not current_region["code"]:
            history_dropdown.visible = False
            history_dropdown.options = []
            page.update()
            return
        
        history = get_fetch_history(current_region["code"])
        
        if history:
            options = [
                ft.dropdown.Option(
                    key=h[0],
                    text=f"📅 {h[0]}"
                )
                for h in history
            ]
            # 最新を先頭に追加
            options.insert(0, ft.dropdown.Option(key="latest", text="🆕 最新"))
            
            history_dropdown.options = options
            history_dropdown.value = "latest"
            history_dropdown.visible = True
        else:
            history_dropdown.visible = False
            history_dropdown.options = []
        
        page.update()
    
    def fetch_weather():
        """気象庁APIから天気予報を取得してDBに保存"""
        if not current_region["code"]:
            page.snack_bar = ft.SnackBar(ft.Text("地域を選択してください"))
            page.snack_bar.open = True
            page.update()
            return
        
        weather_display.controls = [ft.ProgressRing()]
        page.update()
        
        try:
            url = f"{FORECAST_URL_BASE}{current_region['office_code']}.json"
            response = requests.get(url)
            data = response.json()
            
            # data[0]: 今日・明日・明後日の短期予報
            if len(data) > 0:
                time_series = data[0]["timeSeries"]
                
                # timeSeries[0]: 天気・風・波
                weather_time_series = time_series[0]
                weather_times = weather_time_series["timeDefines"]
                
                # 選択した地域のデータを探す
                weather_area = next(
                    (area for area in weather_time_series["areas"] 
                     if area["area"]["code"] == current_region["code"]), 
                    None
                )
                
                # timeSeries[1]: 降水確率
                pop_time_series = time_series[1]
                pop_times = pop_time_series["timeDefines"]
                pop_area = next(
                    (area for area in pop_time_series["areas"] 
                     if area["area"]["code"] == current_region["code"]), 
                    None
                )
                
                # timeSeries[2]: 気温（代表地点）
                temp_time_series = time_series[2]
                temp_area = temp_time_series["areas"][0] if len(temp_time_series["areas"]) > 0 else None
                temp_times = temp_time_series["timeDefines"]
                
                if weather_area:
                    # 天気データごとにDBに保存
                    for i, time_str in enumerate(weather_times):
                        forecast_date = time_str.split("T")[0]
                        
                        # この日付の気温を探す
                        max_temp = ""
                        min_temp = ""
                        
                        if temp_area and "temps" in temp_area:
                            # temp_timesから該当する日付のインデックスを探す
                            for j, temp_time in enumerate(temp_times):
                                temp_date = temp_time.split("T")[0]
                                
                                if temp_date == forecast_date and j < len(temp_area["temps"]):
                                    # 時刻で判定（09:00が最高気温、00:00が最低気温）
                                    temp_hour = temp_time.split("T")[1].split(":")[0]
                                    
                                    if temp_hour == "09":
                                        max_temp = temp_area["temps"][j]
                                    elif temp_hour == "00":
                                        min_temp = temp_area["temps"][j]
                        
                        # 降水確率: その日のデータから代表値を取得
                        pop = ""
                        if pop_area and "pops" in pop_area:
                            # この日付に該当する降水確率を取得
                            pops_for_day = []
                            for j, pop_time in enumerate(pop_times):
                                pop_date = pop_time.split("T")[0]
                                if pop_date == forecast_date and j < len(pop_area["pops"]):
                                    if pop_area["pops"][j]:  # 空文字でない場合
                                        pops_for_day.append(pop_area["pops"][j])
                            
                            # その日の最大降水確率を使用
                            if pops_for_day:
                                try:
                                    pop = str(max([int(p) for p in pops_for_day if p]))
                                except:
                                    pop = pops_for_day[0]
                        
                        save_forecast(
                            current_region["code"],
                            time_str,
                            weather_area["weathers"][i] if i < len(weather_area["weathers"]) else "",
                            max_temp,
                            min_temp,
                            pop
                        )
            
            # data[1]: 週間予報（4日目以降）
            if len(data) > 1:
                weekly_series = data[1]["timeSeries"]
                
                # timeSeries[0]: 天気・降水確率
                if len(weekly_series) > 0:
                    weather_weekly = weekly_series[0]
                    weekly_times = weather_weekly["timeDefines"]
                    
                    # 県全体のデータを探す（週間予報は県単位）
                    # まず選択中の地域コードで探す
                    weekly_area = None
                    for area in weather_weekly["areas"]:
                        area_code = area["area"]["code"]
                        # 地域コードまたは県コードで一致するか確認
                        if area_code == current_region["code"] or area_code == current_region["office_code"]:
                            weekly_area = area
                            break
                    
                    # timeSeries[1]: 気温
                    temp_weekly = None
                    temp_weekly_times = []
                    if len(weekly_series) > 1:
                        temp_weekly = weekly_series[1]["areas"][0] if len(weekly_series[1]["areas"]) > 0 else None
                        temp_weekly_times = weekly_series[1]["timeDefines"]
                    
                    if weekly_area:
                        # 週間予報のデータを保存
                        for i, time_str in enumerate(weekly_times):
                            forecast_date = time_str.split("T")[0]
                            
                            # 天気情報（天気コードを天気テキストに変換）
                            weather_text = ""
                            if "weatherCodes" in weekly_area and i < len(weekly_area["weatherCodes"]):
                                weather_code = weekly_area["weatherCodes"][i]
                                weather_text = get_weather_text(weather_code)
                            elif "weathers" in weekly_area and i < len(weekly_area["weathers"]):
                                # 既に天気テキストがある場合はそのまま使用
                                weather_text = weekly_area["weathers"][i]
                            
                            # 降水確率
                            pop = ""
                            if "pops" in weekly_area and i < len(weekly_area["pops"]):
                                pop = weekly_area["pops"][i]
                            
                            # 気温（週間予報の場合は最高・最低の予測範囲がある）
                            max_temp = ""
                            min_temp = ""
                            
                            if temp_weekly:
                                # 日付が一致するインデックスを探す
                                for j, temp_time in enumerate(temp_weekly_times):
                                    temp_date = temp_time.split("T")[0]
                                    if temp_date == forecast_date:
                                        # 最低気温
                                        if "tempsMin" in temp_weekly and j < len(temp_weekly["tempsMin"]):
                                            min_temp = temp_weekly["tempsMin"][j]
                                        
                                        # 最高気温
                                        if "tempsMax" in temp_weekly and j < len(temp_weekly["tempsMax"]):
                                            max_temp = temp_weekly["tempsMax"][j]
                                        break
                            
                            save_forecast(
                                current_region["code"],
                                time_str,
                                weather_text,
                                max_temp,
                                min_temp,
                                pop
                            )
            
            page.snack_bar = ft.SnackBar(ft.Text("✅ 天気予報を取得しました"))
            page.snack_bar.open = True
            
            # 履歴を更新
            update_history_dropdown()
            
            # DBから表示
            display_from_db()
            
        except Exception as e:
            weather_display.controls = [ft.Text(f"エラー: {e}", color="red")]
            page.update()
    
    def display_from_db():
        """DBから天気予報を取得して表示"""
        if not current_region["code"]:
            return
        
        # 履歴から選択された場合は、その時点のデータを表示
        if current_fetched_at["value"] and current_fetched_at["value"] != "latest":
            forecasts = get_forecast_by_time(current_region["code"], current_fetched_at["value"])
            display_title = f"📍 {current_region['name']}の天気予報（{current_fetched_at['value']}時点）"
        else:
            forecasts = get_latest_forecast(current_region["code"])
            display_title = f"📍 {current_region['name']}の天気予報（最新）"
        
        if not forecasts:
            weather_display.controls = [
                ft.Text("データがありません。「天気予報を取得」ボタンを押してください")
            ]
            page.update()
            return
        
        # 表示用のカードを作成
        cards = []
        
        for forecast in forecasts:
            # forecast = (id, region_code, forecast_date, fetched_at, weather_text, max_temp, min_temp, pop)
            
            # 日付を見やすい形式に変換
            try:
                date_str = forecast[2]
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y年%m月%d日 (%a)')
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%Y年%m月%d日 (%a)')
            except:
                formatted_date = date_str
            
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.CALENDAR_TODAY, size=20, color=ft.Colors.BLUE_600),
                            ft.Text(
                                formatted_date,
                                size=16,
                                weight="bold",
                                color=ft.Colors.BLUE_900
                            ),
                        ], spacing=5),
                        ft.Divider(height=1),
                        ft.Row([
                            ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=18, color=ft.Colors.ORANGE_600),
                            ft.Text(f"天気: {forecast[4] if forecast[4] else '情報なし'}", size=15),
                        ], spacing=5),
                        ft.Row([
                            ft.Icon(ft.Icons.THERMOSTAT, size=18, color=ft.Colors.RED_400),
                            ft.Text(
                                f"最高気温: {forecast[5]}°C" if forecast[5] else "最高気温: --",
                                size=14
                            ),
                        ], spacing=5),
                        ft.Row([
                            ft.Icon(ft.Icons.THERMOSTAT, size=18, color=ft.Colors.BLUE_400),
                            ft.Text(
                                f"最低気温: {forecast[6]}°C" if forecast[6] else "最低気温: --",
                                size=14
                            ),
                        ], spacing=5),
                        ft.Row([
                            ft.Icon(ft.Icons.WATER_DROP, size=18, color=ft.Colors.LIGHT_BLUE_600),
                            ft.Text(
                                f"降水確率: {forecast[7]}%" if forecast[7] else "降水確率: --",
                                size=14
                            ),
                        ], spacing=5),
                        ft.Divider(height=1),
                        ft.Text(
                            f"📅 取得: {forecast[3]}",
                            size=10,
                            color="grey",
                            italic=True
                        ),
                    ], spacing=8),
                    padding=15,
                )
            )
            cards.append(card)
        
        weather_display.controls = [
            ft.Text(display_title, size=20, weight="bold"),
            ft.Column(cards, spacing=10)
        ]
        page.update()
    
    # ボタン
    fetch_button = ft.ElevatedButton(
        "天気予報を取得（APIから）",
        icon=ft.Icons.CLOUD_DOWNLOAD,
        on_click=lambda e: fetch_weather(),
        bgcolor=ft.Colors.BLUE_600,
        color=ft.Colors.WHITE
    )
    
    display_button = ft.ElevatedButton(
        "DBから表示",
        icon=ft.Icons.STORAGE,
        on_click=lambda e: display_from_db(),
        bgcolor=ft.Colors.GREEN_600,
        color=ft.Colors.WHITE
    )
    
    # レイアウト
    page.add(
        ft.Column([
            ft.Text("天気予報アプリ（SQLite版）", size=24, weight="bold"),
            ft.Divider(),
            region_dropdown,
            history_dropdown,
            ft.Row([fetch_button, display_button], spacing=10),
            ft.Divider(),
            ft.Container(
                content=weather_display,
                expand=True
            )
        ], spacing=15, expand=True)
    )
    
    # 初期化：地域一覧を読み込み
    load_regions()

ft.app(target=main)