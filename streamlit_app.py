import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import re

# ページ設定
st.set_page_config(page_title="VSOPライブ情報", layout="wide")

# 強制的に翻訳を無効化するスクリプトとスタイル
st.markdown("""
    <script>
        // ボディ全体に notranslate クラスを付与し、翻訳属性を拒否
        document.body.classList.add('notranslate');
        document.body.setAttribute('translate', 'no');
    </script>
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    /* Streamlit固有の要素にも翻訳拒否を適用 */
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

        # シートIDの定義（仕様どおり）
        gid_lives = "0"
        gid_songs = "1476106697"

        # 正確なエクスポートURLを構築
        lives_url = f"{clean_url}/export?format=csv&gid={gid_lives}"
        songs_url = f"{clean_url}/export?format=csv&gid={gid_songs}"

        # データ読み込み
        df_lives = pd.read_csv(lives_url, encoding='utf-8')
        df_songs = pd.read_csv(songs_url, encoding='utf-8')

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
        st.error("スプレッドシートURLの形式が解析できませんでした。")
    else:
        st.error(f"データの読み込みに失敗しました: {res_l}")
        with st.expander("原因の確認とデバッグ"):
            st.write("アクセスしようとしたURL:")
            base = st.secrets["connections"]["gsheets"]["spreadsheet"]
            st.code(f"Base: {base}")
            st.write("※スプレッドシートが「ウェブに公開」されており、閲覧権限が適切か確認してください。")
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
        st.error("シート構造が正しくありません。")
        st.stop()

    st.markdown("---")
    st.warning("⚠️ ブラウザの自動翻訳（Google 翻訳など）が ON の場合、表示エラーが発生します。必ず OFF にしてください。")

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

# 曲リストの生成（HTML iframeを使用してReactの干渉を避ける）
video_link_base = selected_live_row.get('動画リンク', "")
required_cols = ['楽曲名', 'ボーカル', 'STARTTIME']

if all(col in songs_to_display.columns for col in required_cols):
    content_html = """
    <div style="font-family: sans-serif; line-height: 2.0; color: #31333F;">
    """
    for _, song in songs_to_display.iterrows():
        song_name = song['楽曲名']
        vocal = song['ボーカル']
        starttime = song['STARTTIME']
        
        youtube_link = ""
        if pd.notna(video_link_base) and pd.notna(starttime):
            try:
                seconds = int(starttime)
                connector = "&" if "?" in str(video_link_base) else "?"
                youtube_link = f"{video_link_base}{connector}t={seconds}"
            except:
                youtube_link = video_link_base

        link_tag = f'<a href="{youtube_link}" target="_blank" style="color: #0068c9; text-decoration: none;">{youtube_link}</a>' if youtube_link else ""
        content_html += f'<div style="border-bottom: 1px solid #eee; padding: 5px 0;">{song_name} {vocal} {link_tag}</div>'
    
    content_html += '</div>'
    
    # iframeとしてレンダリング（高さは曲数に応じて調整）
    height = max(400, len(songs_to_display) * 45)
    components.html(content_html, height=height, scrolling=True)
else:
    st.error("必要な列が欠落しています。")
