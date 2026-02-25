import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import re

# ページ設定
st.set_page_config(page_title="VSOPライブ情報", layout="wide")

# 強制的に翻訳を無効化
st.markdown("""
    <script>
        document.body.classList.add('notranslate');
        document.body.setAttribute('translate', 'no');
    </script>
    <style>
    .stApp { background-color: #f0f2f6; }
    div[data-testid="stSidebar"], div[data-testid="stMain"] { translate: no !important; }
    .block-container {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. 接続仕様
@st.cache_data(show_spinner="データを読み込んでいます...")
def load_data():
    try:
        if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
            return "secrets_missing", None, None
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        match = re.search(r"(https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+)", str(base_url))
        if not match: return "url_format_error", None, None
        clean_url = match.group(1)

        gid_lives = "0"
        gid_songs = "1268681059" 
        gid_feedback = "591211524"

        lives_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_lives}"
        songs_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_songs}"
        feedback_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_feedback}"

        df_lives = pd.read_csv(lives_url, encoding='utf-8')
        df_songs = pd.read_csv(songs_url, encoding='utf-8')
        df_feedback = pd.read_csv(feedback_url, encoding='utf-8')

        df_lives.columns = [str(c).strip() for c in df_lives.columns]
        df_songs.columns = [str(c).strip() for c in df_songs.columns]
        df_feedback.columns = [str(c).strip() for c in df_feedback.columns]

        return df_lives, df_songs, df_feedback
    except Exception as e:
        return str(e), None, None

res_l, res_s, res_f = load_data()
if isinstance(res_l, str):
    st.error(f"データの読み込みに失敗しました: {res_l}")
    st.stop()
df_lives, df_songs, df_feedback = res_l, res_s, res_f

# 列名の特定
col_lives, col_songs, col_f = df_lives.columns.tolist(), df_songs.columns.tolist(), df_feedback.columns.tolist()

id_col_lives = next((c for c in ['ライブ番号', 'ライブID'] if c in col_lives), col_lives[0] if col_lives else None)
id_col_songs = next((c for c in ['ライブ番号', 'ライブID'] if c in col_songs), None)
id_col_f = next((c for c in ['ライブ番号', 'ライブID'] if c in col_f), col_f[0] if col_f else None)

date_col = next((c for c in ['日付', '開催日'] if c in col_lives), None)
live_name_col = next((c for c in ['ライブ名', '名称'] if c in col_lives), None)

# 共通スタイル
table_style = """
<style>
    .frame-container { background-color: #fdfdfd; padding: 15px; border-radius: 8px; border: 1px solid #eee; margin-bottom: 20px; }
    .custom-table { width: 100%; border-collapse: collapse; font-family: sans-serif; color: #31333F; }
    .custom-table th { background-color: #f1f3f9; text-align: left; padding: 12px; border-bottom: 2px solid #ddd; font-size: 14px; }
    .custom-table td { padding: 10px 12px; border-bottom: 1px solid #eee; font-size: 14px; vertical-align: top; }
    .custom-table tr:hover { background-color: #f9fbff; }
    .no-col { width: 30px; color: #999; text-align: center; }
    .link-cell { word-break: break-all; }
    .author-cell { width: 120px; font-weight: bold; }
    .date-cell { width: 150px; color: #666; font-size: 12px; }
    a { color: #0068c9; text-decoration: none; }
    a:hover { text-decoration: underline; }
</style>
"""

# サイドバー
with st.sidebar:
    st.header("🔍 検索・選択")
    if date_col and live_name_col:
        df_lives['display_name'] = df_lives[date_col].astype(str) + " " + df_lives[live_name_col].astype(str)
        selected_live_display = st.selectbox("ライブを選択してください", df_lives['display_name'].tolist())
        selected_live_row = df_lives[df_lives['display_name'] == selected_live_display].iloc[0]
    else:
        st.stop()
    st.warning("⚠️ 翻訳をオフにしてください。")

# 抽出
if id_col_lives:
    live_id_val = selected_live_row[id_col_lives]
    songs_to_display = df_songs[df_songs[id_col_songs].astype(str) == str(live_id_val)].copy() if id_col_songs else pd.DataFrame()
    feedback_to_display = df_feedback[df_feedback[id_col_f].astype(str) == str(live_id_val)].copy() if id_col_f else pd.DataFrame()

# メイン表示
st.title("VSOPライブ情報")
st.subheader(f"ライブ: {selected_live_display}")

# --- 上段: セットリスト ---
st.markdown("### 📋 セットリスト")
song_name_col = next((c for c in ['楽曲名', '曲名', '曲'] if c in col_songs), col_songs[0] if col_songs else None)
vocal_col = next((c for c in ['ボーカル', 'Vocal'] if c in col_songs), None)
time_col = next((c for c in ['STARTTIME', 'TIME'] if c in col_songs), None)
sort_col = next((c for c in ['曲順', '演奏順'] if c in col_songs), None)

if not songs_to_display.empty:
    if sort_col: songs_to_display = songs_to_display.sort_values(by=sort_col)
    video_link_base = selected_live_row.get('動画リンク', "")
    html = table_style + "<div class='frame-container'><table class='custom-table'>"
    html += "<tr><th class='no-col'>#</th><th>楽曲</th><th>ボーカル</th><th class='link-cell'>YouTube</th></tr>"
    for i, (_, row) in enumerate(songs_to_display.iterrows(), 1):
        name = row[song_name_col] if pd.notna(row[song_name_col]) else "-"
        vocal = row[vocal_col] if vocal_col and pd.notna(row[vocal_col]) else ""
        t = row[time_col] if time_col and pd.notna(row[time_col]) else 0
        y_url = ""
        if pd.notna(video_link_base) and t != 0:
            try:
                if isinstance(t, str) and ":" in t:
                    p = t.split(':')
                    s = int(p[-1]) + int(p[-2]) * 60 + (int(p[-3]) * 3600 if len(p) > 2 else 0)
                else: s = int(float(t))
                y_url = f"{video_link_base}{'&' if '?' in str(video_link_base) else '?'}t={s}"
            except: y_url = video_link_base
        l_html = f'<a href="{y_url}" target="_blank">視聴</a>' if y_url else ""
        html += f"<tr><td class='no-col'>{i}</td><td>{name}</td><td>{vocal}</td><td class='link-cell'>{l_html}</td></tr>"
    html += "</table></div>"
    components.html(html, height=min(400, len(songs_to_display) * 50 + 80), scrolling=True)

# --- 下段: ライブ感想 ---
st.markdown("### 💬 ライブ感想")
# シート構造（スクショより）: A=ライブ番号, B=投稿, C=コメント, D=投稿時間
if len(col_f) >= 4:
    f_author_idx = 1 # B: 投稿
    f_text_idx = 2   # C: コメント
    f_date_idx = 3   # D: 投稿時間
else:
    # 予備の検索ロジック
    f_author_idx = next((i for i, c in enumerate(col_f) if c in ['投稿', '投稿者', '名前']), 1)
    f_text_idx = next((i for i, c in enumerate(col_f) if c in ['コメント', '感想', '内容']), 2)
    f_date_idx = next((i for i, c in enumerate(col_f) if c in ['投稿時間', '投稿日時', '日時']), 3)

if not feedback_to_display.empty:
    html_f = table_style + "<div class='frame-container' style='background-color: #fff9f0;'><table class='custom-table'>"
    html_f += "<tr><th class='no-col'>#</th><th>感想内容</th><th class='author-cell'>投稿者</th><th class='date-cell'>投稿日時</th></tr>"
    for i, (_, row) in enumerate(feedback_to_display.iterrows(), 1):
        # 列のインデックスで正確に取得
        author = row.iloc[f_author_idx] if len(row) > f_author_idx and pd.notna(row.iloc[f_author_idx]) else "匿名"
        txt = row.iloc[f_text_idx] if len(row) > f_text_idx and pd.notna(row.iloc[f_text_idx]) else "-"
        dt = row.iloc[f_date_idx] if len(row) > f_date_idx and pd.notna(row.iloc[f_date_idx]) else "-"
        
        html_f += f"<tr><td class='no-col'>{i}</td><td>{txt}</td><td class='author-cell'>{author}</td><td class='date-cell'>{dt}</td></tr>"
    html_f += "</table></div>"
    components.html(html_f, height=300, scrolling=True)
else:
    st.info("感想未登録")
