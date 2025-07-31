# 画像ファイルについて

このフォルダには、READMEファイルで使用する画像ファイルを保存します。

## 画像の追加方法

1. **画像ファイルをこのフォルダに追加**
   - データ構造図、フローチャート、結果グラフなどを配置
   - 推奨フォーマット: PNG, JPG, SVG
   - ファイル名は英数字とハイフンを使用（例：`data-flow.png`）

2. **README.mdで画像を参照**
   ```markdown
   ![説明文](images/画像ファイル名.png)
   ```

## 画像の最適化

- **ファイルサイズ**: 1MB以下を推奨
- **解像度**: 幅1200px以下が適切
- **形式**:
  - 図表・グラフ: PNG
  - フローチャート: SVG
  - スクリーンショット: PNG

## 使用例

```markdown
# データ構造図
![データ構造](images/data-structure.png)

# LOD変換フロー
![LOD変換フロー](images/lod-conversion-flow.png)

# Steam API連携図
![Steam API連携](images/steam-api-integration.png)
```

## 推奨する画像

- **data-structure.png**: データ構造の概要図
- **lod-conversion-flow.png**: LOD変換のフローチャート
- **steam-api-integration.png**: Steam API連携図
- **turtle-output-example.png**: Turtle形式出力例
- **json-structure.png**: JSON構造の説明図
- **system-architecture.png**: システム全体のアーキテクチャ図