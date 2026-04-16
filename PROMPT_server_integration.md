# サーバー側連携プロンプト

以下の仕様に基づき、GitHub Pages リポジトリ `Mao_gathering` の `config.txt` と画像ファイルを管理する処理を実装してください。

---

## システム概要

VRChat ワールド内の UdonSharp スクリプト `ImageGalleryManager` が GitHub Pages 上の `config.txt` を定期取得し、どの画像を何枚・誰の投稿で表示するかを決定します。

---

## config.txt の仕様

### ファイルパス

```
https://<username>.github.io/Mao_gathering/config.txt
```

### フォーマット

```
タイプ名:スロット番号:投稿者名
```

- **1行 = 1枚の画像**に対応
- `#` 始まりの行・空行は無視
- 投稿者名は省略可能（例: `nature:001:`）
- スロット番号は 001～100 の範囲（画像ファイル名の連番と一致）
- エントリの追加・削除は他の行に影響しない

### 例

```
nature:001:illusive_isc
nature:002:Ruby3dayo
city:001:illusive_isc
food:001:Another674
food:003:Another674
food:005:Ruby3dayo
```

---

## 画像ファイルの仕様

### URL パターン

```
https://<username>.github.io/Mao_gathering/images/{タイプ名}/{3桁連番}.jpg
```

例: `images/nature/001.jpg`, `images/nature/002.jpg`

### 連番ルール

- config.txt のスロット番号 = 画像ファイル名
- 例: `nature:003:xxx` → `images/nature/003.jpg`
- **スロットは 100 枚固定**。抹け番があっても他のスロットに影響しない

---

## UdonSharp 側のマッピング（参考）

`imageUrls[]` のレイアウト:

```
[0..99]    = nature/001.jpg 〜 nature/100.jpg
[100..199] = city/001.jpg   〜 city/100.jpg
[200..299] = food/001.jpg   〜 food/100.jpg
```

タイプの順番は Unity Inspector の `typeNames[]` で固定。config.txt はデータのみ管理し、タイプ順序の変更にはワール再アップが必要。

---

## サーバー側に期待する処理

1. **画像受け取り時**
   - タイプと投稿者名を受け取る
   - 対象タイプの空きスロット番号を找して `images/{タイプ}/NNN.jpg` に保存
   - `config.txt` に `タイプ名:NNN:投稿者名` を追加
   - 変更を git commit & push

2. **削除時**
   - `config.txt` から対象行を削除
   - 画像ファイルはそのまま残してよい（スロット番号復元不要）
   - 再利用する場合は同じスロット番号に上書き

3. **制約**
   - スロット番号は 001～100 の範囲
   - 同じタイプ内で同じスロット番号の重複不可

---

## permissions.txt（管理者・スタッフ権限）

```
https://<username>.github.io/Mao_gathering/permissions.txt
```

フォーマット:

```
[admin]
illusive_isc

[staff]
Ruby3dayo
Another674
```

投稿・削除操作の権限チェックに使用してください（`[admin]` or `[staff]` に含まれるユーザーのみ操作可）。
