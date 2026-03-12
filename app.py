import streamlit as st
from datetime import date

st.set_page_config(page_title="Łucznik - Karta Punktowa", layout="centered")

# --- INICJALIZACJA ZMIENNYCH ---
if 'started' not in st.session_state:
    st.session_state.started = False
if 'scores' not in st.session_state:
    st.session_state.scores = []
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

def handle_radio_click():
    val = st.session_state.radio_input
    if val is not None:
        add_score(val)
        st.session_state.radio_input = None

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

    st.markdown(f"### {info['Typ']} ({info['Data']})")
    st.markdown(f"**Strzały:** {len(scores)}/{st.session_state.max_total_arrows} &nbsp;&nbsp;|&nbsp;&nbsp; **Punkty:** {total_points}/{max_total_score} ({percent:.0f}%)")
    st.divider()

    st.write("Wybierz trafienie (zapisuje się automatycznie):")
    
    st.radio(
        "Punkty",
        options=["X", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "M"],
        horizontal=True,
        index=None, 
        key="radio_input", 
        on_change=handle_radio_click, 
        label_visibility="collapsed"
    )
    
    st.write("") 
    st.button("⌫ Cofnij ostatnią strzałę", on_click=undo_score, use_container_width=True)

    st.divider()

    def get_color_style(val):
        if val in ["X", "10", "9"]: return "background-color: #FCE205; color: black;"
        if val in ["8", "7"]: return "background-color: #E53935; color: white;"
        if val in ["6", "5"]: return "background-color: #039BE5; color: white;"
        if val in ["4", "3"]: return "background-color: #212121; color: white;"
        if val in ["2", "1"]: return "background-color: #ffffff; color: black;"
        if val == "M": return "background-color: #9e9e9e; color: white;"
        return "background-color: transparent;"

    # --- PŁASKI HTML BEZ WCIĘĆ (Gwarancja rysowania tabeli) ---
    def render_round_html(round_num, round_scores, cumulative_start):
        r_points = sum(get_num(s) for s in round_scores)
        r_hits = len([s for s in round_scores if s != "M"])
        r_10s = round_scores.count("10") + round_scores.count("X") 
        r_xs = round_scores.count("X")
        
        html = f"<div style='margin-bottom: 25px; font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
        html += f"<div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 5px;'><b>Runda {round_num}</b><span style='font-weight: bold;'>{info['Dystans']}</span></div>"
        html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black;'>"
        html += f"<tr style='border-bottom: 1px solid black;'><th rowspan='2' style='border: 1px solid black; border-right: 2px solid black; padding: 2px; width: 30px;'></th><th colspan='{arrows_per_end}' style='border: 1px solid black; padding: 2px; font-size: 14px;'>Pfeile</th><th colspan='2' style='border: 1px solid black; border-left: 2px solid black; padding: 2px; font-size: 14px;'>Summen</th></tr>"
        html += f"<tr style='border-bottom: 2px solid black;'>"
        
        for arr in range(1, arrows_per_end + 1):
            html += f"<th style='border: 1px solid black; padding: 2px; width: 30px; font-size: 12px;'>{arr}</th>"
            
        html += f"<th style='border: 1px solid black; border-left: 2px solid black; padding: 2px; font-size: 12px;'>Seria</th><th style='border: 1px solid black; padding: 2px; font-size: 12px;'>Übertrag</th></tr>"
        
        cumul_total = cumulative_start
        expected_ends = info['SeriiWRundzie']
        
        for end_idx in range(expected_ends):
            arrow_idx_start = end_idx * arrows_per_end
            end_scores = round_scores[arrow_idx_start:arrow_idx_start + arrows_per_end]
            
            if len(end_scores) > 0:
                end_sum = sum(get_num(s) for s in end_scores)
                cumul_total += end_sum
            else:
                end_sum = ""
                
            arrow_label = (end_idx + 1) * arrows_per_end
            
            html += "<tr>"
            html += f"<td style='border: 1px solid black; border-right: 2px solid black; padding: 4px; font-weight: bold; font-size: 14px;'>{arrow_label}</td>"
            
            for j in range(arrows_per_end):
                if j < len(end_scores):
                    val = end_scores[j]
                    style = get_color_style(val)
                    circle = f"<div style='width: 22px; height: 22px; border-radius: 50%; {style} display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; margin: 0 auto; border: 1px solid #aaa;'>{val}</div>"
                    html += f"<td style='border: 1px solid black; padding: 2px;'>{circle}</td>"
                else:
                    html += "<td style='border: 1px solid black; padding: 2px;'></td>"
            
            html += f"<td style='border: 1px solid black; border-left: 2px solid black; padding: 4px; font-weight: bold;'>{end_sum}</td>"
            html += f"<td style='border: 1px solid black; padding: 4px; font-weight: bold;'>{cumul_total if len(end_scores)>0 else ''}</td>"
            html += "</tr>"
            
        html += f"<tr style='border-top: 2px solid black; background-color: #f9f9f9;'><td colspan='{arrows_per_end + 1}' style='text-align: right; padding: 5px; font-weight: bold; border: 1px solid black; border-right: 2px solid black;'>Summe:</td><td colspan='2' style='border: 2px solid black; font-weight: bold; font-size: 16px; padding: 5px;'>{r_points}</td></tr></table>"
        
        html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black; border-top: none;'><tr><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>Treffer:<br><b style='font-size: 14px;'>{r_hits}</b></td><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>10er:<br><b style='font-size: 14px;'>{r_10s}</b></td><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>Xer:<br><b style='font-size: 14px;'>{r_xs}</b></td><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>Kontr.<br>&nbsp;</td></tr></table></div>"
        
        return html, cumul_total

    round1_scores = scores[:st.session_state.max_arrows_per_round]
    round2_scores = scores[st.session_state.max_arrows_per_round:]

    if len(round1_scores) > 0 or not st.session_state.started:
        html1, cumul1 = render_round_html(1, round1_scores, 0)
        st.markdown(html1, unsafe_allow_html=True)
        
    if len(round2_scores) > 0:
        html2, _ = render_round_html(2, round2_scores, cumul1)
        st.markdown(html2, unsafe_allow_html=True)

    if st.button("Zakończ strzelanie (Wkrótce Google Sheets)", type="primary", use_container_width=True):
        reset()
        st.rerun()
