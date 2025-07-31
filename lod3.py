import json
import requests
import time
from typing import List, Dict
from pathlib import Path

class SteamGameCollector:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.api_key = self.config.get('api_key')
        if not self.api_key:
            raise ValueError("APIキーが設定ファイルに見つかりません")
        self.base_url = "https://api.steampowered.com"

    def _load_config(self, config_path: str) -> Dict:
        """設定ファイルを読み込む"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイル {config_path} が見つかりません")
        except json.JSONDecodeError:
            raise ValueError(f"設定ファイル {config_path} の形式が正しくありません")

    def get_indie_games(self, max_games: int = 100, output_file: str = "indie_games.json") -> List[Dict]:
        """インディータグを持つゲームを収集し、結果をJSONファイルに保存する"""
        indie_games = []
        start = 0
        
        try:
            while len(indie_games) < max_games:
                params = {
                    'key': self.api_key,
                    'start': start,
                    'max_results': 50,
                    'tags': 'indie',
                    'format': 'json'
                }
                
                response = requests.get(
                    f"{self.base_url}/IStoreService/GetAppList/v1/",
                    params=params
                )
                
                response.raise_for_status()
                games = response.json().get('response', {}).get('apps', [])
                
                if not games:
                    print("これ以上のゲームが見つかりません")
                    break
                
                for game in games:
                    app_id = game['appid']
                    details = self._get_game_details(app_id)
                    
                    if details:
                        indie_games.append(details)
                        print(f"ゲームを追加: {details.get('name', 'Unknown')}")
                    
                    if len(indie_games) >= max_games:
                        break
                    
                    time.sleep(1)  # API制限を考慮
                
                start += 50
            
            # 結果をJSONファイルに保存
            self._save_results(indie_games, output_file)
            
            return indie_games
            
        except requests.exceptions.RequestException as e:
            print(f"API呼び出し中にエラーが発生しました: {e}")
            return []

    def _get_game_details(self, app_id: int) -> Dict:
        """ゲームの詳細情報を取得する"""
        params = {
            'appids': app_id,
            'key': self.api_key
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/api/appdetails",
                params=params
            )
            response.raise_for_status()
            return response.json().get(str(app_id), {}).get('data', {})
        except requests.exceptions.RequestException as e:
            print(f"ゲームID {app_id} の詳細取得中にエラーが発生: {e}")
            return {}

    def _save_results(self, data: List[Dict], filename: str):
        """結果をJSONファイルに保存する"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"結果を {filename} に保存しました")
        except IOError as e:
            print(f"結果の保存中にエラーが発生: {e}")

if __name__ == "__main__":
    try:
        collector = SteamGameCollector()
        indie_games = collector.get_indie_games(max_games=100)
        print(f"収集したゲーム数: {len(indie_games)}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")