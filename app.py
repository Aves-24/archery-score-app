import streamlit as st
from datetime import date

# Konfiguracja strony
st.set_page_config(page_title="Łucznik - Karta Punktowa", layout="centered")

# --- INICJALIZACJA ZMIENNYCH ---
if 'started' not in st.session_state:
    st.session_state.started = False
if 'scores' not in st.session_state:
    st.session_state.scores = []

def add_score(val):
    if len(st.session_state.scores) < st.session_state.max_total_arrows:
        st.session_state.scores.append(val)

def undo_score():
    if len(st.session_state.scores) > 0:
        st.session_state.scores.pop()

def reset():
    st.session_state.started = False
    st.session_state.scores = []

# --- EKRAN STARTOWY ---
if not st.session_state.started:
    st.title("🏹 Karta Punktowa")
    
    col_a, col_b = st.columns(2)
    with col_a:
        event_type = st.radio("Wydarzenie:", ["Trening", "Turniej"])
    with col_b:
        arrows_per_end = st.radio("Strzał w serii:", [3, 6], index=1)
        
    event_name = st.text_input("Nazwa (opcjonalnie):", placeholder="np. Kwalifikacje")
    ends_per_round = st.number_input("Ilość serii w rundzie:", min_value=1, value=6)
    
    st.subheader("Wybierz Dystans i Tarczę:")
    col1, col2, col3 = st.columns(3)

    base_info = {
        "Data": date.today().strftime("%d.%m.%Y"),
        "Typ": event_type,
        "Nazwa": event_name if event_name else "-",
        "StrzalWSerii": arrows_per_end,
        "SeriiWRundzie": ends_per_round
    }

    max_arrows_per_round = arrows_per_end * ends_per_round
    max_total_arrows = max_arrows_per_round * 2

    def start_session(dystans):
        st.session_state.event_info = base_info
        st.session_state.event_info["Dystans"] = dystans
        st.session_state.max_arrows_per_round = max_arrows_per_round
        st.session_state.max_total_arrows = max_total_arrows
        st.session_state.started = True
        st.rerun()

    with col1:
        st.markdown("<div style='text-align: center; font-size: 30px;'>🎯<br>🎯<br>🎯</div>", unsafe_allow_html=True)
        if st.button("18m (Spot)", use_container_width=True): start_session("18m")
    with col2:
        st.markdown("<div style='text-align: center; font-size: 60px; margin: 15px 0;'>🎯</div>", unsafe_allow_html=True)
        if st.button("30m (80cm)", use_container_width=True): start_session("30m")
    with col3:
        st.markdown("<div style='text-align: center; font-size: 60px; margin: 15px 0;'>🎯</div>", unsafe_allow_html=True)
        if st.button("70m (120cm)", use_container_width=True): start_session("70m")

# --- EKRAN TARCZY (PUNKTACJA) ---
else:
    # --- CSS: MAGICZNA TARCZA ANTY-MOBILNA ---
    st.markdown("""
    <style>
        /* 1. Reset szerokości strony na telefonie (usuwa białe paski po bokach) */
        .block-container {
            padding-left: 0.2rem !important;
            padding-right: 0.2rem !important;
            padding-top: 1rem !important;
            max-width: 100% !important;
            overflow-x: hidden !important;
        }

        /* 2. Brutalne wymuszenie RZĘDÓW (zakaz układania w pionie dla telefonu) */
        /* Dzięki klasie .keypad chronimy resztę aplikacji przed tym kodem */
        div[data-testid="stVerticalBlock"]:has(.keypad) > div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 4px !important;
            width: 100% !important;
        }

        /* 3. Precyzyjna szerokość 4 filarów (każdy idealnie po 25% ekranu) */
        div[data-testid="stVerticalBlock"]:has(.keypad) > div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"] {
            flex: 1 1 25% !important;
            width: 25% !important;
            min-width: 0 !important;
            padding: 0 !important;
        }

        /* Szerokość dolnego rzędu (Zegar 25%, Cofnij 75%) */
        div[data-testid="stVerticalBlock"]:has(.keypad) > div[data-testid="stHorizontalBlock"]:nth-of-type(2) div[data-testid="column"]:nth-child(1) {
            flex: 1 1 25% !important; width: 25% !important; min-width: 0 !important; padding: 0 !important;
        }
        div[data-testid="stVerticalBlock"]:has(.keypad) > div[data-testid="stHorizontalBlock"]:nth-of-type(2) div[data-testid="column"]:nth-child(2) {
            flex: 3 1 75% !important; width: 75% !important; min-width: 0 !important; padding: 0 !important;
        }

        /* 4. Wygląd guzików (Wielkie, pogrubione, ciasno upchane) */
        div[data-testid="stVerticalBlock"]:has(.keypad) div.stButton > button {
            width: 100% !important;
            height: 65px !important;
            font-size: 22px !important;
            font-weight: 900 !important;
            padding: 0 !important;
            margin-bottom: 4px !important;
            border-radius: 8px !important;
            box-shadow: 0 3px 0px rgba(0,0,0,0.1) !important;
        }

        /* --- 5. TWARDE KOLORY DLA FILARÓW PIONOWYCH --- */
        /* Filar 1: X(Y), 7(R), 3(B) */
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(1) div.stButton:nth-of-type(1) button { background: #FCE205 !important; color: black !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(1) div.stButton:nth-of-type(2) button { background: #E53935 !important; color: white !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(1) div.stButton:nth-of-type(3) button { background: #212121 !important; color: white !important; border: none !important; }

        /* Filar 2: 10(Y), 6(N), 2(B) */
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(2) div.stButton:nth-of-type(1) button { background: #FCE205 !important; color: black !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(2) div.stButton:nth-of-type(2) button { background: #039BE5 !important; color: white !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(2) div.stButton:nth-of-type(3) button { background: #FFFFFF !important; color: black !important; border: 2px solid #CCC !important; }

        /* Filar 3: 9(Y), 5(N), 1(B) */
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(3) div.stButton:nth-of-type(1) button { background: #FCE205 !important; color: black !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(3) div.stButton:nth-of-type(2) button { background: #039BE5 !important; color: white !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(3) div.stButton:nth-of-type(3) button { background: #FFFFFF !important; color: black !important; border: 2px solid #CCC !important; }

        /* Filar 4: 8(R), 4(B), M(B) */
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(4) div.stButton:nth-of-type(1) button { background: #E53935 !important; color: white !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(4) div.stButton:nth-of-type(2) button { background: #212121 !important; color: white !important; border: none !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(1) div[data-testid="column"]:nth-child(4) div.stButton:nth-of-type(3) button { background: #FFFFFF !important; color: black !important; border: 2px solid #CCC !important; }

        /* Rząd Dolny: Zegar i Cofnij */
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(2) div[data-testid="column"]:nth-child(1) div.stButton button { background: #F0F3F4 !important; color: black !important; border: none !important; font-size: 26px !important; }
        div[data-testid="stVerticalBlock"]:has(.keypad) div[data-testid="stHorizontalBlock"]:nth-of-type(2) div[data-testid="column"]:nth-child(2) div.stButton button { background: #5DADE2 !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

    info = st.session_state.event_info
    scores = st.session_state.scores
    arrows_per_end = info['StrzalWSerii']
    max_round_score = st.session_state.max_arrows_per_round * 10
    max_total_score = st.session_state.max_total_arrows * 10
    
    def get_num(s): return 10 if s in ["X", "10"] else (0 if s == "M" else int(s))
    
    total_points = sum(get_num(s) for s in scores)
    count_x = scores.count("X")
    count_10 = scores.count("10")
    count_9 = scores.count("9")
    avg = total_points / len(scores) if len(scores) > 0 else 0
    percent = (total_points / (len(scores) * 10) * 100) if len(scores) > 0 else 0

    # --- NAGŁÓWEK ---
    st.markdown(f"### {info['Typ']} ({info['Data']})")
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.write(f"Strzały: **{len(scores)}/{st.session_state.max_total_arrows}**")
    with col_stat2:
        st.write(f"Punkty: **{total_points}/{max_total_score} ({percent:.0f}%)**")

    st.divider()

    # --- KLAWIATURA (FILARY PIONOWE) ---
    # Pakujemy wszystko do jednego wirtualnego kontenera "keypad", żeby CSS zadziałał tylko tutaj
    with st.container():
        st.markdown('<div class="keypad"></div>', unsafe_allow_html=True)
        
        # 4 Pionowe Kolumny
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            st.button("X", on_click=add_score, args=("X",), use_container_width=True)
            st.button("7", on_click=add_score, args=("7",), use_container_width=True)
            st.button("3", on_click=add_score, args=("3",), use_container_width=True)
        with col2: 
            st.button("10", on_click=add_score, args=("10",), use_container_width=True)
            st.button("6", on_click=add_score, args=("6",), use_container_width=True)
            st.button("2", on_click=add_score, args=("2",), use_container_width=True)
        with col3: 
            st.button("9", on_click=add_score, args=("9",), use_container_width=True)
            st.button("5", on_click=add_score, args=("5",), use_container_width=True)
            st.button("1", on_click=add_score, args=("1",), use_container_width=True)
        with col4: 
            st.button("8", on_click=add_score, args=("8",), use_container_width=True)
            st.button("4", on_click=add_score, args=("4",), use_container_width=True)
            st.button("M", on_click=add_score, args=("M",), use_container_width=True)
            
        # Rząd na samym dole
        col_z, col_c = st.columns([1, 3])
        with col_z: st.button("⏱️", disabled=True, use_container_width=True)
        with col_c: st.button("⌫ COFNIJ", on_click=undo_score, use_container_width=True)

    st.divider()

    # --- TABELA HTML (Z kolorowymi kółkami, dokładnie jak ze zdjęcia) ---
    def get_color_style(val):
        if val in ["X", "10", "9"]: return "background-color: #FCE205; color: black;"
        if val in ["8", "7"]: return "background-color: #E53935; color: white;"
        if val in ["6", "5"]: return "background-color: #039BE5; color: white;"
        if val in ["4", "3"]: return "background-color: #212121; color: white;"
        if val in ["2", "1"]: return "background-color: #ffffff; color: black; border: 1px solid #ccc;"
        if val == "M": return "background-color: #9e9e9e; color: white;"
        return "background-color: transparent;"

    def render_round_html(round_num, round_scores, cumulative_start):
        r_points = sum(get_num(s) for s in round_scores)
        r_max_current = len(round_scores) * 10
        r_percent = (r_points / r_max_current * 100) if r_max_current > 0 else 0
        
        html = f"""
        <div style='margin-bottom: 20px; font-family: Arial, sans-serif;'>
            <b>Runda {round_num}</b><br>
            Punkty: <b>{r_points}/{max_round_score} ({r_percent:.0f}%)</b>
            <table style='width: 100%; border-collapse: collapse; text-align: center; margin-top: 5px;'>
                <tr style='background-color: #f2f2f2; border-bottom: 2px solid #ddd;'>
                    <th colspan='{arrows_per_end}' style='padding: 5px; border: 1px solid #ddd;'>Strzały</th>
                    <th style='padding: 5px; border: 1px solid #ddd;'>Suma</th>
                    <th style='padding: 5px; border: 1px solid #ddd;'>Razem</th>
                </tr>
        """
        
        cumul_total = cumulative_start
        for i in range(0, len(round_scores), arrows_per_end):
            end_scores = round_scores[i:i+arrows_per_end]
            end_sum = sum(get_num(s) for s in end_scores)
            cumul_total += end_sum
            
            html += "<tr>"
            for j in range(arrows_per_end):
                if j < len(end_scores):
                    val = end_scores[j]
                    style = get_color_style(val)
                    circle = f"<div style='width: 28px; height: 28px; border-radius: 50%; {style} display: inline-flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold;'>{val}</div>"
                    html += f"<td style='padding: 5px; border: 1px solid #ddd;'>{circle}</td>"
                else:
                    html += "<td style='padding: 5px; border: 1px solid #ddd;'></td>"
            
            html += f"<td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>{end_sum}</td>"
            html += f"<td style='padding: 5px; border: 1px solid #ddd; font-weight: bold;'>{cumul_total}</td>"
            html += "</tr>"
            
        html += "</table></div>"
        return html, cumul_total

    round1_scores = scores[:st.session_state.max_arrows_per_round]
    round2_scores = scores[st.session_state.max_arrows_per_round:]

    if len(round1_scores) > 0:
        html1, cumul1 = render_round_html(1, round1_scores, 0)
        st.markdown(html1, unsafe_allow_html=True)
        
    if len(round2_scores) > 0:
        html2, _ = render_round_html(2, round2_scores, cumul1)
        st.markdown(html2, unsafe_allow_html=True)

    if st.button("Zakończ strzelanie", type="secondary", use_container_width=True):
        reset()
        st.rerun()
