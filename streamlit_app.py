import time
import random
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="ミニ競馬レースゲーム", layout="wide")

st.title("🏇 簡易ミニ競馬レース（ダビスタ風シミュレーター）")
st.write("お気に入りの馬を登録して、番号（馬）が画面を駆け抜けるレースの様子を見届けよう！")

# セッションステートでゲームの状態を保持
if "race_running" not in st.session_state:
  st.session_state.race_running = False

col1, col2 = st.columns([1, 2])

with col1:
  st.subheader("📝 出走馬の設定")
  
  # デフォルトの出走馬データ
  default_horses = pd.DataFrame([
      {"馬番": 1, "馬名": "サイレンススズカ風", "能力(スピード)": 85, "脚質": "逃げ"},
      {"馬番": 2, "馬名": "ディープインパクト風", "能力(スピード)": 92, "脚質": "差し"},
      {"馬番": 3, "馬名": "オルフェーヴル風", "能力(スピード)": 90, "脚質": "差し"},
      {"馬番": 4, "馬名": "ツインターボ風", "能力(スピード": 78, "脚質": "大逃げ"},
      {"馬番": 5, "馬名": "ゴールドシップ風", "能力(スピード)": 88, "脚質": "追込"},
  ])

  edited_horses = st.data_editor(default_horses, num_rows="dynamic", key="horse_editor")

  race_distance = st.slider("コース距離 (m)", min_value=1000, max_value=3000, value=1600, step=200)

  start_button = st.button("🏁 レーススタート！", type="primary")

with col2:
  st.subheader("🏟️ レース実況＆ビジュアル中継")
  
  race_placeholder = st.empty()
  commentary_placeholder = st.empty()

  if start_button:
    st.session_state.race_running = True
    
    # 準備
    horses = edited_horses.to_dict("records")
    n_horses = len(horses)
    
    if n_horses < 2:
      st.error("馬を2頭以上登録してください！")
    else:
      # 位置情報の初期化 (0m ～ 1000mのプログレスに変換)
      positions = {h["馬名"]: 0 for h in horses}
      max_pos = 1000  # ゴール位置
      
      # 実況ログ
      logs = ["【ファンファーレが鳴り響き、ゲートが開いた！】"]
      commentary_placeholder.markdown("\n\n".join(logs))

      # レース進行ループ（全10ステップでゴールへ）
      for step in range(1, 11):
        time.sleep(0.4) # 演出用のウェイト
        
        progress_html = "<div style='font-family: monospace; font-size: 16px;'>"
        
        for h in horses:
          name = h["馬名"]
          ability = float(h["能力(スピード)"])
          
          # スピードに少しランダムな揺らぎ（展開のあや）をプラス
          speed_factor = random.uniform(0.8, 1.2)
          advance = (ability * speed_factor) * (max_pos / 10) * 0.1
          
          # 脚質ごとの挙動補正
          if h["脚質"] == "逃げ" and step <= 5:
            advance *= 1.3
          elif h["脚質"] in ["差し", "追込"] and step >= 6:
            advance *= 1.4
            
          positions[name] = min(max_pos, positions[name] + advance)
          
          # グラフ風に進捗バー（--馬番-- 🐎==========）を表示
          percent = int((positions[name] / max_pos) * 40)
          bar = "=" * percent + "🐎" + "-" * max(0, 40 - percent)
          progress_html += f"<b>{h['馬番']}番 {name}</b> [{h['脚質']}]<br>{bar} ({int(positions[name])}m)<br><br>"
          
        progress_html += "</div>"
        race_placeholder.markdown(progress_html, unsafe_allow_html=True)
        
        # 途中経過の実況
        if step == 3:
          leader = max(positions, key=positions.get)
          logs.append(f"【3コーナー通過】 現在先頭は <b>{leader}</b>！各馬固まって第3コーナーへ！")
        elif step == 7:
          leader = max(positions, key=positions.get)
          logs.append(f"【直線に向いた！】 さあ先頭は <b>{leader}</b>！後方から追い込んでくる馬はいるか！？")
          
        commentary_placeholder.markdown("\n\n".join(logs))

      # ゴール判定
      sorted_finish = sorted(positions.items(), key=lambda x: x[1], reverse=True)
      winner = sorted_finish[0][0]
      second = sorted_finish[1][0]
      third = sorted_finish[2][0] if len(sorted_finish) > 2 else ""

      logs.append(f"🎉 **【ゴールイン！】 優勝は {winner} ！！** 2着は {second}、3着は {third} でした！")
      commentary_placeholder.markdown("\n\n".join(logs))
