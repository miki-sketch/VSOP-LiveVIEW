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

        df_lives.columns = df_lives.columns.str.strip()
        df_songs.columns = df_songs.columns.str.strip()

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

# 列名の選定（柔軟に対応）
col_lives = df_lives.columns.tolist()
col_songs = df_songs.columns.tolist()

# ID列の特定: 「ライブID」がなければ「ライブ番号」を探す
id_col_lives = 'ライブID' if 'ライブID' in col_lives else ('ライブ番号' if 'ライブ番号' in col_lives else None)
id_col_songs = 'ライブID' if 'ライブID' in col_songs else ('ライブ番号' if 'ライブ番号' in col_songs else None)

# サイドバー
with st.sidebar:
    st.header("検索・選択")
    # 「日付」と「ライブ名」を表示に使用
    date_col = '日付' if '日付' in col_lives else ('開催日' if '開催日' in col_lives else None)
    name_col_lives = 'ライブ名' if 'ライブ名' in col_lives else ('名称' if '名称' in col_lives else None)

    if date_col and name_col_lives:
        df_lives['display_name'] = df_lives[date_col].astype(str) + " " + df_lives[name_col_lives].astype(str)
        live_list = df_lives['display_name'].tolist()
        selected_live_display = st.selectbox("ライブを選択してください", live_list)
        selected_live_row = df_lives[df_lives['display_name'] == selected_live_display].iloc[0]
    else:
        st.error(f"ライブ情報シートに必要な列が見つかりません。 (列名: {', '.join(col_lives)})")
        st.stop()

    st.markdown("---")
    st.warning("⚠️ エラーが出る場合は自動翻訳をオフにしてください。")
    
    # デバッグ情報の表示切り替え
    with st.expander("🛠 デバッグ情報（開発用）"):
        st.write("ライブ情報列:", col_lives)
        st.write("演奏曲目列:", col_songs)
        st.write("紐付け列:", f"Lives:{id_col_lives} / Songs:{id_col_songs}")

# 結果表示
if id_col_lives and id_col_songs:
    live_id_val = selected_live_row[id_col_lives]
    # 数値/文字列の不一致を避けるため両方strにする
    songs_to_display = df_songs[df_songs[id_col_songs].astype(str) == str(live_id_val)].copy()
else:
    st.warning("紐付け用のID（ライブID または ライブ番号）が両方のシートに見つかりません。")
    st.stop()

if songs_to_display.empty:
    st.info(f"選択されたライブ（ID: {live_id_val}）に該当する曲が見つかりませんでした。")
    st.stop()

st.subheader(f"演奏曲目: {selected_live_display}")

# ソート
sort_col = '曲順' if '曲順' in col_songs else None
if sort_col:
    songs_to_display = songs_to_display.sort_values(by=sort_col)

# 曲リストの生成
video_link_base = selected_live_row.get('動画リンク', "")
song_name_col = '楽曲名' if '楽曲名' in col_songs else '曲名'
vocal_col = 'ボーカル' if 'ボーカル' in col_songs else 'Vocal'
time_col = 'STARTTIME' if 'STARTTIME' in col_songs else ('TIME' if 'TIME' in col_songs else None)

if song_name_col in col_songs and vocal_col in col_songs:
    content_html = '<div style="font-family: sans-serif; line-height: 2.0; color: #31333F;">'
    for _, song in songs_to_display.iterrows():
        s_name = song[song_name_col]
        s_vocal = song[vocal_col]
        s_time = song[time_col] if time_col else 0
        
        youtube_link = ""
        if pd.notna(video_link_base) and pd.notna(s_time):
            try:
                # 00:00 形式の変換
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
    st.error(f"表示に必要な列（曲名、ボーカル）が見つかりません。")
