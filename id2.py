import requests
import json
import time
from datetime import datetime
import os

class SteamGameFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"
        
    def get_all_apps(self):
        """
        Steam上の全アプリケーションのリストを取得します
        """
        try:
            url = f"{self.base_url}/ISteamApps/GetAppList/v2/"
            print("Fetching complete app list from Steam...")
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'applist' in data and 'apps' in data['applist']:
                apps = data['applist']['apps']
                print(f"Found {len(apps)} total applications")
                return apps
            return []
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching app list: {e}")
            return []

    def get_indie_games(self, max_price=2000, min_reviews=10, count=1000):
        """
        インディーゲームをフィルタリングして取得します
        """
        filtered_games = []
        processed_count = 0
        
        try:
            # 全アプリのリストを取得
            all_apps = self.get_all_apps()
            
            print(f"\nProcessing games to find indie titles...")
            for app in all_apps:
                app_id = str(app['appid'])
                
                # 進捗表示（1000アプリごと）
                processed_count += 1
                if processed_count % 1000 == 0:
                    print(f"Processed {processed_count} apps...")
                    
                    # 途中経過を保存
                    if filtered_games:
                        self.save_to_json(filtered_games, "indie_games_progress.json")
                
                # ゲームの詳細情報を取得
                details = self.get_game_details(app_id)
                
                if "error" not in details:
                    # インディーゲームかどうかをチェック
                    is_indie = any(genre.lower() == "インディー" for genre in details.get("genres", []))
                    
                    if is_indie:
                        # 価格チェック
                        price = self._extract_price(details["price"]["final"])
                        if price is not None and price <= max_price and price > 0:
                            # レビュー数チェック
                            if details.get("total_reviews", 0) >= min_reviews:
                                filtered_games.append(details)
                                print(f"\nFound indie game: {details['title']}")
                                print(f"Price: {details['price']['final']}")
                                print(f"Reviews: {details['total_reviews']}")
                                print(f"Genres: {', '.join(details['genres'])}")
                                
                                # 指定した数のゲームを見つけたら終了
                                if len(filtered_games) >= count:
                                    break
                
                time.sleep(1)  # APIレート制限を考慮
                
            return filtered_games
            
        except Exception as e:
            print(f"Error during indie game filtering: {e}")
            return filtered_games

    def get_game_details(self, app_id):
        """
        ゲームの詳細情報を取得します
        """
        url = "https://store.steampowered.com/api/appdetails"
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
                
                # ゲームタイプをチェック
                if game_data.get("type") != "game":
                    return {"error": "Not a game"}
                
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
                    "steam_appid": app_id,
                    "description": game_data.get("short_description", ""),
                    "genres": [genre.get("description", "") for genre in game_data.get("genres", [])],
                    "developer": game_data.get("developers", []),
                    "publisher": game_data.get("publishers", []),
                    "release_date": game_data.get("release_date", {}).get("date", ""),
                    "price": price,
                    "total_reviews": total_reviews,
                    "header_image": game_data.get("header_image", ""),
                    "platforms": game_data.get("platforms", {}),
                    "categories": [cat.get("description", "") for cat in game_data.get("categories", [])],
                    "initial_release_date": game_data.get("release_date", {}).get("date", ""),
                    "supported_languages": game_data.get("supported_languages", ""),
                    "metacritic": game_data.get("metacritic", {})
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

    def _extract_price(self, price_str):
        """
        価格文字列から数値を抽出します
        """
        try:
            if not price_str or price_str == "価格情報なし":
                return None
            return int(''.join(filter(str.isdigit, price_str)))
        except ValueError:
            return None

    def save_to_json(self, data, filename="indie_games_data.json"):
        """
        データをJSONファイルに保存します
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, ensure_ascii=False, indent=2, fp=f)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

def main():
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
            api_key = config.get("api_key")
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    fetcher = SteamGameFetcher(api_key)
    
    # フィルタリング条件を設定
    MAX_PRICE = 20000
    MIN_REVIEWS = 500
    GAME_COUNT = 100000
    
    print(f"Starting search for indie games...")
    print(f"Criteria: Price <= ¥{MAX_PRICE}, Reviews >= {MIN_REVIEWS}")
    
    # ゲームを取得
    games_data = fetcher.get_indie_games(
        max_price=MAX_PRICE,
        min_reviews=MIN_REVIEWS,
        count=GAME_COUNT
    )
    
    if not games_data:
        print("No indie games found matching the criteria")
        return
    
    # 最終結果を保存
    output_file = "indie_games_final.json"
    fetcher.save_to_json(games_data, output_file)
    
    # 結果のサマリーを表示
    print(f"\nFound {len(games_data)} indie games matching criteria")
    print("\nGenre distribution:")
    genre_counts = {}
    for game in games_data:
        for genre in game["genres"]:
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{genre}: {count} games")

if __name__ == "__main__":
    main()