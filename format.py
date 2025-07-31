
import json
from datetime import datetime
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

class SteamGamesLODConverter:
    def __init__(self):
        self.g = Graph()
        self.ex = Namespace("https://example.com/games/")
        self.schema = Namespace("http://schema.org/")
        
        self.g.bind("rdf", RDF)
        self.g.bind("rdfs", RDFS)
        self.g.bind("schema", self.schema)
        self.g.bind("ex", self.ex)

        self.define_classes()

    def define_classes(self):
        multiplayer_game = self.ex.MultiplayerGame
        japanese_multiplayer_game = self.ex.JapaneseMultiplayerGame

        self.g.add((multiplayer_game, RDF.type, RDFS.Class))
        self.g.add((multiplayer_game, RDFS.subClassOf, self.schema.VideoGame))
        self.g.add((japanese_multiplayer_game, RDF.type, RDFS.Class))
        self.g.add((japanese_multiplayer_game, RDFS.subClassOf, multiplayer_game))

    def parse_date(self, date_str: str) -> str:
        try:
            date = datetime.strptime(date_str, '%Y年%m月%d日')
            return date.strftime('%Y-%m-%d')
        except:
            return date_str

    def convert_price(self, price_str: str) -> str:
        try:
            return price_str.replace('¥', '').replace(',', '').strip()
        except:
            return "0"

    def extract_max_players(self, description: str) -> int:
        """
        説明文から最大プレイヤー数を抽出する
        """
        import re
        
        # プレイヤー数を示す可能性のあるパターン
        patterns = [
            r'(\d+)人対戦',
            r'(\d+)人でプレイ',
            r'(\d+)人まで',
            r'(\d+)プレイヤー',
            r'最大(\d+)人',
            r'(\d+)人マルチプレイ',
            r'(\d+)人同時プレイ',
            r'(\d+)人オンライン',
            r'(\d+)人の友達',
            r'(\d+)-player',
            r'up to (\d+) players',
            r'(\d+) players',
            r'1~(\d+)人',
            r'1-(\d+)人'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description)
            if matches:
                # 複数マッチした場合は最大値を取る
                return max(int(num) for num in matches)
        
        return None

    def calculate_avg_playtime(self, reviews: list) -> float:
        """
        レビューから平均プレイ時間を計算する
        """
        if not reviews:
            return None
            
        total_time = sum(review['author'].get('playtime_at_review', 0) for review in reviews)
        return round(total_time / len(reviews), 1) if len(reviews) > 0 else None

    def convert_game(self, game_data: dict) -> None:
        game_uri = self.ex[game_data['steam_appid']]
        
        self.g.add((game_uri, RDF.type, self.ex.JapaneseMultiplayerGame))
        self.g.add((game_uri, self.schema.name, Literal(game_data['title'])))
        
        # Steam URLをsameAsとして追加
        steam_url = f"https://store.steampowered.com/app/{game_data['steam_appid']}"
        self.g.add((game_uri, self.schema.sameAs, URIRef(steam_url)))
        
        # 説明文からプレイヤー数を抽出
        if 'description' in game_data:
            max_players = self.extract_max_players(game_data['description'])
            if max_players:
                self.g.add((game_uri, self.schema.maxPlayers, Literal(str(max_players), datatype=XSD.integer)))
        
        # レビューから平均プレイ時間を計算
        if 'detailed_reviews' in game_data:
            avg_playtime = self.calculate_avg_playtime(game_data['detailed_reviews'])
            if avg_playtime:
                self.g.add((game_uri, self.ex.averagePlaytime, Literal(str(avg_playtime), datatype=XSD.decimal)))
        
        if 'developer' in game_data:
            for dev in game_data['developer']:
                self.g.add((game_uri, self.schema.creator, Literal(dev)))

            if 'publisher' in game_data:
                for pub in game_data['publisher']:
                    self.g.add((game_uri, self.schema.publisher, Literal(pub)))

            if 'release_date' in game_data:
                release_date = self.parse_date(game_data['release_date'])
                self.g.add((game_uri, self.schema.datePublished, Literal(release_date)))

            if 'price' in game_data and 'final' in game_data['price']:
                price = self.convert_price(game_data['price']['final'])
                self.g.add((game_uri, self.schema.price, Literal(price)))

            if 'genres' in game_data:
                for genre in game_data['genres']:
                    self.g.add((game_uri, self.schema.genre, Literal(genre)))

            if 'categories' in game_data:
                multiplayer_modes = [
                    cat for cat in game_data['categories'] 
                    if any(term in cat for term in ['PvP', 'マルチプレイヤー', '協力'])
                ]
                for mode in multiplayer_modes:
                    self.g.add((game_uri, self.ex.multiplayerModes, Literal(mode)))

            if 'platforms' in game_data:
                platforms = [name for name, supported in game_data['platforms'].items() if supported]
                for platform in platforms:
                    self.g.add((game_uri, self.schema.operatingSystem, Literal(platform.capitalize())))

            if 'review_stats' in game_data:
                stats = game_data['review_stats']
                if 'total_reviews' in stats:
                    self.g.add((game_uri, self.schema.reviewCount, Literal(str(stats['total_reviews']))))
                if 'review_score_desc' in stats:
                    self.g.add((game_uri, self.schema.aggregateRating, Literal(stats['review_score_desc'])))

            if 'supported_languages' in game_data:
                langs = game_data['supported_languages'].split(', ')
                langs = [lang.split('<')[0] for lang in langs]
                for lang in langs:
                    if lang.strip():
                        self.g.add((game_uri, self.schema.inLanguage, Literal(lang.strip())))
                        
    def convert_games(self, games_data: list) -> None:
        for game_data in games_data:
            self.convert_game(game_data)
    
    def save_to_file(self, filename: str, format: str = 'turtle') -> None:
        # 一時ファイルに書き出し
        temp_filename = 'temp_' + filename
        self.g.serialize(destination=temp_filename, format=format)
        
        # ファイルを読み込んで置換
        with open(temp_filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # schema1 を schema に置換
        content = content.replace('schema1:', 'schema:')
        content = content.replace('@prefix schema1:', '@prefix schema:')
        
        # 最終ファイルに書き出し
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 一時ファイルを削除
        import os
        os.remove(temp_filename)

if __name__ == "__main__":
    try:
        with open('enriched_games_progress_10.json', 'r', encoding='utf-8') as f:
            games_data = json.load(f)

        converter = SteamGamesLODConverter()
        converter.convert_games(games_data)
        converter.save_to_file('steam_games.ttl')
        
        print("変換が完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")