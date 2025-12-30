import flet as ft
import requests
from datetime import datetime

#　URL定義
AREA_URL = "https://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL_BASE = "https://www.jma.go.jp/bosai/forecast/data/forecast/"

def main(page: ft.Page):
    # アプリ設定
    page.title = "天気予報アプリMU"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#ffffff" #　白背景
    page.window_width = 1200
    page.window_height = 850
    page.padding = 0

    # いろんな天気のパータンに応じてアイコンと色を返す（４つとか変わるやつはむずいので今回は省略）
    def get_weather_theme(text):
        if "雷" in text and "雨" in text:
            return "⛈️", ft.Colors.DEEP_PURPLE_600, ft.LinearGradient(colors=["#E9D5FF", "#C084FC"])
        if "雷" in text:
            return "⚡", ft.Colors.PURPLE_500, ft.LinearGradient(colors=["#F3E8FF", "#D8B4FE"])
        if "雪" in text:
            return "☃️", ft.Colors.CYAN_500, ft.LinearGradient(colors=["#E0F7FA", "#B2EBF2"])
        if "晴" in text and "雨" in text:
            return "🌦️", ft.Colors.ORANGE_400, ft.LinearGradient(colors=["#FFF7ED", "#BAE6FD"])
        if ("曇" in text or "くもり" in text) and "雨" in text:
            return "🌧️", ft.Colors.BLUE_GREY_600, ft.LinearGradient(colors=["#F1F5F9", "#CBD5E1"])
        if "雨" in text:
            return "🌧️", ft.Colors.BLUE_600, ft.LinearGradient(colors=["#E0F2FE", "#BAE6FD"])
        if "晴" in text and ("曇" in text or "くもり" in text):
             return "🌤️", ft.Colors.ORANGE_400, ft.LinearGradient(colors=["#FFF7ED", "#E2E8F0"])
        if "晴" in text:
            return "☀️", ft.Colors.ORANGE_600, ft.LinearGradient(colors=["#FFF7ED", "#FFEDD5"])
        if "曇" in text or "くもり" in text:
            return "☁️", ft.Colors.BLUE_GREY_400, ft.LinearGradient(colors=["#F1F5F9", "#E2E8F0"])
        
        # それ以外
        return "🌤️", ft.Colors.INDIGO_400, ft.LinearGradient(colors=["#F8FAFC", "#F1F5F9"])

    # --- 表示エリアの作成 ---
    content_area = ft.Column(expand=True, scroll="auto", spacing=30)

    # 今日の天気を表示するカードを作る関数
    def create_hero_card(name, weather_text, temp, pop, wind):
        emoji, theme_color, gradient_bg = get_weather_theme(weather_text)
        
        return ft.Container(
            gradient=gradient_bg,
            padding=40,
            border_radius=30,
            border=ft.border.all(1, ft.Colors.WHITE),
            shadow=ft.BoxShadow(blur_radius=20, color="#00000005"),
            content=ft.Row([
                # 左：大きなアイコン
                ft.Column([
                    ft.Text(emoji, size=120),
                    ft.Text(weather_text, size=20, weight="bold", color=theme_color),
                ], horizontal_alignment="center", width=220),
                
                # 中央：地域と気温
                ft.Column([
                    ft.Text(f"📍 {name}", size=16, color=ft.Colors.BLUE_GREY_400),
                    ft.Row([
                        ft.Text(str(temp), size=72, weight="bold", color=ft.Colors.BLUE_GREY_900),
                        ft.Container(
                            content=ft.Text("°C", size=24, color=ft.Colors.BLUE_GREY_900),
                            padding=ft.padding.only(top=20)
                        ),
                    ]),
                ], expand=True),

                # 右：詳細情報（降水確率・風）
                ft.Column([
                    # 降水確率バッジ
                    ft.Container(
                        content=ft.Row([ft.Icon(ft.Icons.WATER_DROP, size=18), ft.Text(f"降水確率 {pop}%")], spacing=5),
                        bgcolor=ft.Colors.WHITE, padding=12, border_radius=15
                    ),
                    # 風の情報バッジ
                    ft.Container(
                        content=ft.Row([ft.Icon(ft.Icons.AIR, size=18), ft.Text(wind, size=11)], spacing=5),
                        bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.WHITE), padding=12, border_radius=15, width=180
                    ),
                ], spacing=10)
            ])
        )

    # --- APIからデータを取ってきて表示を更新する ---
    def update_weather(office_code, region_code, region_name):
        # 読み込み中...を表示
        content_area.controls = [ft.Container(ft.ProgressRing(), padding=100, alignment=ft.alignment.center)]
        page.update()

        # 気象庁からデータを取得
        url = f"{FORECAST_URL_BASE}{office_code}.json"
        response = requests.get(url)
        data = response.json()

        # 必要なデータを取り出し
        # 時系列データ
        time_series = data[0]["timeSeries"]
        
        # 今日の天気
        weather_area = next(area for area in time_series[0]["areas"] if area["area"]["code"] == region_code)
        pop_area     = next(area for area in time_series[1]["areas"] if area["area"]["code"] == region_code)
        temp_area    = time_series[2]["areas"][0] # 気温は代表地点のものを使うことが多い

        # 今日の天気カードを作って表示エリアに追加
        hero_card = create_hero_card(
            region_name, 
            weather_area["weathers"][0],
            temp_area["temps"][1] if len(temp_area["temps"]) > 1 else "--", # 最高気温
            pop_area["pops"][0] if pop_area["pops"] else "0",
            weather_area["winds"][0]
        )
        content_area.controls = [hero_card]
        
        # 週間予報があれば追加
        if len(data) > 1:
            weekly_time_series = data[1]["timeSeries"]
            weekly_weather_area = weekly_time_series[0]["areas"][0]
            weekly_temp_area    = weekly_time_series[1]["areas"][0]
            
            # 横にスクロールできる列を作成
            weekly_row = ft.Row(scroll="auto", spacing=15)
            
            # 1日ずつループしてカードを作る
            for i in range(len(weekly_time_series[0]["timeDefines"])):
                
                code = weekly_weather_area["weatherCodes"][i]
                weather_type = "曇"

                if code.startswith("1"):
                    if code in ["102", "112", "113", "114", "118", "119"]:
                        weather_type = "晴雨"
                    elif code in ["100", "123", "124", "130", "131"]:
                        weather_type = "晴"
                    else:
                        weather_type = "晴曇"

                elif code.startswith("2"):
                    if code in ["202", "203", "206", "207", "212", "213", "214", "218", "219", "222", "224", "226"]:
                         weather_type = "曇雨"
                    elif code in ["201", "210", "211", "223", "230"]:
                         weather_type = "曇晴"
                    else:
                         weather_type = "曇"

                elif code.startswith("3"):
                    weather_type = "雨"
                    if code in ["313", "314", "317", "323", "324", "325"]:
                        weather_type = "雨曇"
                
                elif code.startswith("4"):
                    weather_type = "雪"

                emoji, _, _ = get_weather_theme(weather_type)
                
                # 日付のフォーマット（例: 01/05）
                date_str = weekly_time_series[0]["timeDefines"][i]
                date_dt = datetime.fromisoformat(date_str.replace('Z','+00:00'))
                formatted_date = date_dt.strftime("%m/%d")

                # 降水確率
                pop_str = weekly_weather_area['pops'][i]
                
                # 小さなカードを作成
                card = ft.Container(
                    width=100, padding=20, border_radius=20, bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, "#F1F5F9"),
                    content=ft.Column([
                        ft.Text(formatted_date, size=12, color=ft.Colors.BLUE_GREY_400),
                        ft.Text(emoji, size=30),
                        
                        # 降水確率（あれば表示）
                        ft.Container(
                            content=ft.Text(f"{pop_str}%", size=11, color=ft.Colors.BLUE_GREY_700),
                            bgcolor="#F1F5F9",
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=10,
                            visible=True if pop_str else False
                        ),

                        ft.Row([
                            ft.Text(f"{weekly_temp_area['tempsMin'][i]}°", color=ft.Colors.BLUE_400, size=12),
                            ft.Text(f"{weekly_temp_area['tempsMax'][i]}°", color=ft.Colors.RED_400, size=12),
                        ], spacing=5, alignment="center"),
                    ], horizontal_alignment="center", spacing=5)
                )
                weekly_row.controls.append(card)

            content_area.controls.append(ft.Text("📅 週間予報", size=18, weight="bold", color=ft.Colors.BLUE_GREY_800))
            content_area.controls.append(weekly_row)
        
        page.update()

    # --- サイドメニュー（地域リスト）を作る ---
    sidebar = ft.Column(scroll="auto", spacing=0)

    def init_menu():
        # エリア一覧を取得
        res = requests.get(AREA_URL).json()
        
        # センター（地方）ごとにループ
        for center_code, center_info in res["centers"].items():
            offices_widgets = []
            
            # 各県（オフィス）ごとにループ
            for office_code in center_info.get("children", []):
                office_info = res["offices"][office_code]
                
                # その県の中の地域（東京地方、伊豆諸島など）
                region_widgets = []
                for region_code in office_info.get("children", []):
                    if region_code in res["class10s"]:
                        region_name = res["class10s"][region_code]["name"]
                        
                        # クリックしたら update_weather を呼ぶボタン
                        tile = ft.ListTile(
                            title=ft.Text(region_name, size=13),
                            on_click=lambda e, oc=office_code, rc=region_code, rn=region_name: update_weather(oc, rc, rn)
                        )
                        region_widgets.append(tile)
                
                # 県のアコーディオンメニュー
                offices_widgets.append(
                    ft.ExpansionTile(
                        title=ft.Text(office_info["name"], size=14, weight="bold"),
                        controls=region_widgets
                    )
                )
            
            # 地方のアコーディオンメニュー
            sidebar.controls.append(
                ft.ExpansionTile(title=ft.Text(center_info["name"]), controls=offices_widgets)
            )
        page.update()

    # --- 全体のレイアウト組み立て ---
    page.appbar = ft.AppBar(
        title=ft.Text("天気予報", weight="bold", color=ft.Colors.BLUE_GREY_900),
        bgcolor=ft.Colors.WHITE, elevation=0
    )

    page.add(
        ft.Row([
            ft.Container(content=sidebar, width=280, bgcolor=ft.Colors.WHITE, padding=10),
            ft.Container(content=content_area, padding=40, expand=True)
        ], expand=True, spacing=0)
    )

    # 最初にメニューを作る
    init_menu()

ft.app(target=main)