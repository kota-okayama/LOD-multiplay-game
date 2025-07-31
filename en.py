import json
import requests
import time
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import os

class SteamDataEnricher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.steam_api_url = "https://api.steampowered.com"
        self.store_api_url = "https://store.steampowered.com/api"
        self.request_delay = 1.0
    def get_review_stats(self, app_id: str) -> Dict:
        """
        レビュー統計を取得
        """
        print(f"\nFetching review statistics for app ID: {app_id}")
        url = f"https://store.steampowered.com/appreviews/{app_id}"
        params = {
            'json': 1,
            'language': 'all',
            'filter': 'all',
            'num_per_page': 100,
            'day_range': 365  # 過去1年のレビューを取得
        }
        
        try:
            response = requests.get(url, params=params)
            time.sleep(self.request_delay)
            data = response.json()
            
            summary = data.get('query_summary', {})
            
            # レビュースコアの計算（ポジティブレビューの割合）
            total_reviews = summary.get('total_reviews', 0)
            positive_reviews = summary.get('total_positive', 0)
            negative_reviews = summary.get('total_negative', 0)
            
            review_score = 0
            if total_reviews > 0:
                review_score = (positive_reviews / total_reviews) * 100

            result = {
                'total_reviews': total_reviews,
                'positive_reviews': positive_reviews,
                'negative_reviews': negative_reviews,
                'review_score': round(review_score, 2),
                'review_score_desc': summary.get('review_score_desc', 'No reviews'),
                'recent_reviews': {
                    'total': summary.get('total_reviews', 0),
                    'positive': summary.get('total_positive', 0),
                    'negative': summary.get('total_negative', 0)
                }
            }
            
            print(f"Found {result['total_reviews']} total reviews")
            print(f"Review score: {result['review_score']}%")
            return result
            
        except Exception as e:
            print(f"Error fetching review stats: {e}")
            return {
                'total_reviews': 0,
                'positive_reviews': 0,
                'negative_reviews': 0,
                'review_score': 0,
                'review_score_desc': 'Error',
                'recent_reviews': {
                    'total': 0,
                    'positive': 0,
                    'negative': 0
                }
            }

    def get_detailed_review_data(self, app_id: str, num_reviews: int = 100) -> List[Dict]:
        """
        詳細なレビューデータを取得
        """
        print(f"\nFetching detailed review data for app ID: {app_id}")
        url = f"https://store.steampowered.com/appreviews/{app_id}"
        params = {
            'json': 1,
            'language': 'japanese',  # 日本語レビューを優先
            'filter': 'all',
            'num_per_page': num_reviews,
            'review_type': 'all',
            'purchase_type': 'all'
        }
        
        try:
            response = requests.get(url, params=params)
            time.sleep(self.request_delay)
            data = response.json()
            
            reviews = data.get('reviews', [])
            processed_reviews = []
            
            for review in reviews:
                processed_review = {
                    'author': {
                        'steamid': review.get('author', {}).get('steamid'),
                        'playtime_forever': review.get('author', {}).get('playtime_forever', 0),
                        'playtime_at_review': review.get('author', {}).get('playtime_at_review', 0)
                    },
                    'voted_up': review.get('voted_up', False),
                    'votes_up': review.get('votes_up', 0),
                    'votes_funny': review.get('votes_funny', 0),
                    'weighted_vote_score': review.get('weighted_vote_score', 0),
                    'comment_count': review.get('comment_count', 0),
                    'steam_purchase': review.get('steam_purchase', False),
                    'received_for_free': review.get('received_for_free', False),
                    'written_during_early_access': review.get('written_during_early_access', False),
                    'timestamp_created': review.get('timestamp_created', 0),
                    'timestamp_updated': review.get('timestamp_updated', 0),
                    'review_text': review.get('review', '')
                }
                processed_reviews.append(processed_review)
            
            print(f"Processed {len(processed_reviews)} detailed reviews")
            return processed_reviews
            
        except Exception as e:
            print(f"Error fetching detailed review data: {e}")
            return []

    

    def process_json_file(self, input_filename: str, output_filename: str):
        """
        JSONファイルを処理して拡充データを追加
        """
        games = self.load_json_data(input_filename)
        if not games:
            return
        
        print(f"Processing {len(games)} games...")
        enriched_games = []
        
        for i, game in enumerate(games, 1):
            print(f"\nProcessing game {i}/{len(games)}")
            enriched_game = self.enrich_game_data(game)
            enriched_games.append(enriched_game)
            
            # 10ゲームごとに中間保存
            if i % 10 == 0:
                self.save_json_data(enriched_games, f"enriched_games_progress_{i}.json")
                print(f"Saved progress for {i} games")
        
        self.save_json_data(enriched_games, output_filename)
        print(f"\nProcessing completed. Enriched data saved to {output_filename}")

    def load_json_data(self, filename: str) -> List[Dict]:
        """
        既存のJSONファイルを読み込む
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
            return []

    def get_achievements(self, app_id: str) -> Dict:
        """
        実績情報を取得
        """
        url = f"{self.steam_api_url}/ISteamUserStats/GetSchemaForGame/v2/?key={self.api_key}&appid={app_id}"
        try:
            response = requests.get(url)
            time.sleep(self.request_delay)
            data = response.json()
            
            achievements = data.get('game', {}).get('availableGameStats', {}).get('achievements', [])
            return {
                'total_achievements': len(achievements),
                'achievements_list': achievements
            }
        except Exception as e:
            print(f"Error fetching achievements for {app_id}: {e}")
            return {'total_achievements': 0, 'achievements_list': []}

    def get_series_info(self, app_id: str) -> Dict:
        """
        シリーズ情報を取得
        """
        url = f"https://store.steampowered.com/app/{app_id}/"
        try:
            response = requests.get(url, headers={'Accept-Language': 'ja,ja-JP'})
            time.sleep(self.request_delay)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # フランチャイズブロックを探す
            franchise_block = soup.find('div', {'class': 'franchise_notice'})
            if franchise_block:
                series_name = franchise_block.text.strip()
                series_url = franchise_block.find('a')['href'] if franchise_block.find('a') else None
                return {
                    'is_series': True,
                    'series_name': series_name,
                    'series_url': series_url
                }
            return {'is_series': False, 'series_name': None, 'series_url': None}
        except Exception as e:
            print(f"Error fetching series info for {app_id}: {e}")
            return {'is_series': False, 'series_name': None, 'series_url': None}

    def get_developer_details(self, developer_name: str) -> Dict:
        """
        開発者の詳細情報を取得
        """
        url = f"https://store.steampowered.com/search/?developer={developer_name}"
        try:
            response = requests.get(url)
            time.sleep(self.request_delay)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 開発者のゲーム数を取得
            games = soup.find_all('a', {'class': 'search_result_row'})
            
            return {
                'name': developer_name,
                'total_games': len(games),
                'search_url': url
            }
        except Exception as e:
            print(f"Error fetching developer details for {developer_name}: {e}")
            return {'name': developer_name, 'total_games': 0, 'search_url': url}

    def get_playtime_stats(self, app_id: str) -> Dict:
        """
        プレイ時間統計を取得
        """
        url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={app_id}"
        try:
            response = requests.get(url)
            time.sleep(self.request_delay)
            data = response.json()
            
            return {
                'current_players': data.get('response', {}).get('player_count', 0)
            }
        except Exception as e:
            print(f"Error fetching playtime stats for {app_id}: {e}")
            return {'current_players': 0}

    def enrich_game_data(self, game_data: Dict) -> Dict:
        """
        ゲームデータを拡充
        """
        app_id = str(game_data['steam_appid'])
        print(f"\nEnriching data for {game_data['title']} (AppID: {app_id})")
        
        # レビュー統計を追加
        review_stats = self.get_review_stats(app_id)
        game_data['review_stats'] = review_stats
        
        # 詳細なレビューデータを追加
        detailed_reviews = self.get_detailed_review_data(app_id)
        game_data['detailed_reviews'] = detailed_reviews
        
        # 実績情報を追加
        achievements = self.get_achievements(app_id)
        game_data['achievements'] = achievements
        
        # シリーズ情報を追加
        series_info = self.get_series_info(app_id)
        game_data['series_info'] = series_info
        
        # 開発者詳細を追加
        developer_details = []
        for dev in game_data['developer']:
            details = self.get_developer_details(dev)
            developer_details.append(details)
        game_data['developer_details'] = developer_details
        
        # プレイ時間統計を追加
        playtime_stats = self.get_playtime_stats(app_id)
        game_data['playtime_stats'] = playtime_stats
        
        return game_data

    def process_json_file(self, input_filename: str, output_filename: str):
        """
        JSONファイルを処理して拡充データを追加
        """
        games = self.load_json_data(input_filename)
        if not games:
            return
        
        print(f"Processing {len(games)} games...")
        enriched_games = []
        
        for i, game in enumerate(games, 1):
            print(f"\nProcessing game {i}/{len(games)}")
            enriched_game = self.enrich_game_data(game)
            enriched_games.append(enriched_game)
            
            # 100ゲームごとに中間保存
            if i % 10 == 0:
                self.save_json_data(enriched_games, f"enriched_games_progress_{i}.json")
        
        self.save_json_data(enriched_games, output_filename)
        print(f"\nProcessing completed. Enriched data saved to {output_filename}")

    def save_json_data(self, data: List[Dict], filename: str):
        """
        JSONデータを保存
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Data saved to {filename}")
        except Exception as e:
            print(f"Error saving JSON data: {e}")

def main():
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
            api_key = config.get("api_key")
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    enricher = SteamDataEnricher(api_key)
    
    input_file = "output.json"
    output_file = "enriched_indie_games_with_reviews.json"
    
    print(f"Starting data enrichment process...")
    print(f"Reading from: {input_file}")
    print(f"Will save to: {output_file}")
    
    enricher.process_json_file(input_file, output_file)

if __name__ == "__main__":
    main()