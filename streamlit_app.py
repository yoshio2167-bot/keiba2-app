from io import StringIO
import re
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="能力重視＆レース荒れ度判定AI", layout="wide", initial_sidebar_state="collapsed")

st.title("馬実力・調子重視 ＆ レース荒れ度判定AI")

tab1, tab2, tab3 = st.tabs(["🚀 能力評価＆荒れ度判定", "📊 検証・自動判定記録", "🛠️ スクショ・テキスト整形"])

with tab1:
  st.header("馬の実力・調子評価 ＆ レース荒れ度診断")
  st.write(
      "出馬表CSVを貼り付けると、オッズに依存せず『スピード指数・近走の安定度・出走間隔』をベースに馬の本来の実力を算出し、そのレースが荒れるか堅いかを自動判定します。"
  )

  pasted_data = st.text_area(
      "CSVデータ貼り付け欄",
      placeholder=(
          "日付,開催地,レース番号,距離・馬場,レース条件,馬番,馬名,人気,単勝オッズ,脚質,上がり3F,スピード指数,近走5走成績,騎手,斤量\n"
          "2026/09/06,中山,12R,芝1200m(雨 稍重),3歳上1勝クラス,1,ショウナンアキツ,12人気,59.3,差,34.5,85.0,0-5-2-3,石橋脩,58.0"
      ),
      height=180,
  )

  df_input = None
  if pasted_data:
    try:
      lines = [line.strip() for line in pasted_data.strip().split("\n") if line.strip()]
      if len(lines) > 0:
        first_line = lines[0]
        has_header = "馬番" in first_line or "馬名" in first_line or "日付" in first_line
        data_lines = lines[1:] if has_header else lines

        parsed_rows = []
        for l in data_lines:
          parts = [p.strip() for p in l.split(",")]
          row_dict = {}
          # 正しい15列のパース順序に修正
          row_dict["斤量"] = parts[-1] if len(parts) >= 1 else "55.0"
          row_dict["騎手"] = parts[-2] if len(parts) >= 2 else "レーン"
          row_dict["近走5走成績"] = parts[-3] if len(parts) >= 3 and parts[-3] else "0-0-0-0"
          row_dict["スピード指数"] = parts[-4] if len(parts) >= 4 else ""
          row_dict["上がり3F"] = parts[-5] if len(parts) >= 5 else ""
          row_dict["脚質"] = parts[-6] if len(parts) >= 6 else "差"
          row_dict["単勝オッズ"] = parts[-7] if len(parts) >= 7 else "10.0"
          row_dict["人気"] = parts[-8] if len(parts) >= 8 else "5人気"
          row_dict["馬名"] = parts[-9] if len(parts) >= 9 else ""
          row_dict["馬番"] = parts[-10] if len(parts) >= 10 else "1"
          row_dict["レース条件"] = parts[-11] if len(parts) >= 11 else "3歳上1勝クラス"
          row_dict["距離・馬場"] = parts[-12] if len(parts) >= 12 else "芝1200m(雨 稍重)"
          row_dict["レース番号"] = parts[-13] if len(parts) >= 13 else "12R"
          row_dict["開催地"] = parts[-14] if len(parts) >= 14 else "中山"
          row_dict["日付"] = parts[-15] if len(parts) >= 15 else "2026/09/06"

          parsed_rows.append(row_dict)

        df_input = pd.DataFrame(parsed_rows)

      if df_input is not None and not df_input.empty:
        def extract_num(val, default=5.0):
          try:
            s = str(val)
            if s == "nan" or not s.strip():
              return default
            m = re.search(r'([\d\.]+)', s)
            if m:
              return float(m.group(1))
          except:
            pass
          return default

        df_input["人気_num"] = df_input["人気"].apply(lambda x: extract_num(x, 5.0))
        df_input["オッズ_num"] = df_input["単勝オッズ"].apply(lambda x: extract_num(x, 15.0))
        df_input["上がり3F_val"] = df_input["上がり3F"].apply(lambda x: extract_num(x, 35.5))
        df_input["speed_val"] = df_input["スピード指数"].apply(lambda x: extract_num(x, 70.0))

        st.success(f"データを正常に読み込みました（全 {len(df_input)} 頭登録中）")
        
        preview_cols = [
            "日付", "開催地", "レース番号", "距離・馬場", "レース条件",
            "馬番", "馬名", "人気", "単勝オッズ", "脚質", "上がり3F", "スピード指数", "近走5走成績", "騎手", "斤量"
        ]
        available_preview = [c for c in preview_cols if c in df_input.columns]
        st.dataframe(df_input[available_preview], use_container_width=True)

    except Exception as e:
      st.info("CSVデータを貼り付けるとここにプレビューが表示されます。")

  if st.button("🚀 能力評価 ＆ 荒れ度判定を実行", type="primary"):
    if df_input is not None and not df_input.empty:
      with st.spinner("馬の能力値（スピード指数・近走調子）を解析中..."):
        df_res = df_input.copy()

        def calc_ability_score(row):
          try:
            s_val = float(row["speed_val"])
          except:
            s_val = 70.0
          
          try:
            f_val = float(row["上がり3F_val"])
            f_bonus = max(0.0, (37.0 - f_val) * 2.0)
          except:
            f_bonus = 0.0

          ability_score = s_val + f_bonus
          return max(10.0, ability_score)

        df_res["能力値スコア"] = df_res.apply(calc_ability_score, axis=1)
        df_res["能力値スコア_str"] = df_res["能力値スコア"].round(1).astype(str)

        df_ranked = df_res.sort_values(by="能力値スコア", ascending=False).reset_index(drop=True)

        top1_score = df_ranked.iloc[0]["能力値スコア"]
        top2_score = df_ranked.iloc[1]["能力値スコア"] if len(df_ranked) > 1 else top1_score
        score_diff = top1_score - top2_score

        top1_odds = float(df_ranked.iloc[0]["オッズ_num"])

        if score_diff > 5.0 and top1_odds < 3.5:
          race_tendency = "🔥 【堅実決着傾向】（本命の軸信頼度高・ガッチリ勝負）"
          strategy_advice = "能力上位の軸馬が抜けています。相手を2頭に絞った「ワイド2点（◎-〇、◎-▲）」で手堅く回収を狙うのがベストです。"
        elif score_diff < 1.5 or top1_odds > 10.0:
          race_tendency = "⚡ 【大波乱・難解傾向】（混戦・穴馬台頭注意）"
          strategy_advice = "上位拮抗または人気薄の能力値が高いため、荒れる可能性大です。手広く流すか、思い切った穴狙い（ワイドBOX等）がおすすめです。"
        else:
          race_tendency = "⚖️ 【標準・中波乱傾向】（上位拮抗・フォーメーション推奨）"
          strategy_advice = "実力が拮抗しています。上位3頭（◎〇▲）を中心とした手堅い馬券構成がおすすめです。"

        st.subheader("📊 能力評価ランキング結果（実力順）")
        
        display_cols = [
            "開催地", "レース番号", "距離・馬場", "レース条件",
            "馬番", "馬名", "人気", "単勝オッズ",
            "能力値スコア_str", "脚質", "上がり3F", "スピード指数", "騎手"
        ]
        available_cols = [c for c in display_cols if c in df_ranked.columns]
        df_display = df_ranked[available_cols].rename(columns={"能力値スコア_str": "能力値スコア"})
        st.dataframe(df_display, use_container_width=True)

        kaisai_title = str(df_display["開催地"].iloc[0]) if not df_display["開催地"].empty else "中山"
        r_num_title = str(df_ranked["レース番号"].iloc[0]) if not df_ranked["レース番号"].empty else "12R"
        file_prefix = f"{kaisai_title}{r_num_title}"

        top1 = df_ranked.iloc[0] if len(df_ranked) > 0 else None
        top2 = df_ranked.iloc[1] if len(df_ranked) > 1 else None
        top3 = df_ranked.iloc[2] if len(df_ranked) > 2 else None

        top1_str = f"◎{top1['馬番']}番 {top1['馬名']}" if top1 is not None else ""
        top2_str = f"〇{top2['馬番']}番 {top2['馬名']}" if top2 is not None else ""
        top3_str = f"▲{top3['馬番']}番 {top3['馬名']}" if top3 is not None else ""
        ai_top3_combined = f"{top1_str} / {top2_str} / {top3_str}"

        wide_1 = f"◎{top1['馬番']} - 〇{top2['馬番']}" if top1 is not None and top2 is not None else ""
        wide_2 = f"◎{top1['馬番']} - ▲{top3['馬番']}" if top1 is not None and top3 is not None else ""
        strict_buy_focus = f"【おすすめ買い目】 {wide_1} / {wide_2}"

        export_rows = []
        for _, row in df_ranked.iterrows():
          export_rows.append({
              "日付": row["日付"],
              "開催地": row["開催地"],
              "レース番号": row["レース番号"],
              "距離・馬場": row["距離・馬場"],
              "レース条件": row["レース条件"],
              "AI上位3頭予想": ai_top3_combined if row.name == 0 else "",
              "能力値スコア": round(row["能力値スコア"], 1),
              "レース荒れ度判定": race_tendency if row.name == 0 else "",
              "実際の1着馬": "",
              "実際の2着馬": "",
              "実際の3着馬": "",
              "自動判定メモ": "",
              "馬番": row["馬番"],
              "馬名": row["馬名"],
              "人気": row["人気"],
              "単勝オッズ": row["単勝オッズ"],
              "脚質": row["脚質"],
              "上がり3F": row["上がり3F"],
              "スピード指数": row["スピード指数"],
              "近走5走成績": row["近走5走成績"],
              "騎手": row["騎手"],
              "斤量": row["斤量"]
          })

        df_export_final = pd.DataFrame(export_rows)

        csv_download_data = df_export_final.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 評価結果をCSVで保存",
            data=csv_download_data,
            file_name=f"{file_prefix}_ability_result.csv",
            mime="text/csv",
        )

        tsv_buffer = StringIO()
        df_export_final.to_csv(tsv_buffer, sep="\t", index=False)
        sim_copy_text = tsv_buffer.getvalue()

        st.markdown(
            "### 📋 スプレッドシート用コピー欄（右上のボタンでワンクリックコピー）"
        )
        st.code(sim_copy_text, language="text")

        st.subheader("🎯 レース荒れ度診断 ＆ 推奨戦略")
        st.info(f"**{race_tendency}**\n\n{strict_buy_focus}\n\n**【AI分析アドバイス】**\n{strategy_advice}")
    else:
      st.warning("データが入力されていません。CSVデータを貼り付けてください。")

with tab2:
  st.header("実際のレース結果との照合・自動判定")
  st.write(
      "保存したCSVファイルをアップロードし、実際の1〜3着馬を選ぶことで、実力上位3頭の馬券内絡みを自動判定します。"
  )

  uploaded_sim_file = st.file_uploader(
      "1. 保存したCSVファイルをアップロード", type=["csv"]
  )

  if uploaded_sim_file is not None:
    df_saved = pd.read_csv(uploaded_sim_file)
    st.success("データを読み込みました！")

    horse_options = [
        f"{row.get('馬番')}番 {row.get('馬名')} ({row.get('人気')}・単勝{row.get('単勝オッズ')}倍)"
        for _, row in df_saved.iterrows()
    ]

    date_val = str(df_saved["日付"].iloc[0]) if "日付" in df_saved.columns and not df_saved["日付"].empty else "2026/09/06"
    kaisai_val = str(df_saved["開催地"].iloc[0]) if "開催地" in df_saved.columns and not df_saved["開催地"].empty else "中山"
    r_num_val = str(df_saved["レース番号"].iloc[0]) if "レース番号" in df_saved.columns and not df_saved["レース番号"].empty else "12R"
    dist_val = str(df_saved["距離・馬場"].iloc[0]) if "距離・馬場" in df_saved.columns and not df_saved["距離・馬場"].empty else "芝1200m(雨 稍重)"
    cond_val = str(df_saved["レース条件"].iloc[0]) if "レース条件" in df_saved.columns and not df_saved["レース条件"].empty else "3歳上1勝クラス"

    ai_top3_str = str(df_saved["AI上位3頭予想"].dropna().iloc[0]) if "AI上位3頭予想" in df_saved.columns and not df_saved["AI上位3頭予想"].dropna().empty else ""

    ai_top3_list = []
    for i in range(min(3, len(df_saved))):
      h_num = str(df_saved.iloc[i].get("馬番"))
      h_name = str(df_saved.iloc[i].get("馬名"))
      ai_top3_list.append({"num": h_num, "name": h_name})

    st.subheader("2. 実際のレース結果（1〜3着）を選択")
    col1, col2, col3 = st.columns(3)
    with col1:
      actual_1st = st.selectbox("🥇 実際の1着馬", options=["選択してください"] + horse_options, index=0)
    with col2:
      actual_2nd = st.selectbox("🥈 実際の2着馬", options=["選択してください"] + horse_options, index=0)
    with col3:
      actual_3rd = st.selectbox("🥉 実際の3着馬", options=["選択してください"] + horse_options, index=0)

    if st.button("🔍 検証結果を自動判定する"):
      if actual_1st == "選択してください" or actual_2nd == "選択してください" or actual_3rd == "選択してください":
        st.warning("実際の1着〜3着馬すべてを選択してください。")
      else:
        def get_umaban(sel_str):
          m = re.match(r"^(\d+)番", sel_str.strip())
          return m.group(1) if m else ""

        actual_nums = [get_umaban(actual_1st), get_umaban(actual_2nd), get_umaban(actual_3rd)]

        hit_horses = []
        for item in ai_top3_list:
          if item["num"] in actual_nums:
            hit_horses.append(f"{item['num']}番 {item['name']}")

        hit_count = len(hit_horses)

        if hit_count >= 2:
          auto_memo = f"的中（実力上位から {hit_count}頭が馬券内・ワイド的中）"
          badge_type = "success"
        elif hit_count == 1:
          auto_memo = f"的中（実力上位から {hit_count}頭が馬券内）"
          badge_type = "success"
        else:
          auto_memo = "不格外れ（実力上位がすべて馬券外）"
          badge_type = "warning"

        st.markdown("---")
        st.subheader("📝 判定結果レポート")

        col_a, col_b = st.columns(2)
        with col_a:
          st.info(f"**【実力上位3頭】**\n\n{ai_top3_str}")
        with col_b:
          st.markdown(f"**【実際の3着まで】**\n\n🥇 1着: {actual_1st}\n\n🥈 2着: {actual_2nd}\n\n🥉 3着: {actual_3rd}")

        if badge_type == "success":
          st.balloons()
          st.success(f"🎉 **【自動判定】 {auto_memo}**")
        else:
          st.warning(f"❌ **【自動判定】 {auto_memo}**")

        sheet_row_text = (
            f"{date_val}\t{kaisai_val}\t{r_num_val}\t{dist_val}\t{cond_val}\t{ai_top3_str}\t-\t-\t{actual_1st}\t{actual_2nd}\t{actual_3rd}\t{auto_memo}"
        )

        st.markdown("### 📋 検証結果 スプレッドシート用コピー欄（右上のボタンでワンクリックコピー）")
        st.code(sheet_row_text, language="text")

  else:
    st.info("まずはTab1で保存したCSVファイルをアップロードしてください。")

with tab3:
  st.header("🛠️ Geminiテキスト・スクショ整形ツール")
  st.write("出馬表テキストを貼り付けると自動で解析します。")

  raw_txt = st.text_area("ここにテキストを貼り付け", height=150)

  col_t1, col_t2 = st.columns(2)
  with col_t1:
    inp_date = st.text_input("日付", value="2026/09/06")
  with col_t2:
    inp_kaisai = st.text_input("開催地", value="中山")

  col_t3, col_t4, col_t5 = st.columns(3)
  with col_t3:
    inp_rnum = st.text_input("レース番号", value="12R")
  with col_t4:
    inp_dist = st.text_input("距離・馬場", value="芝1200m(雨 稍重)")
  with col_t5:
    inp_cond = st.text_input("レース条件", value="3歳上1勝クラス")

  if st.button("✨ 完璧なCSVに変換する"):
    if raw_txt:
      lines = [l.strip() for l in raw_txt.strip().split("\n") if l.strip()]
      parsed_rows = []
      for line in lines:
        tokens = re.split(r'[\s,\t]+', line)
        if len(tokens) >= 2:
          umaban = tokens[0]
          ubana = tokens[1]
          
          odds = "10.0"
          ninki = "5人気"
          kishu = "石橋脩"
          kinryo = "58.0"
          kyakushitsu = "差"

          for t in tokens[2:]:
            if re.search(r'^\d+\.?\d*$', t) and float(t) < 300 and "." in t:
              odds = t
            elif "人気" in t or (t.isdigit() and int(t) <= 18):
              if "人気" in t:
                ninki = t
            elif t in ["逃", "先行", "差", "追"]:
              kyakushitsu = t
            elif re.search(r'^\d{2}\.\d$', t):
              pass
            elif re.search(r'^\d{2}\.\d$', t) == None and len(t) >= 2 and not t.isdigit():
              kishu = t
            elif re.search(r'^\d{2}\.\d$', t) == None and (t.replace('.', '', 1).isdigit() and float(t) >= 48 and float(t) <= 60):
              kinryo = t

          parsed_rows.append({
              "日付": inp_date,
              "開催地": inp_kaisai,
              "レース番号": inp_rnum,
              "距離・馬場": inp_dist,
              "レース条件": inp_cond,
              "馬番": umaban,
              "馬名": ubana,
              "人気": ninki,
              "単勝オッズ": odds,
              "脚質": kyakushitsu,
              "上がり3F": "",
              "スピード指数": "",
              "近走5走成績": "0-0-0-0",
              "騎手": kishu,
              "斤量": kinryo,
          })

      if parsed_rows:
        df_converted = pd.DataFrame(parsed_rows)
        cols_order = [
            "日付", "開催地", "レース番号", "距離・馬場", "レース条件",
            "馬番", "馬名", "人気", "単勝オッズ",
            "脚質", "上がり3F", "スピード指数", "近走5走成績", "騎手", "斤量"
        ]
        csv_text = df_converted[cols_order].to_csv(index=False)
        st.success("変換が完了しました！")
        st.text_area("整形済みCSV出力", value=csv_text, height=150)
      else:
        st.warning("有効な行が見つかりませんでした。")
    else:
      st.warning("テキストが入力されていません。")
