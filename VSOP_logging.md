# ログ機能追加指示書

## 概要
ユーザーの行動ログをGAS経由でGoogleスプレッドシートに記録する。
将来的に「名前入力」方式に拡張できる設計にすること。

---

## ログ記録先
既存のGAS Web App URLを流用：
```
https://script.google.com/macros/s/AKfycbyoVXp7Au4e-oDHIm5w-4lo0dAqFWD09-fwMnj--m8pR3lobVdLsFclDy13Lf1TeOLg/exec
```

スプレッドシートの「アクセスログ」シートに記録する（シートは作成済み）。

---

## ログのデータ構造

```json
{
  "action": "log",
  "event": "access" | "search" | "play",
  "timestamp": "2026-03-17T18:00:00+09:00",
  "userName": "",
  "detail": {
    "page": "LiveList" など（eventがaccessの場合）,
    "keyword": "検索キーワード"（eventがsearchの場合）,
    "songName": "曲名"（eventがplayの場合）,
    "liveName": "ライブ名"（eventがplayの場合）
  }
}
```

`userName` は現時点では常に空文字 `""` で送る。将来的に名前を入れる箇所。

---

## フロントエンド側の実装

### src/utils/logger.js を新規作成

```js
import { GAS_URL } from '../config'

export async function sendLog(event, detail = {}) {
  const payload = {
    action: 'log',
    event,
    timestamp: new Date().toLocaleString('sv-SE', { timeZone: 'Asia/Tokyo' }).replace(' ', 'T') + '+09:00',
    userName: '',  // 将来ここにlocalStorage等から名前を取得する処理を入れる
    detail,
  }
  try {
    await fetch(GAS_URL, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  } catch (e) {
    // ログ失敗はサイレントに無視（UXに影響させない）
  }
}
```

### 記録するタイミング

| イベント | 場所 | detailの内容 |
|---|---|---|
| `access` | App.jsx のタブ切り替え時 | `{ page: 'LiveList' \| 'LiveDetail' \| 'SongSearch' }` |
| `access` | LiveDetail表示時 | `{ page: 'LiveDetail', liveName: 'ライブ名' }` |
| `search` | SongSearch.jsx の検索入力時（500msデバウンス） | `{ keyword: '入力値' }` |
| `play` | 視聴ボタンクリック時（LiveDetail・SongSearch両方） | `{ songName: '曲名', liveName: 'ライブ名' }` |

---

## GAS側の実装

既存の GAS スクリプトに `log` アクションを追加する。

### シート構成（作成済み）
「アクセスログ」シートの列構成：
`A: アクセス番号 | B: タイムスタンプ | C: イベント | D: ユーザー名 | E: 詳細`

### GASに追加するコード

```javascript
function handleLog(payload) {
  const ss = SpreadsheetApp.openById('1tiks8xZQukiy-xdzaSUzk-90BoKOv397S47i2HFkggU');
  const sheet = ss.getSheetByName('アクセスログ');
  if (!sheet) return 'error: sheet not found';

  // アクセス番号：ヘッダー行を除いたデータ行数 + 1 で採番
  const lastRow = sheet.getLastRow();
  const accessNo = lastRow; // 2行目が1番、3行目が2番...

  sheet.appendRow([
    accessNo,
    payload.timestamp,
    payload.event,
    payload.userName || '（匿名）',
    JSON.stringify(payload.detail),
  ]);
  return 'success';
}
```

既存の `doPost` 関数内に以下を追加：
```javascript
if (payload.action === 'log') return ContentService.createTextOutput(handleLog(payload));
```

---

## 作業手順

1. **GASを修正する**
   - GASスクリプトに `handleLog` 関数と `doPost` への分岐を追加
   - 「デプロイを管理」→「編集」から再デプロイ（URLは変わらない）

2. **フロントエンドを修正する**
   - `src/utils/logger.js` を新規作成
   - App.jsx・LiveDetail.jsx・SongSearch.jsx に `sendLog` 呼び出しを追加

3. `npm run build` でビルド確認後、git push → Vercel自動デプロイ

---

## 将来の名前入力への拡張方法（メモ）
- `logger.js` の `userName: ''` の箇所を `localStorage.getItem('vsop_user_name') || ''` に変えるだけ
- 名前入力UIは初回アクセス時のモーダルかヘッダーに小さく配置する想定
