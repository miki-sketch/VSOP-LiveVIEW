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
      mode: 'no-cors',
      body: JSON.stringify(payload),
    })
  } catch (e) {
    // ログ失敗はサイレントに無視（UXに影響させない）
  }
}
