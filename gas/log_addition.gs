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
    formatDetail(payload.event, payload.detail || {}),
  ]);
  return 'success';
}

// ====================================================
// formatDetail: イベント種別・詳細に応じて人間が読める文字列を返す
// ====================================================

function formatDetail(event, detail) {
  if (event === 'access') {
    const page = detail.page || '';
    const keyword = detail.keyword || '';

    if (page === 'SongSearch' && keyword) {
      return '曲目検索：「' + keyword + '」を選択した';
    }
    if (page === 'SongSearch') return '曲目検索にアクセス';
    if (page === 'LiveList')   return 'LIVE一覧にアクセス';
    if (page === 'LiveDetail') return 'LIVE詳細にアクセス：' + (detail.liveName || '');
    if (page === 'Candidates') return '選曲候補にアクセス';
    if (page === 'Album')      return 'アルバムにアクセス：' + (detail.liveName || '');
    return 'アクセス：' + page;
  }

  if (event === 'play') {
    const song = detail.songName || '';
    const live = detail.liveName || '';
    if (song && live) return '「' + song + '」を視聴（' + live + '）';
    if (song)         return '「' + song + '」を視聴';
    return '動画を視聴';
  }

  if (event === 'search') {
    return '検索：「' + (detail.keyword || '') + '」';
  }

  return JSON.stringify(detail);
}
