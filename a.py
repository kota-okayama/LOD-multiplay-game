from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS
import json
from datetime import datetime

def convert_games_to_lod():
    # グラフの初期化
    g = Graph()
    
    # 名前空間の定義
    ex = Namespace("https://example.com/games/")
    schema1 = Namespace("http://schema.org/")
    
    # 名前空間のバインド
    g.bind("ex", ex)
    g.bind("rdfs", RDFS)
    g.bind("schema1", schema1)

    # クラス階層の定義
    g.add((ex.JapaneseMultiplayerGame, RDF.type, RDFS.Class))
    g.add((ex.JapaneseMultiplayerGame, RDFS.subClassOf, ex.MultiplayerGame))
    g.add((ex.MultiplayerGame, RDF.type, RDFS.Class))
    g.add((ex.MultiplayerGame, RDFS.subClassOf, schema1.VideoGame))

    # JSONデータの読み込み
    with open('enriched_games_progress_10', 'r', encoding='utf-8') as f:
        games_data = json.load(f)

    for game in games_data:
        game_uri = ex[game['steam_appid']]
        
        # 基本情報
        g.add((game_uri, RDF.type, ex.JapaneseMultiplayerGame))
        g.add((game_uri, schema1.name, Literal(game['title'])))
        
        # 開発者とパブリッシャー
        if 'developer' in game:
            for dev in game['developer']:
                g.add((game_uri, schema1.creator, Literal(dev)))
        if 'publisher' in game:
            for pub in game['publisher']:
                g.add((game_uri, schema1.publisher, Literal(pub)))

        # 発売日
        if 'release_date' in game:
            try:
                date = datetime.strptime(game['release_date'], '%Y年%m月%d日')
                release_date = date.strftime('%Y-%m-%d')
                g.add((game_uri, schema1.datePublished, Literal(release_date)))
            except:
                pass

        # 価格
        if 'price' in game and 'final' in game['price']:
            price = game['price']['final'].replace('¥', '').replace(',', '').strip()
            g.add((game_uri, schema1.price, Literal(price)))

        # ジャンル
        if 'genres' in game:
            for genre in game['genres']:
                g.add((game_uri, schema1.genre, Literal(genre)))

        # プラットフォーム
        if 'platforms' in game:
            for platform, supported in game['platforms'].items():
                if supported:
                    g.add((game_uri, schema1.operatingSystem, Literal(platform.capitalize())))

        # レビュー情報
        if 'review_stats' in game:
            stats = game['review_stats']
            if 'total_reviews' in stats:
                g.add((game_uri, schema1.reviewCount, Literal(str(stats['total_reviews']))))
            if 'review_score_desc' in stats:
                g.add((game_uri, schema1.aggregateRating, Literal(stats['review_score_desc'])))

        # マルチプレイヤー情報
        if 'categories' in game:
            multiplayer_modes = [
                cat for cat in game['categories']
                if any(term in cat for term in ['PvP', 'マルチプレイヤー', '協力'])
            ]
            for mode in multiplayer_modes:
                g.add((game_uri, ex.multiplayerModes, Literal(mode)))

        # 言語サポート
        if 'supported_languages' in game:
            langs = game['supported_languages'].split(', ')
            langs = [lang.split('<')[0] for lang in langs]  # HTMLタグを除去
            for lang in langs:
                if lang.strip():  # 空の文字列を除外
                    g.add((game_uri, schema1.inLanguage, Literal(lang.strip())))

    # ファイルに保存
    g.serialize(destination='steam_games.ttl', format='turtle')

if __name__ == "__main__":
    convert_games_to_lod()