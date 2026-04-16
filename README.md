# Mao_gathering Gallery Data

GitHub Pages で公開する ImageGallery 用データリポジトリ。

## フォルダ構成

```
config.txt          ← ImageGalleryManager が読む設定ファイル
permissions.txt     ← StaffManager が読む権限リスト
images/
  nature/           ← 001.jpg, 002.jpg, ...
  city/             ← 001.jpg, 002.jpg, ...
  food/             ← 001.jpg, 002.jpg, ...
```

## 画像の追加方法

1. 対応フォルダに `001.jpg` から順番に画像を追加
2. `config.txt` の有効枚数を更新（例: `nature:100:5` → 5枚有効）
3. push するだけでワールド再アップ不要

## config.txt フォーマット

```
タイプ名:登録数:有効枚数
nature:100:50
```

## GitHub Pages 設定

Settings → Pages → Source: `main` ブランチ `/` (root)

公開後の config.txt URL:
`https://<username>.github.io/Mao_gathering/config.txt`

公開後の permissions.txt URL:
`https://<username>.github.io/Mao_gathering/permissions.txt`

## permissions.txt フォーマット

```
[admin]
AdminName1

[staff]
StaffName1
StaffName2
```

- `[admin]` / `[staff]` セクション区切り
- 空行・`#` 始まり行は無視
- StaffManager の `Staff List Url` にURLを設定する
