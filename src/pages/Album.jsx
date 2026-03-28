import { useState, useEffect, useCallback } from 'react';
import { sendLog } from '../utils/logger';
import styles from './Album.module.css';

export default function Album({ liveNo, lives, photos, onBack }) {
  const live = lives.find((l) => l['ライブ番号'] === liveNo);
  const [lightboxIndex, setLightboxIndex] = useState(null);

  useEffect(() => {
    if (live) {
      sendLog('access', { page: 'Album', liveName: live['ライブ名'] });
    }
  }, [liveNo]); // eslint-disable-line react-hooks/exhaustive-deps

  const openLightbox = (index) => {
    setLightboxIndex(index);
    sendLog('play', { songName: '写真を閲覧', liveName: live?.['ライブ名'] });
  };

  const closeLightbox = () => setLightboxIndex(null);

  const movePrev = useCallback(() => {
    setLightboxIndex((i) => (i > 0 ? i - 1 : photos.length - 1));
  }, [photos.length]);

  const moveNext = useCallback(() => {
    setLightboxIndex((i) => (i < photos.length - 1 ? i + 1 : 0));
  }, [photos.length]);

  useEffect(() => {
    if (lightboxIndex === null) return;
    const handleKey = (e) => {
      if (e.key === 'ArrowLeft') movePrev();
      else if (e.key === 'ArrowRight') moveNext();
      else if (e.key === 'Escape') closeLightbox();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [lightboxIndex, movePrev, moveNext]);

  if (!live) return <p className={styles.notFound}>ライブが見つかりません。</p>;

  const currentPhoto = lightboxIndex !== null ? photos[lightboxIndex] : null;

  return (
    <div className={styles.container}>
      <div className={styles.albumHeader}>
        <div>
          <div className={styles.liveName}>{live['ライブ名']}</div>
          <div className={styles.liveDate}>{formatDate(live['日付'])}</div>
        </div>
        <button className={styles.backBtn} onClick={onBack}>
          ← ライブ詳細に戻る
        </button>
      </div>

      {photos.length === 0 ? (
        <p className={styles.placeholder}>写真がありません</p>
      ) : (
        <div className={styles.grid}>
          {photos.map((photo, index) => (
            <div
              key={index}
              className={styles.cell}
              onClick={() => openLightbox(index)}
            >
              <img
                src={photo['写真URL']}
                alt={photo['キャプション'] || `写真 ${index + 1}`}
                className={styles.thumb}
                loading="lazy"
              />
              {(photo['キャプション'] || photo['撮影者']) && (
                <div className={styles.caption}>
                  {photo['キャプション'] && (
                    <span className={styles.captionText}>{photo['キャプション']}</span>
                  )}
                  {photo['撮影者'] && (
                    <span className={styles.photographer}>📷 {photo['撮影者']}</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {lightboxIndex !== null && (
        <div className={styles.lightboxOverlay} onClick={closeLightbox}>
          <div className={styles.lightbox} onClick={(e) => e.stopPropagation()}>
            <button className={styles.lbClose} onClick={closeLightbox}>✕</button>
            <button className={styles.lbArrow} data-dir="prev" onClick={movePrev}>‹</button>
            <div className={styles.lbImgWrap}>
              <img
                src={currentPhoto['写真URL']}
                alt={currentPhoto['キャプション'] || `写真 ${lightboxIndex + 1}`}
                className={styles.lbImg}
              />
            </div>
            <button className={styles.lbArrow} data-dir="next" onClick={moveNext}>›</button>
          </div>
          {(currentPhoto['キャプション'] || currentPhoto['撮影者']) && (
            <div className={styles.lbCaption}>
              {currentPhoto['キャプション'] && (
                <span className={styles.lbCaptionText}>{currentPhoto['キャプション']}</span>
              )}
              {currentPhoto['撮影者'] && (
                <span className={styles.lbPhotographer}>📷 {currentPhoto['撮影者']}</span>
              )}
            </div>
          )}
          <div className={styles.lbCounter}>
            {lightboxIndex + 1} / {photos.length}
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
