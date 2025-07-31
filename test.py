import requests
import json
import time
from bs4 import BeautifulSoup
from typing import Dict, Optional

class SteamGameDetailsTester:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.steam_api_url = "https://api.steampowered.com"
        self.store_api_url = "https://store.steampowered.com/api"
        self.request_delay = 1.0

    def get_game_details(self, app_id: str) -> Dict:
        """
        ゲームの基本情報を取得
        """
        print(f"\nFetching basic details for app ID: {app_id}")
        params = {
            'appids': app_id,
            'cc': 'jp',
            'l': 'japanese'
        }
        
        try:
            response = requests.get(f"{self.store_api_url}/appdetails", params=params)
            response.raise_for_status()
            time.sleep(self.request_delay)
            
            data = response.json()
            if data[app_id]['success']:
                game_data = data[app_id]['data']
                print(f"Successfully retrieved basic details for: {game_data.get('name', 'Unknown')}")
                return game_data
            else:
                print("Failed to get game details")
                return {}
        except Exception as e:
            print(f"Error fetching game details: {e}")
            return {}

    def get_achievements(self, app_id: str) -> Dict:
        """
        実績情報を取得
        """
        print("\nFetching achievements...")
        url = f"{self.steam_api_url}/ISteamUserStats/GetSchemaForGame/v2/?key={self.api_key}&appid={app_id}"
        try:
            response = requests.get(url)
            time.sleep(self.request_delay)
            data = response.json()
            
            achievements = data.get('game', {}).get('availableGameStats', {}).get('achievements', [])
            result = {
                'total_achievements': len(achievements),
                'achievements_list': achievements
            }
            print(f"Found {result['total_achievements']} achievements")
            return result
        except Exception as e:
            print(f"Error fetching achievements: {e}")
            return {'total_achievements': 0, 'achievements_list': []}

    def get_series_info(self, app_id: str) -> Dict:
        """
        シリーズ情報を取得
        """
        print("\nFetching series information...")
        url = f"https://store.steampowered.com/app/{app_id}/"
        try:
            response = requests.get(url, headers={'Accept-Language': 'ja,ja-JP'})
            time.sleep(self.request_delay)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            franchise_block = soup.find('div', {'class': 'franchise_notice'})
            if franchise_block:
                series_name = franchise_block.text.strip()
                series_url = franchise_block.find('a')['href'] if franchise_block.find('a') else None
                print(f"Found series: {series_name}")
                return {
                    'is_series': True,
                    'series_name': series_name,
                    'series_url': series_url
                }
            print("No series information found")
            return {'is_series': False, 'series_name': None, 'series_url': None}
        except Exception as e:
            print(f"Error fetching series info: {e}")
            return {'is_series': False, 'series_name': None, 'series_url': None}

    def get_developer_details(self, developer_name: str) -> Dict:
        """
        開発者の詳細情報を取得
        """
        print(f"\nFetching developer details for: {developer_name}")
        url = f"https://store.steampowered.com/developer/{developer_name}"
        try:
            response = requests.get(url)
            time.sleep(self.request_delay)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            games = soup.find_all('a', {'class': 'store_capsule'})
            website = None
            
            # 開発者の外部ウェブサイトを探す
            links = soup.find_all('a', {'class': 'linkbar'})
            for link in links:
                if 'Website' in link.text:
                    website = link['href']
            
            result = {
                'name': developer_name,
                'total_games': len(games),
                'website': website,
                'steam_url': url if response.status_code == 200 else None
            }
            print(f"Developer has {result['total_games']} games on Steam")
            return result
        except Exception as e:
            print(f"Error fetching developer details: {e}")
            return {'name': developer_name, 'total_games': 0, 'website': None, 'steam_url': None}

    def get_review_stats(self, app_id: str) -> Dict:
        """
        レビュー統計を取得
        """
        print("\nFetching review statistics...")
        url = f"https://store.steampowered.com/appreviews/{app_id}"
        params = {
            'json': 1,
            'language': 'all',
            'filter': 'all',
            'num_per_page': 100
        }
        
        try:
            response = requests.get(url, params=params)
            time.sleep(self.request_delay)
            data = response.json()
            
            summary = data.get('query_summary', {})
            result = {
                'total_reviews': summary.get('total_reviews', 0),
                'positive_reviews': summary.get('total_positive', 0),
                'negative_reviews': summary.get('total_negative', 0),
                'review_score': summary.get('review_score', 0),
                'review_score_desc': summary.get('review_score_desc', 'No reviews')
            }
            print(f"Found {result['total_reviews']} total reviews")
            return result
        except Exception as e:
            print(f"Error fetching review stats: {e}")
            return {'total_reviews': 0, 'positive_reviews': 0, 'negative_reviews': 0, 'review_score': 0, 'review_score_desc': 'Error'}

    def get_player_stats(self, app_id: str) -> Dict:
        """
        プレイヤー統計を取得
        """
        print("\nFetching player statistics...")
        url = f"{self.steam_api_url}/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={app_id}"
        try:
            response = requests.get(url)
            time.sleep(self.request_delay)
            data = response.json()
            
            current_players = data.get('response', {}).get('player_count', 0)
            print(f"Current players: {current_players}")
            return {'current_players': current_players}
        except Exception as e:
            print(f"Error fetching player stats: {e}")
            return {'current_players': 0}

    def get_complete_info(self, app_id: str) -> Dict:
        """
        全ての情報を収集して統合
        """
        print(f"\nGathering complete information for app ID: {app_id}")
        
        # 基本情報を取得
        basic_info = self.get_game_details(app_id)
        if not basic_info:
            print("Failed to get basic game information")
            return {}
            
        # 追加情報を取得
        achievements = self.get_achievements(app_id)
        series_info = self.get_series_info(app_id)
        review_stats = self.get_review_stats(app_id)
        player_stats = self.get_player_stats(app_id)
        
        # 開発者情報を取得
        developers = basic_info.get('developers', [])
        developer_details = []
        for dev in developers:
            developer_details.append(self.get_developer_details(dev))
        
        # すべての情報を統合
        complete_info = {
            'app_id': app_id,
            'name': basic_info.get('name'),
            'description': basic_info.get('short_description'),
            'detailed_description': basic_info.get('detailed_description'),
            'release_date': basic_info.get('release_date', {}).get('date'),
            'developers': developers,
            'developer_details': developer_details,
            'publishers': basic_info.get('publishers', []),
            'genres': [genre['description'] for genre in basic_info.get('genres', [])],
            'categories': [cat['description'] for cat in basic_info.get('categories', [])],
            'price': basic_info.get('price_overview', {}),
            'supported_languages': basic_info.get('supported_languages'),
            'achievements': achievements,
            'series_info': series_info,
            'review_stats': review_stats,
            'player_stats': player_stats,
            'header_image': basic_info.get('header_image'),
            'website': basic_info.get('website'),
            'platforms': basic_info.get('platforms', {})
        }
        
        return complete_info

    def save_to_json(self, data: Dict, filename: str):
        """
        データをJSONファイルとして保存
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\nData saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")

def main():
    # Steam API keyの設定
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
            api_key = config.get("api_key")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # テスト用のゲームID (例: Stardew Valley = 413150)
    app_id = input("Enter Steam App ID to test (e.g., 413150 for Stardew Valley): ")
    
    fetcher = SteamGameDetailsTester(api_key)
    game_info = fetcher.get_complete_info(app_id)
    
    if game_info:
        output_file = f"game_details_{app_id}.json"
        fetcher.save_to_json(game_info, output_file)
        
        # 基本情報を表示
        print("\nBasic information retrieved:")
        print(f"Title: {game_info.get('name')}")
        print(f"Developers: {', '.join(game_info.get('developers', []))}")
        print(f"Release Date: {game_info.get('release_date')}")
        print(f"Total Achievements: {game_info.get('achievements', {}).get('total_achievements')}")
        print(f"Current Players: {game_info.get('player_stats', {}).get('current_players')}")
    else:
        print("Failed to retrieve game information")

if __name__ == "__main__":
    main()