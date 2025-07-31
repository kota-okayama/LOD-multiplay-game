import json

def is_japanese_multiplayer_game(game_data):
    # 日本語対応チェック
    has_japanese = '日本語' in game_data['supported_languages']
    
    # マルチプレイヤー対応チェック
    multiplayer_categories = [
        'マルチプレイヤー',
        'オンライン協力プレイ',
        'オンラインPvP',
        'ローカル協力プレイ',
        'ローカルマルチプレイヤー'
    ]
    
    is_multiplayer = any(category in game_data['categories'] for category in multiplayer_categories)
    
    return has_japanese and is_multiplayer

# 入力ファイルを読み込み
with open('indie_games_progress.json', 'r', encoding='utf-8') as f:
    games = json.load(f)

# 日本語対応マルチプレイヤーゲームをフィルタリング
japanese_multiplayer_games = [game for game in games if is_japanese_multiplayer_game(game)]

# 結果を新しいJSONファイルに出力
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(japanese_multiplayer_games, f, ensure_ascii=False, indent=2)