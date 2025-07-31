import requests
import json
import time
from datetime import datetime
import os

class SteamGameFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://store.steampowered.com/api"
        
    def get_games_list(self, max_price=2000, min_reviews=1, count=10000):
        """
        指定した条件に合うゲームのリストを取得します
        """
        filtered_games = []
        
        try:
            # Steam の検索APIを使用してより多くのゲームを取得
            for start_index in range(0, count, 100):  # 100件ずつ取得
                search_url = "https://store.steampowered.com/api/storesearch/"
                search_params = {
                    "start": start_index,
                    "count": 100,
                    "maxprice": max_price,
                    "category1": 998,  # ゲームカテゴリ
                    "l": "japanese",
                    "cc": "jp"
                }
                
                print(f"Fetching games {start_index + 1} to {start_index + 100}...")
                
                response = requests.get(search_url, params=search_params)
                response.raise_for_status()
                search_data = response.json()
                
                if not search_data.get("items"):
                    print("No more games found")
                    break
                
                for game in search_data["items"]:
                    app_id = str(game['id'])
                    if app_id not in filtered_games:  # 重複を避ける
                        details = self.get_game_details(app_id)
                        
                        if "error" not in details:
                            if details.get("total_reviews", 0) >= min_reviews:
                                filtered_games.append(app_id)
                                price = details["price"]["final"]
                                print(f"Found game: {details.get('title')} - {price}")
                                
                                if len(filtered_games) >= count:
                                    return filtered_games
                        
                        time.sleep(1)  # APIレート制限を考慮
                
                time.sleep(2)  # ページ間の待機時間
            
            print(f"Found {len(filtered_games)} games matching criteria")
            return filtered_games
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching games list: {e}")
            return []

    def get_game_details(self, app_id):
        """
        指定したapp_idのゲーム情報を取得します
        """
        url = f"https://store.steampowered.com/api/appdetails"
        params = {
            "appids": app_id,
            "cc": "jp",
            "l": "japanese"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data[str(app_id)]["success"]:
                game_data = data[str(app_id)]["data"]
                
                # レビュー情報を取得
                reviews_url = f"https://store.steampowered.com/appreviews/{app_id}"
                reviews_params = {
                    "json": 1,
                    "language": "all",
                    "purchase_type": "all"
                }
                
                reviews_response = requests.get(reviews_url, params=reviews_params)
                reviews_data = reviews_response.json()
                total_reviews = reviews_data.get("query_summary", {}).get("total_reviews", 0)
                
                price_info = game_data.get("price_overview", {})
                price = {
                    "initial": price_info.get("initial_formatted", "価格情報なし"),
                    "final": price_info.get("final_formatted", "価格情報なし"),
                    "discount_percent": price_info.get("discount_percent", 0)
                }
                
                formatted_data = {
                    "title": game_data.get("name", ""),
                    "description": game_data.get("short_description", ""),
                    "genres": [genre.get("description", "") for genre in game_data.get("genres", [])],
                    "categories": [cat.get("description", "") for cat in game_data.get("categories", [])],
                    "developer": game_data.get("developers", []),
                    "publisher": game_data.get("publishers", []),
                    "release_date": game_data.get("release_date", {}).get("date", ""),
                    "price": price,
                    "total_reviews": total_reviews,
                    "header_image": game_data.get("header_image", ""),
                    "steam_appid": app_id
                }
                
                return formatted_data
            else:
                return {"error": "Game information not found"}
                
        except requests.exceptions.RequestException as e:
            return {"error": f"API request failed: {str(e)}"}
        except KeyError as e:
            return {"error": f"Data structure error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
            
    def get_multiple_games_data(self, app_ids):
        """
        複数のゲーム情報を取得します
        """
        games_data = []
        total = len(app_ids)
        
        for i, app_id in enumerate(app_ids, 1):
            print(f"Fetching data for game {app_id}... ({i}/{total})")
            game_data = self.get_game_details(app_id)
            if "error" not in game_data:
                games_data.append(game_data)
                # 100ゲームごとにファイルに保存（途中経過を保存）
                if i % 100 == 0:
                    self.save_to_json(games_data, f"games_data_partial_{i}.json")
                    print(f"Saved partial data for {i} games")
            
            time.sleep(1)  # APIレート制限を考慮
            
        return games_data
            
    def save_to_json(self, data, filename="game_data.json"):
        """
        データをJSONファイルに保存します
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, ensure_ascii=False, indent=2, fp=f)
            
def load_config(config_file="config.json"):
    """
    設定ファイルからAPIキーを読み込みます
    """
    try:
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Configuration file '{config_file}' not found")
            
        with open(config_file, 'r') as f:
            config = json.load(f)
            
        if 'api_key' not in config:
            raise KeyError("API key not found in configuration file")
            
        return config['api_key']
        
    except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
        print(f"Error loading configuration: {e}")
        return None

def main():
    # 設定ファイルからAPIキーを読み込み
    api_key = load_config()
    if not api_key:
        print("Failed to load API key from configuration file")
        return
    
    fetcher = SteamGameFetcher(api_key)
    
    # フィルタリング条件を設定
    MAX_PRICE = 20000
    MIN_REVIEWS = 1
    GAME_COUNT = 1000  # 取得するゲーム数
    
    # 条件に合うゲームのリストを取得
    print(f"Searching for games under ¥{MAX_PRICE} with at least {MIN_REVIEWS} reviews...")
    game_ids = fetcher.get_games_list(
        max_price=MAX_PRICE,
        min_reviews=MIN_REVIEWS,
        count=GAME_COUNT
    )
    
    if not game_ids:
        print("No games found matching the criteria")
        return
    
    # 取得したゲームの詳細情報を取得
    print(f"\nFetching detailed information for {len(game_ids)} games...")
    games_data = fetcher.get_multiple_games_data(game_ids)
    
    # 最終的なJSONファイルに保存
    output_file = "filtered_games_data_final.json"
    fetcher.save_to_json(games_data, output_file)
    
    # 結果を表示
    print(f"\nSuccessfully retrieved data for {len(games_data)} games")
    print(f"Data has been saved to {output_file}")
    
    # サマリー表示
    print("\nSummary of retrieved games:")
    genres_count = {}
    price_ranges = {"0-1000": 0, "1001-5000": 0, "5001-10000": 0, "10001+": 0}
    
    for game in games_data:
        # ジャンルのカウント
        for genre in game["genres"]:
            genres_count[genre] = genres_count.get(genre, 0) + 1
        
        # 価格帯のカウント
        price = int(''.join(filter(str.isdigit, game["price"]["final"]))) if game["price"]["final"] != "価格情報なし" else 0
        if price <= 1000:
            price_ranges["0-1000"] += 1
        elif price <= 5000:
            price_ranges["1001-5000"] += 1
        elif price <= 10000:
            price_ranges["5001-10000"] += 1
        else:
            price_ranges["10001+"] += 1
    
    print("\nGenre distribution:")
    for genre, count in sorted(genres_count.items(), key=lambda x: x[1], reverse=True):
        print(f"{genre}: {count} games")
    
    print("\nPrice range distribution:")
    for price_range, count in price_ranges.items():
        print(f"¥{price_range}: {count} games")

if __name__ == "__main__":
    main()