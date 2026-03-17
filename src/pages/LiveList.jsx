import styles from './LiveList.module.css';

export default function LiveList({ lives, onSelect }) {
  const upcoming = lives.filter((l) => l['STATUS'] !== '済');
  const done = lives
    .filter((l) => l['STATUS'] === '済')
    .sort((a, b) => (a['日付'] < b['日付'] ? 1 : -1));

  return (
    <div className={styles.container}>
      {upcoming.length > 0 && (
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>UPCOMING</h2>
          {upcoming.map((live) => (
            <LiveCard key={live['ライブ番号']} live={live} onSelect={onSelect} />
          ))}
        </section>
      )}

      <section className={styles.section}>
        {upcoming.length > 0 && (
          <h2 className={styles.sectionTitle}>PAST LIVES</h2>
        )}
        {done.map((live) => (
          <LiveCard key={live['ライブ番号']} live={live} onSelect={onSelect} />
        ))}
      </section>
    </div>
  );
}

function extractYoutubeId(url) {
  if (!url) return null;
  const m = url.match(/(?:youtu\.be\/|[?&]v=)([\w-]{11})/);
  return m ? m[1] : null;
}

function LiveCard({ live, onSelect }) {
  const isUpcoming = live['STATUS'] !== '済';
  const videoId = extractYoutubeId(live['動画リンク']);
  const thumbUrl = videoId
    ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
    : null;

  return (
    <div
      className={`${styles.card} ${isUpcoming ? styles.upcomingCard : ''}`}
      onClick={() => onSelect(live['ライブ番号'])}
    >
      <div className={styles.cardBody}>
        <div className={styles.cardText}>
          <div className={styles.cardTop}>
            <div className={styles.dateBlock}>
              <span className={styles.date}>{formatDate(live['日付'])}</span>
              {live['開始時間'] && (
                <span className={styles.time}>{live['開始時間']}</span>
              )}
            </div>
            {isUpcoming && <span className={styles.upcomingBadge}>UPCOMING</span>}
          </div>

          <div className={styles.liveName}>{live['ライブ名']}</div>

          <div className={styles.meta}>
            {live['会場'] && <span>{live['会場']}</span>}
            {live['地域'] && <span className={styles.sep}>·</span>}
            {live['地域'] && <span>{live['地域']}</span>}
            {live['形式'] && <span className={styles.sep}>·</span>}
            {live['形式'] && <span>{live['形式']}</span>}
            {live['演奏時間'] && <span className={styles.sep}>·</span>}
            {live['演奏時間'] && <span>{live['演奏時間']}分</span>}
          </div>
        </div>

        {thumbUrl && (
          <a
            className={styles.thumb}
            href={live['動画リンク']}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            <img src={thumbUrl} alt={live['ライブ名']} />
          </a>
        )}
      </div>
    </div>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr.replace(/\//g, '-'));
  if (isNaN(d)) return dateStr;
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
}
