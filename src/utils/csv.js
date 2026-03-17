import { csvUrl } from '../config';

/**
 * CSVテキストを配列of配列にパース（クォートや改行を考慮）
 */
function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuote = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];

    if (inQuote) {
      if (ch === '"' && next === '"') {
        field += '"';
        i++;
      } else if (ch === '"') {
        inQuote = false;
      } else {
        field += ch;
      }
    } else {
      if (ch === '"') {
        inQuote = true;
      } else if (ch === ',') {
        row.push(field);
        field = '';
      } else if (ch === '\n') {
        row.push(field);
        field = '';
        rows.push(row);
        row = [];
      } else if (ch === '\r') {
        // skip
      } else {
        field += ch;
      }
    }
  }
  if (field !== '' || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  return rows;
}

/**
 * GID を指定してCSVをfetchし、ヘッダー行をキーにしたオブジェクト配列を返す
 */
export async function fetchSheet(gid) {
  const res = await fetch(csvUrl(gid));
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
  const text = await res.text();
  const rows = parseCsv(text);
  if (rows.length < 2) return [];

  const headers = rows[0].map((h) => h.trim());
  return rows.slice(1).map((row) => {
    const obj = {};
    headers.forEach((h, i) => {
      obj[h] = (row[i] ?? '').trim();
    });
    return obj;
  });
}

/**
 * "HH:MM:SS" or "MM:SS" → 秒数に変換
 */
export function timeToSeconds(t) {
  if (!t) return null;
  const parts = t.split(':').map(Number);
  if (parts.some(isNaN)) return null;
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return null;
}

/**
 * 動画URL + STARTTIME → ジャンプURL
 */
export function buildVideoUrl(videoUrl, startTime) {
  if (!videoUrl) return null;
  let sec = null;
  if (startTime) {
    const num = Number(startTime);
    if (!isNaN(num) && num > 0) {
      sec = num;
    } else {
      sec = timeToSeconds(startTime);
    }
  }
  if (sec === null || sec === 0) return videoUrl;
  const sep = videoUrl.includes('?') ? '&' : '?';
  return `${videoUrl}${sep}t=${sec}`;
}
