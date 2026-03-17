import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import re
import requests
import json

# ページ設定
st.set_page_config(page_title="VSOPライブ情報", layout="wide")

# セッション状態の初期化
if 'mode' not in st.session_state:
    st.session_state.mode = 'view'

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

def call_gas_api(action, payload):
    # ユーザー提供の GAS Web App URL
    gas_url = "https://script.google.com/macros/s/AKfycbzlBnl1yfHCy2CYS4lT3xlGG9SFLzSh_jQHlBuIkuHlHFFGxqMxAd4P_RlvU2Wqiwhd/exec"
    
    payload['action'] = action
    try:
        # GASへのPOSTリクエスト (JSON型式)
        response = requests.post(gas_url, data=json.dumps(payload), timeout=10)
        return response.text
    except Exception as e:
        return f"error: {str(e)}"

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
    a { color: #0068c9; text-decoration: none; }
</style>
"""

# サイドバー
with st.sidebar:
    st.header("🔍 ライブ選択")
    if date_col and live_name_col:
        df_lives['display_name'] = df_lives[date_col].astype(str) + " " + df_lives[live_name_col].astype(str)
        selected_live_display = st.selectbox("ライブを選択してください", df_lives['display_name'].tolist())
        selected_live_row = df_lives[df_lives['display_name'] == selected_live_display].iloc[0]
        live_id_val = selected_live_row[id_col_lives]
    else:
        st.stop()

    st.markdown("---")
    col1, col2 = st.columns(2)
    if col1.button("📱 表示"):
        st.session_state.mode = 'view'
    if col2.button("✍️ 感想"):
        st.session_state.mode = 'post'

    st.info(f"現在のモード: {'ライブ情報表示' if st.session_state.mode == 'view' else '感想投稿フォーム'}")
    st.warning("⚠️ 翻訳をオフにしてください。")

# --- メインロジック ---
st.title("VSOPライブ情報")
st.subheader(f"{selected_live_display}")

if st.session_state.mode == 'view':
    # セットリスト抽出
    songs_to_display = df_songs[df_songs[id_col_songs].astype(str) == str(live_id_val)].copy() if id_col_songs else pd.DataFrame()
    feedback_to_display = df_feedback[df_feedback[id_col_f].astype(str) == str(live_id_val)].copy() if id_col_f else pd.DataFrame()

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
            name, vocal, t = row[song_name_col], row[vocal_col], row[time_col]
            y_url = ""
            if pd.notna(video_link_base) and pd.notna(t) and t != 0:
                try:
                    if isinstance(t, str) and ":" in t:
                        p = t.split(':'); s = int(p[-1]) + int(p[-2]) * 60 + (int(p[-3]) * 3600 if len(p) > 2 else 0)
                    else: s = int(float(t))
                    y_url = f"{video_link_base}{'&' if '?' in str(video_link_base) else '?'}t={s}"
                except: y_url = video_link_base
            html += f"<tr><td class='no-col'>{i}</td><td>{name}</td><td>{vocal}</td><td><a href='{y_url}' target='_blank'>視聴</a></td></tr>"
        html += "</table></div>"
        components.html(html, height=min(400, len(songs_to_display) * 50 + 80), scrolling=True)

    st.markdown("### 💬 ライブ感想")
    if not feedback_to_display.empty:
        # 表示（Ver 3.3を踏襲）
        html_f = table_style + "<div class='frame-container' style='background-color: #fff9f0;'><table class='custom-table'>"
        html_f += "<tr><th class='no-col'>#</th><th>感想内容</th><th>投稿者</th><th>投稿日時</th></tr>"
        for i, (_, row) in enumerate(feedback_to_display.iterrows(), 1):
            # A=ID, B=投稿者(1), C=内容(2), D=日時(3)
            author, txt, dt = row.iloc[1], row.iloc[2], row.iloc[3]
            html_f += f"<tr><td class='no-col'>{i}</td><td>{txt}</td><td>{author}</td><td>{dt}</td></tr>"
        html_f += "</table></div>"
        components.html(html_f, height=250, scrolling=True)

        # 削除機能
        with st.expander("🗑 感想の削除"):
            st.write("削除したい感想の「登録キー」を入力してください。")
            del_key = st.text_input("登録キー", type="password", key="del_key_input")
            if st.button("削除を実行"):
                if not del_key:
                    st.error("登録キーを入力してください。")
                else:
                    res = call_gas_api("delete", {"live_no": str(live_id_val), "key": del_key})
                    if res == "success":
                        st.success("削除しました。")
                        st.cache_data.clear() # キャッシュクリア
                        st.rerun()
                    elif "gas_url_not_configured" in res:
                        st.error("GASのURLが設定されていません。")
                    else:
                        st.error(f"削除に失敗しました: {res}")
    else:
        st.info("感想未登録")

elif st.session_state.mode == 'post':
    st.markdown("### ✍️ 感想を投稿する")
    with st.container():
        st.write(f"【選択中】 {selected_live_display}")
        u_name = st.text_input("お名前", placeholder="例：VSOPファン")
        u_comment = st.text_area("感想本文", placeholder="楽しかった！などの感想をお願いします")
        u_key = st.text_input("登録キー（削除時に必要です）", type="password", placeholder="任意の英数字")
        
        if st.button("投稿する"):
            if not u_name or not u_comment or not u_key:
                st.error("すべての項目を入力してください（登録キーは空白不可です）。")
            else:
                with st.spinner("送信中..."):
                    res = call_gas_api("add", {
                        "live_no": str(live_id_val),
                        "author": u_name,
                        "text": u_comment,
                        "key": u_key
                    })
                    if res == "success":
                        st.success("投稿が完了しました！")
                        st.cache_data.clear()
                        st.session_state.mode = 'view'
                        st.rerun()
                    elif "gas_url_not_configured" in res:
                        st.error("GASのURLが設定されていません。")
                    else:
                        st.error(f"エラーが発生しました: {res}")
        
        if st.button("キャンセル"):
            st.session_state.mode = 'view'
            st.rerun()
