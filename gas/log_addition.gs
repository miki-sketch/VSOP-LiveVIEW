// ====================================================
// 既存の doPost 関数内に以下の分岐を追加する
// （他のアクション分岐の前に追加）
// ====================================================

// doPost 内に追記:
// if (payload.action === 'log') return ContentService.createTextOutput(handleLog(payload));


// ====================================================
// handleLog 関数を追加する
// ====================================================

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
