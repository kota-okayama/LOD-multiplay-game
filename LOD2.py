import requests
import json
import time
from datetime import datetime
import os

class SteamGameFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://store.steampowered.com/api"
        
    def get_games_list(self, max_price=2000, min_reviews=100, count=10000):
        """
        指定した条件に合うゲームのリストを取得します
        """
        # Steam の Featured Games APIを使用
        url = "https://store.steampowered.com/api/featured"
        filtered_games = []
        
        try:
            # まずはフィーチャードゲームを取得
            response = requests.get(url)
            response.raise_for_status()
            featured_data = response.json()
            
            # フィーチャードゲームから条件に合うものを抽出
            for section in ['featured_win', 'featured_mac', 'featured_linux']:
                if section in featured_data:
                    for game in featured_data[section]:
                        app_id = str(game['id'])
                        price = game.get('final_price', 0) / 100  # 価格は日本円に変換
                        
                        if price <= max_price and price > 0:
                            details = self.get_game_details(app_id)
                            if details.get("total_reviews", 0) >= min_reviews:
                                filtered_games.append(app_id)
                                print(f"Found game: {details.get('title')} - ¥{price}")
                                
                                if len(filtered_games) >= count:
                                    return filtered_games
            
            # 新着・人気ゲームも検索
            url = "https://store.steampowered.com/api/featuredcategories"
            response = requests.get(url)
            response.raise_for_status()
            categories_data = response.json()
            
            for category in ['top_sellers', 'new_releases', 'specials','indie']:
                if category in categories_data:
                    items = categories_data[category].get('items', [])
                    for game in items:
                        app_id = str(game['id'])
                        if app_id not in filtered_games:  # 重複を避ける
                            price = game.get('final_price', 0) / 100
                            
                            if price <= max_price and price > 0:
                                details = self.get_game_details(app_id)
                                if details.get("total_reviews", 0) >= min_reviews:
                                    filtered_games.append(app_id)
                                    print(f"Found game: {details.get('title')} - ¥{price}")
                                    
                                    if len(filtered_games) >= count:
                                        return filtered_games
                                        
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
                    "language": "all"
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
    MAX_PRICE = 20000  # 2000円以下
    MIN_REVIEWS = 100  # 100レビュー以上
    GAME_COUNT = 10000   # 取得するゲーム数
    
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
    print("\nFetching detailed information for each game...")
    games_data = fetcher.get_multiple_games_data(game_ids)
    
    # JSONファイルに保存
    output_file = "filtered_games_data.json"
    fetcher.save_to_json(games_data, output_file)
    
    # 結果を表示
    print(f"\nSuccessfully retrieved data for {len(games_data)} games")
    print(f"Data has been saved to {output_file}")
    
    # 取得したゲームの一覧を表示
    print("\nRetrieved games:")
    for game in games_data:
        price = game["price"]["final"]
        reviews = game["total_reviews"]
        print(f"- {game['title']}: {price} ({reviews} reviews)")

if __name__ == "__main__":
    main()