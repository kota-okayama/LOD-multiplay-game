import requests
import json
import time
from typing import Optional, List, Dict, Union

class SteamGameFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        print("Steam Game Fetcher initialized...")

    def search_games(self, 
                    max_price: int = 2000,
                    min_price: int = 0,
                    min_reviews: int = 10,
                    count: int = 100,
                    region: Optional[str] = None,
                    genres: Optional[List[str]] = None,
                    tags: Optional[List[str]] = None) -> List[Dict]:
        """
        指定した条件でゲームを検索します
        """
        print(f"\nSearching for games with following criteria:")
        print(f"Price range: ¥{min_price} - ¥{max_price}")
        print(f"Region: {region if region else 'Global'}")
        if genres:
            print(f"Genres: {', '.join(genres)}")
        if tags:
            print(f"Tags: {', '.join(tags)}")

        try:
            # Steam Store の検索APIを使用
            search_url = "https://store.steampowered.com/api/storesearch"
            params = {
                "cc": region if region else "JP",
                "l": self._get_language_code(region) if region else "japanese",
                "category1": 998,  # ゲームカテゴリ
                "page": 1,
                "pagesize": 50
            }

            if genres:
                params["term"] = " ".join(genres)
            
            print("\nFetching games from Steam Store...")
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            search_data = response.json()

            if not search_data.get("items"):
                print("No games found in initial search")
                return []

            matching_games = []
            total_items = len(search_data["items"])
            print(f"Found {total_items} games in initial search")

            for i, item in enumerate(search_data["items"], 1):
                app_id = str(item["id"])
                
                # 詳細情報を取得
                details = self.get_game_details(app_id, region)
                if not details or "error" in details:
                    continue

                # 価格の取得と確認
                price = self._extract_price(details.get("price", {}).get("final_formatted", ""))
                
                print(f"\nChecking game {i}/{total_items}: {details.get('title', 'Unknown')}")
                if price is not None:
                    print(f"Price: ¥{price:,}")

                    if min_price <= price <= max_price:
                        review_count = details.get("total_reviews", 0)
                        print(f"Reviews: {review_count}")

                        if review_count >= min_reviews:
                            # ジャンルとタグの確認
                            game_genres = [g.lower() for g in details.get("genres", [])]
                            game_tags = [t.lower() for t in details.get("tags", [])]

                            matches_genres = not genres or any(g.lower() in game_genres for g in genres)
                            matches_tags = not tags or any(t.lower() in game_tags for t in tags)

                            if matches_genres and matches_tags:
                                print(f"✓ Added: {details['title']}")
                                print(f"  Genres: {', '.join(details['genres'])}")
                                matching_games.append(details)

                                if len(matching_games) >= count:
                                    print(f"\nReached target count of {count} games")
                                    return matching_games
                            else:
                                print("✗ Skipped: Does not match genre/tag criteria")
                        else:
                            print(f"✗ Skipped: Not enough reviews ({review_count})")
                    else:
                        print("✗ Skipped: Price outside range")
                else:
                    print("✗ Skipped: No valid price information")

                time.sleep(1)  # APIレート制限を考慮

            print(f"\nFound total of {len(matching_games)} matching games")
            return matching_games

        except requests.exceptions.RequestException as e:
            print(f"Error in API request: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return []

    def get_game_details(self, app_id: str, region: Optional[str] = None) -> Dict:
        """
        ゲームの詳細情報を取得します
        """
        try:
            store_url = "https://store.steampowered.com/api/appdetails"
            params = {
                "appids": app_id,
                "cc": region if region else "JP",
                "l": self._get_language_code(region) if region else "japanese"
            }

            response = requests.get(store_url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data or app_id not in data or not data[app_id].get("success"):
                return {"error": "Game information not found"}

            game_data = data[app_id]["data"]
            
            # レビュー情報を取得
            reviews_url = f"https://store.steampowered.com/appreviews/{app_id}"
            reviews_params = {
                "json": 1,
                "language": self._get_language_code(region) if region else "japanese"
            }
            
            reviews_response = requests.get(reviews_url, params=reviews_params)
            reviews_data = reviews_response.json()

            # 価格情報の取得
            price_info = game_data.get("price_overview", {})
            if price_info:
                price = {
                    "initial_formatted": price_info.get("initial_formatted", ""),
                    "final_formatted": price_info.get("final_formatted", ""),
                    "discount_percent": price_info.get("discount_percent", 0)
                }
            else:
                price = {
                    "initial_formatted": "価格情報なし",
                    "final_formatted": "価格情報なし",
                    "discount_percent": 0
                }

            return {
                "title": game_data.get("name", ""),
                "steam_appid": app_id,
                "genres": [genre.get("description", "") for genre in game_data.get("genres", [])],
                "tags": [tag.get("description", "") for tag in game_data.get("categories", [])],
                "developer": game_data.get("developers", []),
                "publisher": game_data.get("publishers", []),
                "release_date": game_data.get("release_date", {}).get("date", ""),
                "price": price,
                "total_reviews": reviews_data.get("query_summary", {}).get("total_reviews", 0)
            }

        except Exception as e:
            return {"error": str(e)}

    def _extract_price(self, price_str: str) -> Optional[int]:
        """
        価格文字列から数値を抽出します
        例: "¥1,980" → 1980
        """
        try:
            if not price_str or price_str == "価格情報なし" or price_str == "無料":
                return None
            # 数字のみを抽出（カンマと小数点を除去）
            num_str = ''.join(filter(str.isdigit, price_str))
            return int(num_str) if num_str else None
        except ValueError:
            print(f"Warning: Could not parse price string: {price_str}")
            return None

    def _get_language_code(self, region: str) -> str:
        language_mapping = {
            "JP": "japanese",
            "US": "english",
            "KR": "koreana",
            "CN": "schinese",
            "TW": "tchinese",
            "RU": "russian",
            "DE": "german",
            "FR": "french"
        }
        return language_mapping.get(region, "japanese")

def main():
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
            api_key = config.get("api_key")
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return

    fetcher = SteamGameFetcher(api_key)

    # 検索条件の設定
    search_params = {
        "max_price": 2000,    # 最大価格（円）
        "min_price": 0,     # 最小価格（円）
        "min_reviews": 10,   # 最小レビュー数
        "count": 1000,          # 取得数
        "region": "JP",       # 地域
        "genres": None, # ジャンル
        "tags": None  # タグ
    }

    # ゲームの検索
    games = fetcher.search_games(**search_params)

    if games:
        # 結果をJSONファイルに保存
        output_file = "filtered_games.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(games, f, ensure_ascii=False, indent=2)
        
        print("\nFound games summary:")
        for game in games:
            print(f"- {game['title']}")
            print(f"  Price: {game['price']['final_formatted']}")
            print(f"  Genres: {', '.join(game['genres'])}")
            print()
    else:
        print("\nNo games found matching the criteria")

if __name__ == "__main__":
    main()