import { useState, useMemo } from 'react';
import { buildVideoUrl } from '../utils/csv';
import styles from './SongSearch.module.css';

export default function SongSearch({ songs, lives }) {
  const [query, setQuery] = useState('');
  const [mobileView, setMobileView] = useState('list'); // 'list' | 'detail'

  const liveMap = useMemo(() => {
    const m = {};
    lives.forEach((l) => {
      m[l['ライブ番号']] = l;
    });
    return m;
  }, [lives]);

  // 曲名ごとにグループ化、演奏回数降順
  const grouped = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? songs.filter((s) => s['楽曲名'].toLowerCase().includes(q))
      : songs;

    const map = {};
    filtered.forEach((s) => {
      const name = s['楽曲名'];
      if (!map[name]) map[name] = [];
      map[name].push(s);
    });

    return Object.entries(map).sort((a, b) => b[1].length - a[1].length);
  }, [songs, query]);

  const [selectedSong, setSelectedSong] = useState(() => {
    // 初期選択: 後で grouped から先頭を取るが、
    // grouped は useMemo なので初期値はここでは null にして下で補完
    return null;
  });

  // 表示する選択曲: selectedSong が grouped に含まれていれば使う、なければ先頭
  const activeSong = useMemo(() => {
    if (grouped.length === 0) return null;
    const found = grouped.find(([name]) => name === selectedSong);
    return found ? found[0] : grouped[0][0];
  }, [grouped, selectedSong]);

  const activeEntries = useMemo(() => {
    if (!activeSong) return [];
    const found = grouped.find(([name]) => name === activeSong);
    return found ? found[1] : [];
  }, [grouped, activeSong]);

  const handleSelect = (songName) => {
    setSelectedSong(songName);
    setMobileView('detail');
  };

  return (
    <div className={styles.paneWrapper}>
      {/* 左ペイン: 曲一覧 */}
      <div className={`${styles.leftPane} ${mobileView === 'detail' ? styles.hiddenOnMobile : ''}`}>
        <div className={styles.searchBox}>
          <input
            className={styles.searchInput}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedSong(null); // 検索変更時は先頭に戻す
            }}
            placeholder="曲名を検索…"
          />
          {query && (
            <button className={styles.clearBtn} onClick={() => { setQuery(''); setSelectedSong(null); }}>
              ×
            </button>
          )}
        </div>

        <div className={styles.songList}>
          {grouped.length === 0 ? (
            <p className={styles.noResult}>一致する曲はありません</p>
          ) : (
            grouped.map(([songName, entries]) => (
              <button
                key={songName}
                className={`${styles.songRow} ${activeSong === songName ? styles.songRowActive : ''}`}
                onClick={() => handleSelect(songName)}
              >
                <span className={styles.songRowName}>{songName}</span>
                <span className={styles.songRowCount}>{entries.length}回</span>
              </button>
            ))
          )}
        </div>
      </div>

      {/* 右ペイン: 演奏履歴 */}
      <div className={`${styles.rightPane} ${mobileView === 'list' ? styles.hiddenOnMobile : ''}`}>
        {mobileView === 'detail' && (
          <button className={styles.mobileBackBtn} onClick={() => setMobileView('list')}>
            ← 曲一覧に戻る
          </button>
        )}
        {activeSong ? (
          <HistoryPane
            songName={activeSong}
            entries={activeEntries}
            liveMap={liveMap}
          />
        ) : (
          <p className={styles.placeholder}>左の一覧から曲を選んでください</p>
        )}
      </div>
    </div>
  );
}

function HistoryPane({ songName, entries, liveMap }) {
  const [sortAsc, setSortAsc] = useState(false);

  const sorted = useMemo(() => {
    return [...entries].sort((a, b) => {
      const da = liveMap[a['ライブ番号']]?.['日付'] ?? '';
      const db = liveMap[b['ライブ番号']]?.['日付'] ?? '';
      return sortAsc ? (da > db ? 1 : -1) : da < db ? 1 : -1;
    });
  }, [entries, liveMap, sortAsc]);

  return (
    <div className={styles.historyPane}>
      <div className={styles.historyHeader}>
        <h2 className={styles.historyTitle}>{songName}</h2>
        <button
          className={styles.sortBtn}
          onClick={() => setSortAsc((v) => !v)}
        >
          {sortAsc ? '古い順 ⇄' : '新しい順 ⇄'}
        </button>
      </div>

      <div className={styles.historyList}>
        {sorted.map((s, i) => {
          const live = liveMap[s['ライブ番号']];
          const videoUrl = live
            ? buildVideoUrl(live['動画リンク'], s['STARTTIME'])
            : null;

          return (
            <div key={i} className={styles.historyRow}>
              <span className={styles.histDate}>
                {live ? formatDate(live['日付']) : s['ライブ番号']}
              </span>
              <span className={styles.histLiveName}>
                {live ? live['ライブ名'] : ''}
              </span>
              <span className={styles.histVocal}>{s['ボーカル']}</span>
              {live?.['動画リンク'] ? (
                <a
                  className={styles.watchBtn}
                  href={videoUrl || live['動画リンク']}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  ▶
                </a>
              ) : (
                <span />
              )}
            </div>
          );
        })}
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
