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
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stSidebar"], div[data-testid="stMain"] { translate: no !important; }
    </style>
    """, unsafe_allow_html=True)

# 1. 接続仕様
@st.cache_data(show_spinner="データを読み込んでいます...")
def load_data():
    try:
        if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
            return "secrets_missing", None
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        match = re.search(r"(https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+)", str(base_url))
        if not match: return "url_format_error", None
        clean_url = match.group(1)

        gid_lives = "0"
        gid_songs = "1268681059" 

        lives_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_lives}"
        songs_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_songs}"

        df_lives = pd.read_csv(lives_url, encoding='utf-8')
        df_songs = pd.read_csv(songs_url, encoding='utf-8')

        df_lives.columns = [str(c).strip() for c in df_lives.columns]
        df_songs.columns = [str(c).strip() for c in df_songs.columns]

        return df_lives, df_songs
    except Exception as e:
        return str(e), None

res_l, res_s = load_data()
if isinstance(res_l, str):
    st.error(res_l)
    st.stop()
df_lives, df_songs = res_l, res_s

# 列名の特定
col_lives, col_songs = df_lives.columns.tolist(), df_songs.columns.tolist()

id_col_lives = next((c for c in ['ライブ番号', 'ライブID'] if c in col_lives), col_lives[0] if col_lives else None)
id_col_songs = next((c for c in ['ライブ番号', 'ライブID'] if c in col_songs), None)

date_col = next((c for c in ['日付', '開催日'] if c in col_lives), None)
live_name_col = next((c for c in ['ライブ名', '名称'] if c in col_lives), None)

song_name_col = next((c for c in ['楽曲名', '曲名', '曲'] if c in col_songs), None)
if not song_name_col and len(col_songs) > 0:
    song_name_col = col_songs[0]

vocal_col = next((c for c in ['ボーカル', 'Vocal'] if c in col_songs), None)
time_col = next((c for c in ['STARTTIME', 'TIME'] if c in col_songs), None)
sort_col = next((c for c in ['曲順', '演奏順'] if c in col_songs), None)

# サイドバー
with st.sidebar:
    st.header("検索・選択")
    if date_col and live_name_col:
        df_lives['display_name'] = df_lives[date_col].astype(str) + " " + df_lives[live_name_col].astype(str)
        selected_live_display = st.selectbox("ライブを選択してください", df_lives['display_name'].tolist())
        selected_live_row = df_lives[df_lives['display_name'] == selected_live_display].iloc[0]
    else:
        st.error("ライブ情報の列(日付, ライブ名)が見つかりません。")
        st.stop()

    with st.expander("🛠 デバッグ情報"):
        st.write("特定された列:", {"紐付けID": id_col_songs, "曲名": song_name_col, "ボーカル": vocal_col})
        st.dataframe(df_songs.head(3))

# データの抽出
if id_col_lives and id_col_songs:
    live_id_val = selected_live_row[id_col_lives]
    songs_to_display = df_songs[df_songs[id_col_songs].astype(str) == str(live_id_val)].copy()
else:
    st.error("紐付け用の「ライブ番号」がシートに見つかりませんでした。")
    st.stop()

st.title("VSOPライブ情報")
st.subheader(f"セットリスト: {selected_live_display}")

if songs_to_display.empty:
    st.info(f"このライブに該当する曲が見つかりませんでした。 (ライブ番号: {live_id_val})")
    st.stop()

if sort_col:
    songs_to_display = songs_to_display.sort_values(by=sort_col)

# リスト作成（テーブル形式）
video_link_base = selected_live_row.get('動画リンク', "")
if song_name_col:
    # テーブルのHTML構築
    table_style = """
    <style>
        table { width: 100%; border-collapse: collapse; font-family: sans-serif; color: #31333F; }
        th { background-color: #f0f2f6; text-align: left; padding: 12px; border-bottom: 2px solid #dee2e6; }
        td { padding: 10px 12px; border-bottom: 1px solid #eee; }
        tr:hover { background-color: #f8f9fa; }
        .no-col { width: 40px; color: #888; text-align: center; }
        .link-cell { word-break: break-all; }
        a { color: #0068c9; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
    """
    
    content_html = table_style + "<table>"
    content_html += "<tr><th class='no-col'>#</th><th>楽曲</th><th>ボーカル</th><th class='link-cell'>Youtubeリンク</th></tr>"
    
    for i, (_, song) in enumerate(songs_to_display.iterrows(), 1):
        s_name = song[song_name_col] if pd.notna(song[song_name_col]) else "(untitled)"
        s_vocal = song[vocal_col] if vocal_col and pd.notna(song[vocal_col]) else ""
        s_time = song[time_col] if time_col and pd.notna(song[time_col]) else 0
        
        y_link = ""
        if pd.notna(video_link_base) and s_time != 0:
            try:
                if isinstance(s_time, str) and ":" in s_time:
                    parts = s_time.split(':')
                    sec = int(parts[-1]) + int(parts[-2]) * 60 + (int(parts[-3]) * 3600 if len(parts) > 2 else 0)
                else: sec = int(float(s_time))
                y_link = f"{video_link_base}{'&' if '?' in str(video_link_base) else '?'}t={sec}"
            except: y_link = video_link_base

        link_html = f'<a href="{y_link}" target="_blank">{y_link}</a>' if y_link else ""
        content_html += f"<tr><td class='no-col'>{i}</td><td>{s_name}</td><td>{s_vocal}</td><td class='link-cell'>{link_html}</td></tr>"
    
    content_html += "</table>"
    components.html(content_html, height=max(500, len(songs_to_display) * 60), scrolling=True)
else:
    st.error("表示に必要な列が見つかりませんでした。")
