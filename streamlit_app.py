import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import re

# ページ設定
st.set_page_config(page_title="VSOPライブ情報", layout="wide")

# 強制的に翻訳を無効化するスクリプトとスタイル
st.markdown("""
    <script>
        document.body.classList.add('notranslate');
        document.body.setAttribute('translate', 'no');
    </script>
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    div[data-testid="stSidebar"], div[data-testid="stMain"] {
        translate: no !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. 接続仕様
@st.cache_data(show_spinner="データを読み込んでいます...")
def load_data():
    try:
        if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
            return "secrets_missing", None
            
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        if not base_url or not str(base_url).startswith("http"):
            return "url_invalid", None

        # Google Sheets のベースURLを抽出
        match = re.search(r"(https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+)", str(base_url))
        if not match:
            return "url_format_error", None
        
        clean_url = match.group(1)

        # シートIDの定義
        gid_lives = "0"
        gid_songs = "1476106697" 

        lives_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_lives}"
        songs_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_songs}"

        try:
            df_lives = pd.read_csv(lives_url, encoding='utf-8')
        except Exception as e:
            return f"ライブ情報シート(gid={gid_lives})の読み込みに失敗しました: {e}", None

        try:
            df_songs = pd.read_csv(songs_url, encoding='utf-8')
        except Exception as e:
            return f"演奏曲目シート(gid={gid_songs})の読み込みに失敗しました: {e}", None

        # 全ての列名の前後の空白を削除
        df_lives.columns = [str(c).strip() for c in df_lives.columns]
        df_songs.columns = [str(c).strip() for c in df_songs.columns]

        return df_lives, df_songs
    except Exception as e:
        return str(e), None

res_l, res_s = load_data()

# エラー表示
if isinstance(res_l, str):
    st.error(res_l)
    st.stop()

df_lives: pd.DataFrame = res_l
df_songs: pd.DataFrame = res_s

# タイトル
st.title("VSOPライブ情報")

# 列名の選定（さらに柔軟に対応）
col_lives = df_lives.columns.tolist()
col_songs = df_songs.columns.tolist()

# 1. 紐付け用ID列の特定
# ユーザー要望どおり「ライブ番号」を優先
id_col_lives = next((c for c in ['ライブ番号', 'ライブID', 'LiveID'] if c in col_lives), col_lives[0] if col_lives else None)
id_col_songs = next((c for c in ['ライブ番号', 'ライブID', 'LiveID'] if c in col_songs), None)

# 2. 表示用列の特定 (Lives)
date_col = next((c for c in ['日付', '開催日', 'Date'] if c in col_lives), None)
live_name_col = next((c for c in ['ライブ名', '名称', 'LiveName'] if c in col_lives), None)

# 3. 表示用列の特定 (Songs)
song_name_col = next((c for c in ['楽曲名', '曲名', '曲', '名称', 'Title'] if c in col_songs), None)
# もし見つからず、1番目の列が名前なし(Unnamed)等の場合は1番目を使う
if not song_name_col and len(col_songs) > 0:
    if 'Unnamed' in col_songs[0] or col_songs[0] == "":
         song_name_col = col_songs[0]

vocal_col = next((c for c in ['ボーカル', 'Vocal', 'ボーカリスト'] if c in col_songs), None)
time_col = next((c for c in ['STARTTIME', 'TIME', '時間', '開始時間'] if c in col_songs), None)
sort_col = next((c for c in ['曲順', '演奏順', 'No'] if c in col_songs), None)

# サイドバー
with st.sidebar:
    st.header("検索・選択")

    if date_col and live_name_col:
        # 表示名作成
        df_lives['display_name'] = df_lives[date_col].astype(str) + " " + df_lives[live_name_col].astype(str)
        live_list = df_lives['display_name'].tolist()
        selected_live_display = st.selectbox("ライブを選択してください", live_list)
        selected_live_row = df_lives[df_lives['display_name'] == selected_live_display].iloc[0]
    else:
        st.error(f"ライブ情報の列が特定できません。 (列: {', '.join(col_lives)})")
        st.stop()

    st.markdown("---")
    st.warning("⚠️ エラーが出る場合は自動翻訳をオフにしてください。")
    
    # デバッグ情報の表示
    with st.expander("🛠 デバッグ情報（開発用）"):
        st.write("▼ライブ情報（先頭5行）")
        st.dataframe(df_lives.head())
        st.write("▼演奏曲目（先頭5行）")
        st.dataframe(df_songs.head())
        st.write("特定された列:", {
            "ID(Lives)": id_col_lives,
            "ID(Songs)": id_col_songs,
            "曲名": song_name_col,
            "ボーカル": vocal_col,
            "時間": time_col
        })

# 結果表示
if id_col_lives and id_col_songs:
    live_id_val = selected_live_row[id_col_lives]
    # 文字列として比較
    songs_to_display = df_songs[df_songs[id_col_songs].astype(str) == str(live_id_val)].copy()
else:
    st.warning("紐付け用のID（ライブ番号等）が特定できません。")
    st.stop()

if songs_to_display.empty:
    st.info(f"該当する曲が見つかりませんでした。 (選択ID: {live_id_val})")
    st.stop()

st.subheader(f"演奏曲目: {selected_live_display}")

# ソート
if sort_col:
    songs_to_display = songs_to_display.sort_values(by=sort_col)

# 曲リストの生成
video_link_base = selected_live_row.get('動画リンク', "")

if song_name_col and vocal_col:
    content_html = '<div style="font-family: sans-serif; line-height: 2.0; color: #31333F;">'
    for _, song in songs_to_display.iterrows():
        s_name = song[song_name_col]
        # NaN 対策
        s_name = s_name if pd.notna(s_name) else "(名称未設定)"
        s_vocal = song[vocal_col] if pd.notna(song[vocal_col]) else ""
        s_time = song[time_col] if time_col and pd.notna(song[time_col]) else 0
        
        youtube_link = ""
        if pd.notna(video_link_base) and s_time != 0:
            try:
                if isinstance(s_time, str) and ":" in s_time:
                    parts = s_time.split(':')
                    seconds = int(parts[-1]) + int(parts[-2]) * 60 + (int(parts[-3]) * 3600 if len(parts) > 2 else 0)
                else:
                    seconds = int(float(s_time))
                connector = "&" if "?" in str(video_link_base) else "?"
                youtube_link = f"{video_link_base}{connector}t={seconds}"
            except:
                youtube_link = video_link_base

        link_tag = f'<a href="{youtube_link}" target="_blank" style="color: #0068c9; text-decoration: none;">{youtube_link}</a>' if youtube_link else ""
        content_html += f'<div style="border-bottom: 1px solid #eee; padding: 5px 0;">{s_name} {s_vocal} {link_tag}</div>'
    
    content_html += '</div>'
    height = max(400, len(songs_to_display) * 45)
    components.html(content_html, height=height, scrolling=True)
else:
    st.error(f"曲名またはボーカルの列が見つかりません。デバッグ情報を確認してください。")
