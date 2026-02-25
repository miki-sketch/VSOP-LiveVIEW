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

        # Google Sheets のベースURLを抽出（ID部分まで）
        match = re.search(r"(https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+)", str(base_url))
        if not match:
            return "url_format_error", None
        
        clean_url = match.group(1)

        # シートIDの定義
        # 仕様: ライブ情報=0, 演奏曲目=1476106697
        gid_lives = "0"
        gid_songs = "1476106697" 

        # URL構築 (gviz 方式: より安定している場合が多い)
        lives_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_lives}"
        songs_url = f"{clean_url}/gviz/tq?tqx=out:csv&gid={gid_songs}"

        # データ読み込み
        # 400エラーが出た場合、どちらのシートで失敗したか特定できるように個別に試行
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

# データ読み込み実行
res_l, res_s = load_data()

# エラー表示
if isinstance(res_l, str):
    if res_l == "secrets_missing":
        st.error("Secrets 'connections.gsheets' が設定されていません。")
    elif res_l == "url_invalid":
        st.error("Secrets の URL が正しくありません。")
    elif res_l == "url_format_error":
        st.error("URLの形式が解析できませんでした。")
    else:
        st.error(res_l) # ここに具体的な失敗シート情報が入る
        with st.expander("デバッグ情報"):
            st.write("アクセスに使用したクリーンURL:")
            base = st.secrets["connections"]["gsheets"]["spreadsheet"]
            st.code(f"Original: {base}")
            match = re.search(r"(https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+)", str(base))
            if match:
                st.code(f"Clean: {match.group(1)}")
            st.write("※gid(シートID)が正しいか、またはシートが「リンクを知っている全員」に公開されているか再度ご確認ください。")
    st.stop()

# 型を確定させる
df_lives: pd.DataFrame = res_l
df_songs: pd.DataFrame = res_s

# タイトル
st.title("VSOPライブ情報")

# サイドバー
with st.sidebar:
    st.header("検索・選択")
    if '日付' in df_lives.columns and 'ライブ名' in df_lives.columns:
        df_lives['display_name'] = df_lives['日付'].astype(str) + " " + df_lives['ライブ名'].astype(str)
        live_list = df_lives['display_name'].tolist()
        selected_live_display = st.selectbox("ライブを選択してください", live_list)
        selected_live_row = df_lives[df_lives['display_name'] == selected_live_display].iloc[0]
    else:
        st.error("シートに必要な列（日付、ライブ名）がありません。")
        st.stop()

    st.markdown("---")
    st.warning("⚠️ エラーが出る場合は自動翻訳をオフにしてください。")

# 結果表示
if 'ライブID' in df_lives.columns and 'ライブID' in df_songs.columns:
    live_id = selected_live_row['ライブID']
    songs_to_display = df_songs[df_songs['ライブID'] == live_id].copy()
else:
    st.warning("ライブIDが見つかりません。")
    st.stop()

st.subheader(f"演奏曲目: {selected_live_display}")

if '曲順' in songs_to_display.columns:
    songs_to_display = songs_to_display.sort_values(by='曲順')

# 曲リストの生成
video_link_base = selected_live_row.get('動画リンク', "")

# 列名正規化（仕様と実態のズレを吸収）
# STARTTIME がない場合に TIME を代用
col_songs = songs_to_display.columns.tolist()
name_col = '楽曲名' if '楽曲名' in col_songs else '曲名'
vocal_col = 'ボーカル' if 'ボーカル' in col_songs else 'Vocal'
time_col = 'STARTTIME' if 'STARTTIME' in col_songs else ('TIME' if 'TIME' in col_songs else None)

if name_col in col_songs and vocal_col in col_songs:
    content_html = '<div style="font-family: sans-serif; line-height: 2.0; color: #31333F;">'
    for _, song in songs_to_display.iterrows():
        song_name = song[name_col]
        vocal = song[vocal_col]
        starttime = song[time_col] if time_col else 0
        
        youtube_link = ""
        if pd.notna(video_link_base) and pd.notna(starttime):
            try:
                # 00:00:00 形式などの場合は秒数に変換する必要があるが、一旦数値と仮定
                if isinstance(starttime, str) and ":" in starttime:
                    parts = starttime.split(':')
                    seconds = int(parts[-1]) + int(parts[-2]) * 60 + (int(parts[-3]) * 3600 if len(parts) > 2 else 0)
                else:
                    seconds = int(float(starttime))
                connector = "&" if "?" in str(video_link_base) else "?"
                youtube_link = f"{video_link_base}{connector}t={seconds}"
            except:
                youtube_link = video_link_base

        link_tag = f'<a href="{youtube_link}" target="_blank" style="color: #0068c9; text-decoration: none;">{youtube_link}</a>' if youtube_link else ""
        content_html += f'<div style="border-bottom: 1px solid #eee; padding: 5px 0;">{song_name} {vocal} {link_tag}</div>'
    
    content_html += '</div>'
    height = max(400, len(songs_to_display) * 45)
    components.html(content_html, height=height, scrolling=True)
else:
    st.error(f"必要な列が見つかりません。 (確認できた列: {', '.join(col_songs)})")
