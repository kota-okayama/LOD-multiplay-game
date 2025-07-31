# LOD Multiplay Game System

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Steam API](https://img.shields.io/badge/Steam-API-000000?style=flat-square&logo=steam&logoColor=white)
![RDF](https://img.shields.io/badge/RDF-Turtle-green?style=flat-square)
![LOD](https://img.shields.io/badge/Linked-Open_Data-blue?style=flat-square)

## 📖 概要

LOD Multiplay Game Systemは、Steam APIを使用してゲーム情報を収集し、Linked Open Data（LOD）形式に変換するPythonベースのシステムです。マルチプレイヤーゲームの詳細情報を構造化データとして活用できます。

## ✨ 主な機能

- **Steam API統合** - Steam Store APIからゲーム情報を自動取得
- **LOD変換** - RDF/Turtle形式でのLinked Open Data生成
- **ゲーム検索・フィルタリング** - 価格、ジャンル、地域別検索
- **データエンリッチメント** - レビュー情報、詳細メタデータの追加
- **インディーゲーム特化** - インディーゲームの詳細分析機能

## 🛠️ 技術スタック

- **言語**: Python 3.9+
- **API**: Steam Web API
- **データ形式**: RDF/Turtle, JSON
- **ライブラリ**: 
  - `requests` - HTTP通信
  - `json` - JSONデータ処理
  - `typing` - 型ヒント

## 📁 プロジェクト構造

```
LOD-jissyu/
├── LOD.py                           # メインのSteamゲーム取得クラス
├── LOD2.py                          # 拡張バージョン
├── en.py                            # 英語版ゲーム情報処理
├── test.py                          # テスト・デモスクリプト
├── filter.py                        # データフィルタリング機能
├── format.py                        # データフォーマット変換
├── lod/                             # LODデータ格納フォルダ
│   ├── indie_games_final.json       # 完成版インディーゲームデータ
│   └── indie_games_progress.json    # 処理中データ
├── *.json                           # 各種ゲームデータファイル
├── steam_games.ttl                  # Turtle形式LODファイル
├── steam_games_LOD.ttl              # LOD変換済みデータ
└── package.json / package-lock.json # Node.js依存関係（補助ツール）
```

## 🚀 セットアップ方法

### 前提条件

- Python 3.9以上
- Steam Web API Key（無料で取得可能）

### インストール手順

1. **リポジトリのクローン**
   ```bash
   git clone git@github.com:kota-okayama/LOD-multiplay-game.git
   cd LOD-multiplay-game
   ```

2. **Python仮想環境の作成**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # または
   venv\Scripts\activate     # Windows
   ```

3. **依存パッケージのインストール**
   ```bash
   pip install requests
   ```

4. **Steam API Keyの設定**
   ```bash
   # config.jsonを作成・編集
   {
     "steam_api_key": "YOUR_STEAM_API_KEY_HERE"
   }
   ```

   Steam API Keyは[こちら](https://steamcommunity.com/dev/apikey)から無料で取得できます。

## 📱 使用方法

### 基本的な使用例

```python
from LOD import SteamGameFetcher

# APIキーでインスタンス化
fetcher = SteamGameFetcher("your_steam_api_key")

# ゲーム検索の実行
games = fetcher.search_games(
    max_price=2000,        # 最大価格（円）
    min_price=0,           # 最小価格
    min_reviews=10,        # 最小レビュー数
    count=50,              # 取得件数
    region="JP",           # 地域設定
    genres=["Action", "Indie"],  # ジャンル指定
    tags=["Multiplayer"]   # タグ指定
)

print(f"取得したゲーム数: {len(games)}")
```

### LOD形式での出力

```python
# Turtle形式でのLOD出力
fetcher.export_to_turtle("steam_games_output.ttl")
```

### コマンドライン実行

```bash
# テストスクリプトの実行
python test.py

# 特定条件でのゲーム検索
python LOD.py --max-price 1500 --genre "Indie" --count 100
```

## 🎮 サポートするゲームタイプ

- **インディーゲーム** - Steam上のインディータイトル
- **マルチプレイヤーゲーム** - オンライン協力・対戦ゲーム
- **Early Access** - 早期アクセスタイトル
- **Free to Play** - 基本無料ゲーム

## 📊 データ出力形式

### JSON形式
```json
{
  "appid": 123456,
  "name": "Example Game",
  "price": 1980,
  "genres": ["Action", "Indie"],
  "tags": ["Multiplayer", "Co-op"],
  "reviews": {
    "positive": 85,
    "total": 100
  }
}
```

### Turtle (RDF) 形式
```turtle
@prefix steam: <http://steam.game/> .
@prefix dct: <http://purl.org/dc/terms/> .

steam:123456 a steam:Game ;
    dct:title "Example Game" ;
    steam:price 1980 ;
    steam:genre "Action", "Indie" .
```

## 🖼️ データビジュアライゼーション

<!-- 画像を追加する場合 -->
<!-- ![データ構造図](images/data-structure.png) -->
<!-- ![LOD関係図](images/lod-relations.png) -->

## 🔧 設定オプション

### 検索パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|-----------|------|
| `max_price` | int | 2000 | 最大価格（円） |
| `min_price` | int | 0 | 最小価格（円） |
| `min_reviews` | int | 10 | 最小レビュー数 |
| `count` | int | 100 | 取得ゲーム数 |
| `region` | str | "JP" | 地域コード |
| `genres` | List[str] | None | ジャンルリスト |
| `tags` | List[str] | None | タグリスト |

## 🤝 コントリビュート方法

1. このリポジトリをFork
2. 新しいブランチを作成 (`git checkout -b feature/new-feature`)
3. 変更をコミット (`git commit -m '新機能の追加'`)
4. ブランチにプッシュ (`git push origin feature/new-feature`)
5. Pull Requestを作成

### 開発環境の構築

```bash
# 開発用依存関係のインストール
pip install -r requirements-dev.txt

# テストの実行
python -m pytest tests/

# コードフォーマット
black *.py
```

## 📝 ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 👨‍💻 作成者

**Kota Okayama**
- GitHub: [@kota-okayama](https://github.com/kota-okayama)

## 🔮 今後の予定

- [ ] より多くのゲームプラットフォーム対応（Epic Games Store, GOG等）
- [ ] グラフデータベース（Neo4j）との統合
- [ ] RESTful API の提供
- [ ] WebUI でのデータ閲覧機能
- [ ] 機械学習によるゲーム推薦機能

## 🆘 トラブルシューティング

### よくある問題

**API制限エラー**
```
HTTP 429: Too Many Requests
```
- リクエスト頻度を下げる（`time.sleep()`を追加）
- API Keyが正しく設定されているか確認

**データ取得エラー**
```python
# エラーハンドリング例
try:
    games = fetcher.search_games()
except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
```

**メモリ不足**
- 大量データ処理時は`count`パラメータを小さく設定
- バッチ処理でデータを分割取得

## 🔗 関連リンク

- [Steam Web API Documentation](https://steamcommunity.com/dev)
- [RDF Turtle Specification](https://www.w3.org/TR/turtle/)
- [Linked Open Data Principles](https://www.w3.org/DesignIssues/LinkedData.html)