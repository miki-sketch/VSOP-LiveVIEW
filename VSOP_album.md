# アルバム機能追加指示書

## 概要
ライブごとの写真アルバムを表示する新しいページを追加する。

---

## スプレッドシート情報

**アルバムシート**
- GID: `467135274`
- 列構成: A=ライブ番号, B=写真URL, C=キャプション, D=撮影者

CSV取得URL:
```
https://docs.google.com/spreadsheets/d/1tiks8xZQukiy-xdzaSUzk-90BoKOv397S47i2HFkggU/gviz/tq?tqx=out:csv&gid=467135274
```

---

## config.js の更新

GIDに以下を追加：
```js
album: '467135274',
```

---

## ファイル構成

```
src/pages/
  Album.jsx         ← 新規作成
  Album.module.css  ← 新規作成
```

---

## 画面遷移

- LiveDetail.jsx のライブ情報上部に「📷 アルバム」ボタンを追加
  - そのライブ番号のアルバムデータが1件以上ある場合のみ表示
  - クリックするとApp.jsxのtabを'album'に切り替え、selectedLiveIdを保持したまま遷移
- App.jsx に `tab === 'album'` の分岐を追加して Album.jsx を表示
- Album.jsx 上部に「← ライブ詳細に戻る」ボタンを表示

---

## App.jsx の変更

- tab の種類に `'album'` を追加
- `tab === 'album'` の時は Album コンポーネントを表示
- ヘッダーの戻るボタンは `tab === 'detail' || tab === 'album'` の時に表示

---

## Album.jsx の仕様

### データ取得
- App.jsx でアルバムデータも全件取得してpropsで渡す
- Album.jsx では `props.photos`（そのライブ番号でフィルタ済み）を受け取る

### ヘッダー部分
- ライブ名・日付を表示
- 「← ライブ詳細に戻る」ボタン

### 写真グリッド
- CSS Grid で横3列（スマホは2列）
- 各セル: 正方形、`object-fit: cover`
- 写真の下にキャプション・撮影者を表示（空の場合は非表示）
- 写真をクリックするとライトボックスで拡大表示

### ライトボックス
- クリックした写真をフルスクリーン表示
- 左右の矢印ボタンで前後の写真に移動
- キーボードの左右矢印キーでも移動可能
- ESCキーまたは背景クリックで閉じる
- 拡大時もキャプション・撮影者を下部に表示

---

## デザイン
- 既存の黒×ゴールドテーマを踏襲
- グリッドのギャップ: 8px
- 写真のホバー時: opacity 0.85 + cursor pointer
- ライトボックス背景: `rgba(0,0,0,0.92)`
- 矢印ボタン: ゴールド `#c9a84c`

---

## ログ記録
- アルバムページを開いた時: `sendLog('access', { page: 'Album', liveName })`
- 写真をクリックして拡大した時: `sendLog('play', { songName: '写真を閲覧', liveName })`
  ※ playイベントを流用してログに残す
