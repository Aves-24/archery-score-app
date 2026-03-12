import streamlit as st
from datetime import date

st.set_page_config(page_title="Łucznik - Karta Punktowa", layout="centered")

# --- INICJALIZACJA ZMIENNYCH ---
if 'started' not in st.session_state:
    st.session_state.started = False
if 'scores' not in st.session_state:
    st.session_state.scores = []
# Zmienna pilnująca naszego sprytnego przycisku Radio
if 'radio_input' not in st.session_state:
    st.session_state.radio_input = None

def add_score(val):
    if len(st.session_state.scores) < st.session_state.max_total_arrows:
        st.session_state.scores.append(val)

def undo_score():
    if len(st.session_state.scores) > 0:
        st.session_state.scores.pop()

def reset():
    st.session_state.started = False
    st.session_state.scores = []
    st.session_state.radio_input = None

# --- TWOJA GENIALNA FUNKCJA RESETUJĄCA ---
def handle_radio_click():
    # Pobieramy to, co właśnie kliknąłeś
    val = st.session_state.radio_input
    if val is not None:
        add_score(val) # Zapisujemy do tabeli
        st.session_state.radio_input = None # Natychmiast "odklikujemy" przycisk!

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
    st.markdown(f"**Strzały:** {len(scores)}/{st.session_state.max_total_arrows} &nbsp;&nbsp;|&nbsp;&nbsp; **Punkty:** {total_points}/{max_total_score} ({percent:.0f}%)")
    st.divider()

    # --- TWOJA NOWA, SZYBKA KLAWIATURA ---
    st.write("Wybierz trafienie (zapisuje się automatycznie):")
    
    # Przycisk Radio podłączony do funkcji czyszczącej
    st.radio(
        "Punkty",
        options=["X", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "M"],
        horizontal=True,
        index=None, # Na starcie nic nie jest zaznaczone
        key="radio_input", # Połączenie ze zmienną
        on_change=handle_radio_click, # Funkcja wywoływana OD RAZU po kliknięciu
        label_visibility="collapsed"
    )
    
    st.write("") # Drobny odstęp
    st.button("⌫ Cofnij ostatnią strzałę", on_click=undo_score, use_container_width=True)

    st.divider()

    # --- KOLOROWA TABELA HTML ---
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

    if st.button("Zakończ strzelanie (Wkrótce Google Sheets)", type="primary", use_container_width=True):
        reset()
        st.rerun()
