import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="VSOPライブ情報", layout="wide")

# スタイル設定
st.markdown("""
    <style>
    /* .main クラスは Streamlit 内部で使用されるため競合を避ける */
    .stApp {
        background-color: #f8f9fa;
    }
    .stSelectbox label {
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. 接続仕様
@st.cache_data(show_spinner="データを読み込んでいます...")
def load_data():
    try:
        # st.secrets の構造確認
        if "connections" not in st.secrets or "gsheets" not in st.secrets["connections"]:
            return "secrets_missing", None
            
        base_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # URLが空でないか確認
        if not base_url or not str(base_url).startswith("http"):
            return "url_invalid", None

        # シートIDの定義
        gid_lives = "0"
        gid_songs = "1476106697" # 演奏曲目シート

        # URL構築
        lives_url = f"{base_url}/export?format=csv&gid={gid_lives}"
        songs_url = f"{base_url}/export?format=csv&gid={gid_songs}"

        # データ読み込み
        df_lives = pd.read_csv(lives_url, encoding='utf-8')
        df_songs = pd.read_csv(songs_url, encoding='utf-8')

        # 4. エラーガード: 列名の前後の空白を削除
        df_lives.columns = df_lives.columns.str.strip()
        df_songs.columns = df_songs.columns.str.strip()

        return df_lives, df_songs
    except Exception as e:
        return str(e), None

# データ読み込み実行
res_l, res_s = load_data()

# エラー表示（ブラウザ翻訳による React エラー防止のためシンプルな構成に）
if isinstance(res_l, str):
    if res_l == "secrets_missing":
        st.error("Secrets 'connections.gsheets' が設定されていません。")
        st.info("Streamlit 管理画面の Secrets 設定を確認してください。")
    elif res_l == "url_invalid":
        st.error("Secrets の URL が正しくありません。")
    else:
        st.error(f"データの読み込みに失敗しました: {res_l}")
    st.stop()

# 型ヒント的な扱いのための代入
df_lives: pd.DataFrame = res_l
df_songs: pd.DataFrame = res_s

# ブラウザ翻訳に関する警告（removeChild エラーの主な原因）
st.sidebar.warning("⚠️ ブラウザの自動翻訳機能（Google 翻訳など）がオンになっていると、表示エラーが発生する場合があります。エラーが出る場合は翻訳をオフにしてください。")

if df_lives is not None:
    st.title("VSOPライブ情報")

    # サイドバー: 検索・選択フレーム
    with st.sidebar:
        st.header("検索・選択")
        
        if '日付' in df_lives.columns and 'ライブ名' in df_lives.columns:
            # 日付とライブ名を結合
            df_lives['display_name'] = df_lives['日付'].astype(str) + " " + df_lives['ライブ名'].astype(str)
            live_list = df_lives['display_name'].tolist()
            
            selected_live_display = st.selectbox("ライブを選択してください", live_list)
            selected_live_row = df_lives[df_lives['display_name'] == selected_live_display].iloc[0]
        else:
            st.error("「ライブ情報」シートに '日付' または 'ライブ名' 列が見つかりません。")
            st.stop()

    # B) データの紐付け
    if 'ライブID' in df_lives.columns and 'ライブID' in df_songs.columns:
        live_id = selected_live_row['ライブID']
        songs_to_display = df_songs[df_songs['ライブID'] == live_id].copy()
    else:
        st.warning("紐付け用の 'ライブID' が見つかりません。")
        st.stop()

    # C) 楽曲情報の表示
    st.subheader(f"演奏曲目: {selected_live_display}")

    # ソート
    if '曲順' in songs_to_display.columns:
        songs_to_display = songs_to_display.sort_values(by='曲順')

    # D) YouTubeリンクの生成
    video_link_base = selected_live_row.get('動画リンク', "")
    
    required_cols = ['楽曲名', 'ボーカル', 'STARTTIME']
    if all(col in songs_to_display.columns for col in required_cols):
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
                except ValueError:
                    youtube_link = video_link_base

            # シンプルに書き出し
            st.write(f"{song_name} {vocal} {youtube_link}")
    else:
        st.error("「演奏曲目」シートに必要な列がありません。")
