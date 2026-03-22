import { useRef, useState, useEffect } from 'react';
import styles from './LiveList.module.css';

export default function LiveList({ lives, onSelect }) {
  const upcoming = lives.filter((l) => l['STATUS'] !== '済');
  const done = lives
    .filter((l) => l['STATUS'] === '済')
    .sort((a, b) => new Date(b['日付'].replace(/\//g, '-')) - new Date(a['日付'].replace(/\//g, '-')));

  return (
    <>
      <CustomScrollbar lives={lives} />

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
    </>
  );
}

/* ── カスタムスクロールバー ───────────────────────────────── */

function CustomScrollbar({ lives }) {
  const THUMB_H = 22; // つまみの高さ（固定）
  const MIN_GAP = 24; // バッジ間の最小間隔

  const [thumbTop, setThumbTop] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const [badges, setBadges] = useState([]); // { year, top }

  const barRef = useRef(null);
  const dragStartY = useRef(0);
  const dragStartScrollY = useRef(0);

  // ── 年バッジ位置計算 ──
  // badgeTop = (cardOffsetTop / totalScrollHeight) * barHeight
  useEffect(() => {
    const compute = () => {
      const bar = barRef.current;
      if (!bar) return;
      const barH = bar.clientHeight;
      const totalH = document.documentElement.scrollHeight;

      const cards = document.querySelectorAll('[data-year]');
      const raw = [];
      let prevYear = null;
      cards.forEach((card) => {
        const year = parseInt(card.dataset.year, 10);
        if (year !== prevYear) {
          prevYear = year;
          const offsetTop = card.getBoundingClientRect().top + window.scrollY;
          raw.push({ year, top: (offsetTop / totalH) * barH });
        }
      });

      // 重なり防止: 上から順に 24px 未満なら下にずらす
      const adjusted = [];
      for (const b of raw) {
        let top = b.top;
        if (adjusted.length > 0) {
          const prev = adjusted[adjusted.length - 1].top;
          if (top - prev < MIN_GAP) top = prev + MIN_GAP;
        }
        adjusted.push({ year: b.year, top });
      }
      setBadges(adjusted);
    };
    const t = setTimeout(compute, 300);
    return () => clearTimeout(t);
  }, [lives]);

  // ── スクロール → つまみ位置更新 ──
  useEffect(() => {
    const onScroll = () => {
      const bar = barRef.current;
      if (!bar) return;
      const barH = bar.clientHeight;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      if (maxScroll <= 0) return;
      const top = (window.scrollY / maxScroll) * (barH - THUMB_H);
      setThumbTop(Math.max(0, Math.min(top, barH - THUMB_H)));
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // ── マウスドラッグ ──
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsDragging(true);
    dragStartY.current = e.clientY;
    dragStartScrollY.current = window.scrollY;
  };

  useEffect(() => {
    if (!isDragging) return;
    const onMove = (e) => {
      const bar = barRef.current;
      if (!bar) return;
      const barH = bar.clientHeight;
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
      const delta = ((e.clientY - dragStartY.current) / (barH - THUMB_H)) * maxScroll;
      window.scrollTo(0, dragStartScrollY.current + delta);
    };
    const onUp = () => setIsDragging(false);
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    return () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
  }, [isDragging]);

  // ── タッチドラッグ ──
  const handleTouchStart = (e) => {
    dragStartY.current = e.touches[0].clientY;
    dragStartScrollY.current = window.scrollY;
  };
  const handleTouchMove = (e) => {
    const bar = barRef.current;
    if (!bar) return;
    const barH = bar.clientHeight;
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const delta = ((e.touches[0].clientY - dragStartY.current) / (barH - THUMB_H)) * maxScroll;
    window.scrollTo(0, dragStartScrollY.current + delta);
  };

  // 矢印に最も近い年バッジをアクティブ年として導出
  const activeYear = badges.length > 0
    ? badges.reduce((best, b) =>
        Math.abs(b.top - thumbTop) < Math.abs(best.top - thumbTop) ? b : best
      ).year
    : null;

  return (
    <div className={styles.scrollbarTrack} ref={barRef}>
      <div className={styles.scrollbarLine} />
      {badges.map((b) => (
        <div
          key={b.year}
          className={`${styles.yearBadge} ${b.year === activeYear ? styles.yearBadgeActive : ''}`}
          style={{ top: b.top }}
        >
          {b.year}
        </div>
      ))}
      <div
        className={`${styles.scrollbarThumb} ${isDragging ? styles.dragging : ''}`}
        style={{ top: thumbTop }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
      />
    </div>
  );
}

/* ── ライブカード ──────────────────────────────────────────── */

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
  const year = new Date(live['日付'].replace(/\//g, '-')).getFullYear();

  return (
    <div
      className={`${styles.card} ${isUpcoming ? styles.upcomingCard : ''}`}
      onClick={() => onSelect(live['ライブ番号'])}
      data-year={isNaN(year) ? undefined : year}
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
