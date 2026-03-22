# LiveList カスタムスクロールバー改修指示書

## 概要
既存の左側タイムラインバーを、ドラッグ操作でページスクロールができる
カスタムスクロールバーに改修する。

---

## 完成イメージ

```
│  ─  ← 目盛り線（細い横線）
│  
│  ─  ← 目盛り線
│ ┌──┐
│ │20│ ← ドラッグできるつまみ（大きめ）
│ │26│   スクロールに連動して上下に動く
│ └──┘   ドラッグするとページがスクロールする
│  ─  ← 目盛り線
│  
│  ─  ← 目盛り線
```

---

## 実装仕様

### バー全体
- 位置: ページ左側に `position: fixed` で固定（常に見える）
- 幅: 36px
- 高さ: `calc(100vh - 120px)`（ヘッダー分を除く）
- top: 60px（ヘッダーの高さ分）
- left: `max(0px, calc(50vw - 360px - 36px))`（コンテンツ左端に合わせる）
- 縦線: 中央に1px、ゴールド `#c9a84c`、opacity 0.3

### つまみ（年号バッジ）
- サイズ: 幅 36px、高さ 52px
- スタイル: 四角（border-radius: 4px）、ゴールド背景 `#c9a84c`、黒テキスト
- 表示: 4桁西暦を2段（`20` / `26`）、font-family: Bebas Neue、font-size: 14px
- カーソル: `grab`（ドラッグ中は `grabbing`）
- 位置: スクロール量に応じてバー内を上下に移動
  - `thumbTop = (scrollY / maxScrollY) * (barHeight - thumbHeight)`

### ドラッグ操作
- `mousedown` でドラッグ開始
- `mousemove` でつまみ位置を更新し、対応するスクロール位置に `window.scrollTo()`
- `mouseup` / `mouseleave` でドラッグ終了
- タッチ操作も対応（`touchstart` / `touchmove` / `touchend`）

### 目盛り線
- ライブカードの年が変わる境界位置に対応する場所に目盛りを表示
- 各目盛り: 幅8px の横線、ゴールド `#c9a84c`、opacity 0.5
- バー中央（縦線上）に左右対称に配置
- 年号ラベルなし（つまみに年号が表示されているので不要）
- 目盛りの位置計算:
  - 各年の最初のカードのページ上の位置（offsetTop）を取得
  - `markTop = (cardOffsetTop / maxScrollY) * barHeight`

### スクロール連動
- `window.addEventListener('scroll', ...)` でスクロールを監視
- スクロール位置に応じてつまみを移動
- 現在表示中の年号をつまみに表示（既存のIntersectionObserverロジックを流用）

### スマホ対応（768px未満）
- バー幅を 28px に縮小
- つまみサイズを 28px × 44px に縮小
- font-size: 11px

---

## 注意事項
- `position: fixed` を使うので、既存の `.timelineBar`（position: stickyベース）は廃止して作り直す
- ページの左余白（padding-left）をバーの幅分確保して、カードと重ならないようにする
- ドラッグ中にテキスト選択されないよう `user-select: none` を設定
- バーはLIVE一覧画面のみ表示（LiveDetail・SongSearchでは非表示）
