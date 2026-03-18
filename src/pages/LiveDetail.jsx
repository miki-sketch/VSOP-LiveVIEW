import { useState, useEffect } from 'react';
import { buildVideoUrl } from '../utils/csv';
import { GAS_URL } from '../config';
import { sendLog } from '../utils/logger';
import styles from './LiveDetail.module.css';

export default function LiveDetail({ liveNo, lives, songs, reviews, onReviewsChange }) {
  const live = lives.find((l) => l['ライブ番号'] === liveNo);

  useEffect(() => {
    if (live) {
      sendLog('access', { page: 'LiveDetail', liveName: live['ライブ名'] });
    }
  }, [liveNo]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!live) return <p className={styles.notFound}>ライブが見つかりません。</p>;

  const isUpcoming = live['STATUS'] !== '済';
  const liveSongs = songs
    .filter((s) => s['ライブ番号'] === liveNo)
    .sort((a, b) => {
      const aEncore = a['曲順'] === 'Y';
      const bEncore = b['曲順'] === 'Y';
      if (aEncore !== bEncore) return aEncore ? 1 : -1;
      return Number(a['曲順']) - Number(b['曲順']);
    });
  const liveReviews = reviews.filter((r) => r['ライブ番号'] === liveNo);

  return (
    <div className={styles.container}>
      <LiveInfo live={live} isUpcoming={isUpcoming} />
      <SetlistSection
        live={live}
        songs={liveSongs}
        isUpcoming={isUpcoming}
      />
      {!isUpcoming && (
        <ReviewSection
          liveNo={liveNo}
          reviews={liveReviews}
          onReviewsChange={onReviewsChange}
        />
      )}
    </div>
  );
}

function LiveInfo({ live, isUpcoming }) {
  return (
    <div className={styles.infoCard}>
      <div className={styles.infoTop}>
        <div>
          <div className={styles.infoDate}>
            {formatDate(live['日付'])}
            {live['開始時間'] && (
              <span className={styles.infoTime}> {live['開始時間']}〜</span>
            )}
          </div>
          <h1 className={styles.liveName}>{live['ライブ名']}</h1>
        </div>
        {isUpcoming && <span className={styles.upcomingBadge}>UPCOMING</span>}
      </div>

      <div className={styles.infoMeta}>
        {live['会場'] && (
          <span className={styles.metaItem}>
            <span className={styles.metaIcon}>📍</span>
            {live['会場']}
            {live['地域'] && ` (${live['地域']})`}
          </span>
        )}
        {live['形式'] && (
          <span className={styles.metaItem}>
            <span className={styles.metaIcon}>🏛</span>
            {live['形式']}
          </span>
        )}
        {live['演奏時間'] && (
          <span className={styles.metaItem}>
            <span className={styles.metaIcon}>⏱</span>
            {live['演奏時間']}分
          </span>
        )}
      </div>

      {live['特記事項'] && (
        <p className={styles.note}>{live['特記事項']}</p>
      )}

      {live['動画リンク'] && (
        <a
          className={styles.videoBtn}
          href={live['動画リンク']}
          target="_blank"
          rel="noopener noreferrer"
        >
          ▶ 動画を見る
        </a>
      )}
    </div>
  );
}

function SetlistSection({ live, songs, isUpcoming }) {
  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>SETLIST</h2>
      {isUpcoming && songs.length === 0 ? (
        <p className={styles.placeholder}>演奏予定曲は未定です</p>
      ) : songs.length === 0 ? (
        <p className={styles.placeholder}>セットリストはまだ登録されていません</p>
      ) : (
        <table className={styles.setlistTable}>
          <thead>
            <tr>
              <th>#</th>
              <th>曲名</th>
              <th>ボーカル</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {songs.map((song) => {
              const videoUrl = buildVideoUrl(live['動画リンク'], song['STARTTIME']);
              return (
                <tr key={song['曲番号']}>
                  <td className={styles.orderCell}>
                    {song['曲順'] === 'Y' ? 'Enc' : song['曲順']}
                  </td>
                  <td className={styles.songName}>{song['楽曲名']}</td>
                  <td className={styles.vocalist}>{song['ボーカル']}</td>
                  <td>
                    {live['動画リンク'] && (
                      <a
                        className={styles.watchBtn}
                        href={videoUrl || live['動画リンク']}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => sendLog('play', { songName: song['楽曲名'], liveName: live['ライブ名'] })}
                      >
                        ▶
                      </a>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}

function ReviewSection({ liveNo, reviews, onReviewsChange }) {
  const [showForm, setShowForm] = useState(false);
  const [posting, setPosting] = useState(false);
  const [form, setForm] = useState({ author: '', text: '', key: '' });
  const [formError, setFormError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.author || !form.text || !form.key) {
      setFormError('すべての項目を入力してください');
      return;
    }
    setPosting(true);
    setFormError('');
    try {
      const res = await fetch(GAS_URL, {
        method: 'POST',
        body: JSON.stringify({
          action: 'add',
          live_no: liveNo,
          author: form.author,
          text: form.text,
          key: form.key,
        }),
      });
      const text = await res.text();
      if (text.trim() === 'success') {
        setForm({ author: '', text: '', key: '' });
        setShowForm(false);
        await onReviewsChange();
      } else {
        setFormError('投稿に失敗しました: ' + text);
      }
    } catch (err) {
      setFormError('通信エラー: ' + err.message);
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>REVIEWS</h2>

      {reviews.length === 0 && (
        <p className={styles.placeholder}>まだ感想はありません</p>
      )}

      {reviews.map((r, i) => (
        <ReviewItem key={i} review={r} liveNo={liveNo} onReviewsChange={onReviewsChange} />
      ))}

      <button
        className={styles.toggleFormBtn}
        onClick={() => setShowForm((v) => !v)}
      >
        {showForm ? '× キャンセル' : '+ 感想を投稿する'}
      </button>

      {showForm && (
        <form className={styles.form} onSubmit={handleSubmit}>
          <div className={styles.formField}>
            <label>名前</label>
            <input
              value={form.author}
              onChange={(e) => setForm((f) => ({ ...f, author: e.target.value }))}
              placeholder="ニックネームなど"
            />
          </div>
          <div className={styles.formField}>
            <label>感想</label>
            <textarea
              rows={4}
              value={form.text}
              onChange={(e) => setForm((f) => ({ ...f, text: e.target.value }))}
              placeholder="ライブの感想を書いてください"
            />
          </div>
          <div className={styles.formField}>
            <label>登録キー（削除時に必要）</label>
            <input
              type="password"
              value={form.key}
              onChange={(e) => setForm((f) => ({ ...f, key: e.target.value }))}
              placeholder="任意のキーワード"
            />
          </div>
          {formError && <p className={styles.formError}>{formError}</p>}
          <button className={styles.submitBtn} type="submit" disabled={posting}>
            {posting ? '投稿中…' : '投稿する'}
          </button>
        </form>
      )}
    </div>
  );
}

function ReviewItem({ review, liveNo, onReviewsChange }) {
  const [showModal, setShowModal] = useState(false);
  const [keyInput, setKeyInput] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [delError, setDelError] = useState('');

  const handleDelete = async () => {
    if (!keyInput) {
      setDelError('登録キーを入力してください');
      return;
    }
    setDeleting(true);
    setDelError('');
    try {
      const res = await fetch(GAS_URL, {
        method: 'POST',
        body: JSON.stringify({
          action: 'delete',
          live_no: liveNo,
          text: review['コメント'],
          key: keyInput,
        }),
      });
      const text = await res.text();
      if (text.trim() === 'success') {
        setShowModal(false);
        await onReviewsChange();
      } else {
        setDelError('削除に失敗しました（キーが違う可能性があります）');
      }
    } catch (err) {
      setDelError('通信エラー: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className={styles.reviewItem}>
      <div className={styles.reviewHeader}>
        <span className={styles.reviewAuthor}>{review['登録キー'] || '匿名'}</span>
        <span className={styles.reviewDate}>{review['投稿時間']}</span>
        <button className={styles.deleteBtn} onClick={() => setShowModal(true)}>
          削除
        </button>
      </div>
      <p className={styles.reviewText}>{review['コメント']}</p>

      {showModal && (
        <div className={styles.modalOverlay} onClick={() => setShowModal(false)}>
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <h3>感想を削除</h3>
            <p>登録キーを入力してください</p>
            <input
              type="password"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              placeholder="登録キー"
            />
            {delError && <p className={styles.formError}>{delError}</p>}
            <div className={styles.modalActions}>
              <button
                className={styles.cancelBtn}
                onClick={() => setShowModal(false)}
              >
                キャンセル
              </button>
              <button
                className={styles.confirmDeleteBtn}
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? '削除中…' : '削除する'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr.replace(/\//g, '-'));
  if (isNaN(d)) return dateStr;
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
}
