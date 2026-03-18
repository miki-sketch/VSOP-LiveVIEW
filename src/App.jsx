import { useState, useEffect, useCallback } from 'react';
import { fetchSheet } from './utils/csv';
import { GIDS } from './config';
import LiveList from './pages/LiveList';
import LiveDetail from './pages/LiveDetail';
import SongSearch from './pages/SongSearch';
import { sendLog } from './utils/logger';
import styles from './App.module.css';

export default function App() {
  const [tab, setTab] = useState('lives'); // 'lives' | 'songs'
  const [selectedLiveNo, setSelectedLiveNo] = useState(null);

  const [lives, setLives] = useState([]);
  const [songs, setSongs] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAll = useCallback(async () => {
    try {
      setLoading(true);
      const [l, s, r] = await Promise.all([
        fetchSheet(GIDS.lives),
        fetchSheet(GIDS.songs),
        fetchSheet(GIDS.reviews),
      ]);
      setLives(l);
      setSongs(s);
      setReviews(r);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const reloadReviews = useCallback(async () => {
    const r = await fetchSheet(GIDS.reviews);
    setReviews(r);
  }, []);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const goToDetail = (liveNo) => {
    setSelectedLiveNo(liveNo);
  };

  const goBack = () => {
    setSelectedLiveNo(null);
  };

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoMain}>VSOP</span>
          <span className={styles.logoSub}>LIVE ARCHIVE</span>
        </div>

        <nav className={styles.nav}>
          {selectedLiveNo ? (
            <button className={styles.backBtn} onClick={goBack}>
              ← 一覧
            </button>
          ) : (
            <>
              <button
                className={`${styles.tab} ${tab === 'lives' ? styles.tabActive : ''}`}
                onClick={() => { setTab('lives'); sendLog('access', { page: 'LiveList' }); }}
              >
                LIVE一覧
              </button>
              <button
                className={`${styles.tab} ${tab === 'songs' ? styles.tabActive : ''}`}
                onClick={() => { setTab('songs'); sendLog('access', { page: 'SongSearch' }); }}
              >
                曲目検索
              </button>
            </>
          )}
        </nav>
      </header>

      <main className={styles.main}>
        {loading && <p className={styles.statusMsg}>読み込み中…</p>}
        {error && <p className={styles.errorMsg}>エラー: {error}</p>}
        {!loading && !error && (
          <>
            {selectedLiveNo ? (
              <LiveDetail
                liveNo={selectedLiveNo}
                lives={lives}
                songs={songs}
                reviews={reviews}
                onReviewsChange={reloadReviews}
              />
            ) : tab === 'lives' ? (
              <LiveList lives={lives} onSelect={goToDetail} />
            ) : (
              <SongSearch songs={songs} lives={lives} />
            )}
          </>
        )}
      </main>
    </div>
  );
}
