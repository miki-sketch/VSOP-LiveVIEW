import { useState, useMemo } from 'react';
import { sendLog } from '../utils/logger';
import styles from './Candidates.module.css';

const STEPS = [
  { key: '検討済み', label: '検討済み' },
  { key: '手配開始', label: '手配開始' },
  { key: '手配完了', label: '手配完了' },
  { key: '配布済み', label: '配布済み' },
];

const STATUS_CLASS = {
  untouched:   styles.cardUntouched,
  reviewed:    styles.cardReviewed,
  ordered:     styles.cardOrdered,
  completed:   styles.cardCompleted,
  distributed: styles.cardDistributed,
};

function getStatus(candidate) {
  if (candidate['配布済み']) return 'distributed';
  if (candidate['手配完了']) return 'completed';
  if (candidate['手配開始']) return 'ordered';
  if (candidate['検討済み']) return 'reviewed';
  return 'untouched';
}

// LiveList.jsx と同じ実装（動作実績あり）
function extractYoutubeId(url) {
  if (!url) return null;
  const m = url.match(/(?:youtu\.be\/|[?&]v=)([\w-]{11})/);
  return m ? m[1] : null;
}

export default function Candidates({ candidates }) {
  // 初演済み（L列あり）を常に除外
  const active = useMemo(
    () => candidates.filter((c) => !c['初演']),
    [candidates]
  );

  // 会議日付の一覧（ユニーク・降順）
  const meetingDates = useMemo(() => {
    const set = new Set(active.map((c) => c['会議日付']).filter(Boolean));
    return [...set].sort((a, b) => (a > b ? -1 : 1));
  }, [active]);

  // デフォルト: 最新の日付
  const [selectedDate, setSelectedDate] = useState(() => meetingDates[0] ?? '');

  // selectedDate がリストにない場合は最新にフォールバック
  const currentDate = meetingDates.includes(selectedDate)
    ? selectedDate
    : meetingDates[0] ?? '';

  // フィルター & ソート
  const filtered = useMemo(() => {
    const rows = currentDate
      ? active.filter((c) => c['会議日付'] === currentDate)
      : active;
    return [...rows].sort((a, b) => {
      const pa = parseInt(a['選曲優先順位'], 10) || 999;
      const pb = parseInt(b['選曲優先順位'], 10) || 999;
      return pa - pb;
    });
  }, [active, currentDate]);

  if (active.length === 0) {
    return <p className={styles.empty}>選曲候補データがありません</p>;
  }

  return (
    <div className={styles.wrapper}>
      {/* フィルターバー */}
      <div className={styles.filterBar}>
        <label className={styles.filterLabel} htmlFor="meeting-date-select">
          会議日付:
        </label>
        <select
          id="meeting-date-select"
          className={styles.filterSelect}
          value={currentDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        >
          <option value="">すべて</option>
          {meetingDates.map((d) => (
            <option key={d} value={d}>
              {formatDate(d)}
            </option>
          ))}
        </select>
      </div>

      {/* カードグリッド */}
      <div className={styles.grid}>
        {filtered.map((c, i) => (
          <CandidateCard key={i} candidate={c} />
        ))}
      </div>
    </div>
  );
}

function CandidateCard({ candidate }) {
  const priority  = candidate['選曲優先順位'];
  const title     = candidate['楽曲名'];
  const vo1       = candidate['VO1'];
  const vo2       = candidate['VO2'];
  // 列名の大文字小文字ゆらぎに対応
  const youtubeUrl = candidate['演奏Youtube'] || candidate['演奏YouTube'] || '';
  const note      = candidate['備考'];
  const comment   = candidate['配布係コメント'];

  // デバッグログ（確認後に削除）
  console.log('[Candidates] keys:', Object.keys(candidate));
  console.log('[Candidates] url:', youtubeUrl);
  const videoId = extractYoutubeId(youtubeUrl);
  console.log('[Candidates] videoId:', videoId);

  const voLabel = vo2 ? `${vo1} / ${vo2}` : vo1;
  const status  = getStatus(candidate);
  const thumbUrl = videoId
    ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
    : null;

  return (
    <div className={`${styles.card} ${STATUS_CLASS[status]}`}>
      {/* 上段: メイン情報 */}
      <div className={styles.cardUpper}>
        {/* タイトル行 */}
        <div className={styles.topRow}>
          <div className={styles.titleGroup}>
            <span className={styles.priority}>#{priority}</span>
            <span className={styles.title}>{title}</span>
          </div>
          <div className={styles.metaGroup}>
            {voLabel && <span className={styles.vo}>VO: {voLabel}</span>}
            {thumbUrl && (
              <a
                className={styles.thumbLink}
                href={youtubeUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => { e.stopPropagation(); sendLog('play', { songName: title, source: 'candidates' }); }}
              >
                <img src={thumbUrl} alt={title} />
              </a>
            )}
          </div>
        </div>

        {/* 進捗バー */}
        <ProgressSteps candidate={candidate} />

        {/* 備考 */}
        {note && <div className={styles.note}>備考: {note}</div>}
      </div>

      {/* 下段: 配布係コメント（ある場合のみ） */}
      {comment && (
        <div className={styles.cardLower}>
          <span className={styles.commentIcon}>💬</span>
          <span className={styles.comment}>{comment}</span>
        </div>
      )}
    </div>
  );
}

function ProgressSteps({ candidate }) {
  return (
    <div className={styles.steps}>
      {STEPS.map((step, i) => {
        const done = !!candidate[step.key];
        const dateStr = candidate[step.key] ? formatDate(candidate[step.key]) : '未';
        const tooltip = `${step.label}: ${dateStr}`;
        return (
          <div key={step.key} className={styles.stepItem}>
            <div
              className={`${styles.stepDot} ${done ? styles.stepDotDone : ''}`}
              title={tooltip}
            />
            {i < STEPS.length - 1 && (
              <div className={`${styles.stepLine} ${done ? styles.stepLineDone : ''}`} />
            )}
            <div className={styles.stepMeta}>
              <span className={styles.stepLabel}>{step.label}</span>
              {done && <span className={styles.stepDate}>{formatDate(candidate[step.key])}</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr.replace(/\//g, '-'));
  if (isNaN(d)) return dateStr;
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`;
}
