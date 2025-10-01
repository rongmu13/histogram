import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------
# ページ設定
# ------------------------
st.set_page_config(page_title="CSVデータ解析アプリ（複数CSV対応）", layout="wide")
st.title("📊 CSVデータ解析アプリ（複数CSV対応）")

st.markdown(
    """
- 複数のCSVを同時にアップロードできます（ブラウザとメモリが許す限り）。
- 各ファイルごとに数値列を選択して、統計量・ヒストグラム（KDE）を表示します。
- 必要に応じて相関ヒートマップも確認できます。
    """
)

# ------------------------
# サイドバー（共通設定）
# ------------------------
with st.sidebar:
    st.header("⚙️ 共通設定")
    bins = st.slider("ヒストグラムのビン数", min_value=5, max_value=100, value=20, step=1)
    show_kde = st.checkbox("KDE（分布曲線）を重ねる", value=True)
    max_cols_default = st.slider("各ファイルで最初に選択する列の上限", 1, 12, 5, 1)
    show_corr = st.checkbox("相関ヒートマップを表示（数値列が2列以上の場合）", value=True)
    st.caption("⚠️ 大きなCSVや列数が多い場合、描画に時間がかかることがあります。")

# ------------------------
# ファイルアップローダー（複数）
# ------------------------
uploaded_files = st.file_uploader(
    "CSVファイルをアップロードしてください（複数可）",
    type=["csv"],
    accept_multiple_files=True
)

def read_csv_safely(file):
    """UTF-8優先、ダメならShift_JISで再トライ"""
    try:
        return pd.read_csv(file)
    except UnicodeDecodeError:
        file.seek(0)
        return pd.read_csv(file, encoding="shift_jis", errors="ignore")

if uploaded_files:
    for idx, uploaded_file in enumerate(uploaded_files):
        # 各ファイルのセクション
        st.markdown("---")
        st.subheader(f"🗂️ ファイル {idx+1}: {uploaded_file.name}")

        # 読み込み
        df = read_csv_safely(uploaded_file)

        # プレビュー
        st.caption(f"行数: {len(df):,}　列数: {df.shape[1]:,}")
        st.dataframe(df.head(), use_container_width=True)

        # 数値列抽出
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) == 0:
            st.warning("このファイルに数値データが見つかりませんでした。")
            continue

        # 列選択（デフォルトは先頭から max_cols_default 列）
        default_pick = numeric_cols[:max_cols_default]
        cols_to_plot = st.multiselect(
            "解析する数値列を選択してください（複数可）",
            options=numeric_cols,
            default=default_pick,
            key=f"cols_{uploaded_file.name}_{idx}"
        )

        if len(cols_to_plot) == 0:
            st.info("列を選択すると、統計量とグラフを表示します。")
        else:
            # 各列：統計量＋ヒストグラム
            for col in cols_to_plot:
                st.markdown(f"### 📈 {col}")

                c1, c2 = st.columns([1, 2], gap="large")

                with c1:
                    st.caption("基本統計量")
                    st.write(df[col].describe())

                with c2:
                    fig, ax = plt.subplots(figsize=(7, 4.5))
                    sns.histplot(df[col].dropna(), kde=show_kde, bins=bins, ax=ax)
                    ax.set_title(f"{col} の分布", fontsize=13)
                    ax.set_xlabel(col)
                    st.pyplot(fig, clear_figure=True)

            # 相関ヒートマップ（任意）
            if show_corr and len(numeric_cols) >= 2:
                st.markdown("#### 🔗 相関ヒートマップ（数値列 全体）")
                corr = df[numeric_cols].corr()
                fig, ax = plt.subplots(figsize=(min(1.0 * len(numeric_cols) + 6, 16),
                                                min(0.6 * len(numeric_cols) + 4, 12)))
                sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
                ax.set_title("数値列の相関係数", fontsize=13)
                st.pyplot(fig, clear_figure=True)
else:
    st.info("左上の「Browse files」から、CSVファイルを1つ以上アップロードしてください。")
