import streamlit as st
from datetime import date

st.set_page_config(page_title="Łucznik - Karta Punktowa", layout="centered")

# --- LISTA DYSTANSÓW ---
dystanse_lista = ["18m", "30m", "70m"]

# --- INICJALIZACJA ZMIENNYCH ---
if 'started' not in st.session_state:
    st.session_state.started = False
if 'scores' not in st.session_state:
    st.session_state.scores = []

# Domyślne wartości celownika
if f"dz_{dystanse_lista[0]}" not in st.session_state:
    st.session_state[f"dz_{dystanse_lista[0]}"] = "11"  
    st.session_state[f"sk_{dystanse_lista[0]}"] = "0.7" 
    
    st.session_state[f"dz_{dystanse_lista[1]}"] = ""    
    st.session_state[f"sk_{dystanse_lista[1]}"] = ""    
    
    st.session_state[f"dz_{dystanse_lista[2]}"] = "11"  
    st.session_state[f"sk_{dystanse_lista[2]}"] = "8"   

def add_score(val):
    if len(st.session_state.scores) < st.session_state.max_total_arrows:
        st.session_state.scores.append(val)

def undo_score():
    if len(st.session_state.scores) > 0:
        st.session_state.scores.pop()

def reset():
    st.session_state.started = False
    st.session_state.scores = []
    if 'radio_input' in st.session_state:
        del st.session_state['radio_input']

def handle_radio_click():
    if 'radio_input' in st.session_state:
        val = st.session_state.radio_input
        if val == "⌫":
            undo_score() 
        elif val is not None:
            add_score(val) 
        st.session_state.radio_input = None 

# --- EKRAN STARTOWY ---
if not st.session_state.started:
    
    st.markdown("""
    <div style='background-color: #2E8B57; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <h2 style='color: white; margin: 0; font-size: 26px; font-weight: bold;'>🏹 Karta Punktowa</h2>
    </div>
    """, unsafe_allow_html=True)
    
    event_type = st.radio("typ_wydarzenia", ["Trening", "Turniej"], horizontal=True, label_visibility="collapsed")
    
    event_name = "-"
    if event_type == "Turniej":
        event_name = st.text_input("Nazwa turnieju:", placeholder="np. Mistrzostwa Klubu")
        
    st.write("") 
    
    st.write("🎯 **Wybierz dystans:**")
    dystans = st.radio("Dystans", dystanse_lista, horizontal=True, label_visibility="collapsed")

    arrows_per_end = 6
    ends_per_round = 6

    base_info = {
        "Data": date.today().strftime("%d.%m.%Y"),
        "Typ": event_type,
        "Nazwa": event_name if event_name.strip() else "-",
        "StrzalWSerii": arrows_per_end,
        "SeriiWRundzie": ends_per_round,
        "Dystans": dystans
    }

    st.write("")
    
    if st.button("🚀 ROZPOCZNIJ STRZELANIE", type="primary", use_container_width=True):
        base_info["CelownikDziurka"] = st.session_state[f"dz_{dystans}"].strip() if st.session_state[f"dz_{dystans}"].strip() else "-"
        base_info["CelownikSkala"] = st.session_state[f"sk_{dystans}"].strip() if st.session_state[f"sk_{dystans}"].strip() else "-"
        
        st.session_state.event_info = base_info
        st.session_state.max_arrows_per_round = arrows_per_end * ends_per_round
        st.session_state.max_total_arrows = st.session_state.max_arrows_per_round * 2
        st.session_state.started = True
        st.rerun()

    st.divider()

    with st.expander("⚙️ Ustawienia wizjera (Zmieniaj rzadko)", expanded=False):
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.markdown("<span style='font-size:12px; color:gray;'>Dystans</span>", unsafe_allow_html=True)
        c2.markdown("<span style='font-size:12px; color:gray;'>Dziurka</span>", unsafe_allow_html=True)
        c3.markdown("<span style='font-size:12px; color:gray;'>Skala</span>", unsafe_allow_html=True)
        
        for d in dystanse_lista:
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.markdown(f"<div style='margin-top: 8px; font-weight: bold;'>{d}</div>", unsafe_allow_html=True)
            st.text_input(f"Dz {d}", key=f"dz_{d}", label_visibility="collapsed")
            st.text_input(f"Sk {d}", key=f"sk_{d}", label_visibility="collapsed")

# --- EKRAN TARCZY (PUNKTACJA) ---
else:
    # --- CSS: POWIĘKSZENIE RADIO BUTTONÓW ---
    st.markdown("""
    <style>
        /* Powiększenie odstępów między elementami Radio */
        div[data-testid="stRadio"] > div {
            gap: 15px !important;
            padding: 10px 0 !important;
        }
        
        /* Zwiększenie obszaru klikalnego i czcionki (X, 10, 9...) */
        div[data-testid="stRadio"] label [data-testid="stMarkdownContainer"] p {
            font-size: 22px !important;
            font-weight: 900 !important;
            padding: 10px 5px !important; /* To robi duży ukryty "guzik" pod palcem */
        }
        
        /* Opcjonalne powiększenie samej fizycznej kropki (zadziała w większości przeglądarek) */
        div[data-testid="stRadio"] label span:first-of-type {
            transform: scale(1.4) !important;
            margin-right: 8px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    info = st.session_state.event_info
    scores = st.session_state.scores
    arrows_per_end = info['StrzalWSerii']
    max_round_score = st.session_state.max_arrows_per_round * 10
    max_total_score = st.session_state.max_total_arrows * 10
    
    def get_num(s): return 10 if s in ["X", "10"] else (0 if s == "M" else int(s))
    
    tytul = f"{info['Typ']}" + (f" - {info['Nazwa']}" if info['Nazwa'] != "-" else "")
    celownik_tekst = ""
    if info['CelownikDziurka'] != "-" or info['CelownikSkala'] != "-":
        celownik_tekst = f" | ⚙️ Dz: {info['CelownikDziurka']} Sk: {info['CelownikSkala']}"
        
    st.markdown(f"<div style='text-align: center; color: gray; font-size: 14px; margin-bottom: 10px;'>{tytul} | {info['Data']} | {info['Dystans']}{celownik_tekst}</div>", unsafe_allow_html=True)

    st.write("Wybierz trafienie:")
    
    st.radio(
        "Punkty",
        options=["X", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "M", "⌫"], 
        horizontal=True,
        index=None, 
        key="radio_input", 
        on_change=handle_radio_click, 
        label_visibility="collapsed"
    )

    st.divider()

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
        r_hits = len([s for s in round_scores if s != "M"])
        r_10s = round_scores.count("10") + round_scores.count("X") 
        r_xs = round_scores.count("X")
        r_max_current = len(round_scores) * 10
        r_percent = (r_points / r_max_current * 100) if r_max_current > 0 else 0
        
        html = f"<div style='margin-bottom: 20px; font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
        html += f"<div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 5px;'><b>Runda {round_num}</b><span style='font-weight: bold;'>{info['Dystans']}</span></div>"
        html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black;'>"
        html += f"<tr style='background-color: #f2f2f2; color: #000000; border-bottom: 1px solid black;'><th rowspan='2' style='border: 1px solid black; border-right: 2px solid black; padding: 2px; width: 30px;'></th><th colspan='{arrows_per_end}' style='border: 1px solid black; padding: 2px; font-size: 14px;'>Pfeile</th><th colspan='2' style='border: 1px solid black; border-left: 2px solid black; padding: 2px; font-size: 14px;'>Summen</th></tr>"
        html += f"<tr style='background-color: #f2f2f2; color: #000000; border-bottom: 2px solid black;'>"
        
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
                    html += "<td style='padding: 2px; border: 1px solid black;'></td>"
            
            html += f"<td style='border: 1px solid black; border-left: 2px solid black; padding: 4px; font-weight: bold;'>{end_sum}</td>"
            html += f"<td style='border: 1px solid black; padding: 4px; font-weight: bold;'>{cumul_total if len(end_scores)>0 else ''}</td>"
            html += "</tr>"
            
        html += f"<tr style='border-top: 2px solid black; background-color: #f9f9f9; color: #000;'><td colspan='{arrows_per_end + 1}' style='text-align: right; padding: 5px; font-weight: bold; border: 1px solid black; border-right: 2px solid black;'>Summe:</td><td colspan='2' style='border: 2px solid black; font-weight: bold; font-size: 16px; padding: 5px;'>{r_points}</td></tr></table>"
        
        html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black; border-top: none; color: #000;'><tr><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>Treffer:<br><b style='font-size: 14px;'>{r_hits}</b></td><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>10er:<br><b style='font-size: 14px;'>{r_10s}</b></td><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>Xer:<br><b style='font-size: 14px;'>{r_xs}</b></td><td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; text-align: left;'>Kontr.<br>&nbsp;</td></tr></table></div>"
        
        return html, cumul_total

    round1_scores = scores[:st.session_state.max_arrows_per_round]
    round2_scores = scores[st.session_state.max_arrows_per_round:]

    if len(round2_scores) == 0:
        if len(round1_scores) > 0 or not st.session_state.started:
            html1, cumul1 = render_round_html(1, round1_scores, 0)
            st.markdown(html1, unsafe_allow_html=True)
    else:
        html1, cumul1 = render_round_html(1, round1_scores, 0)
        with st.expander("✅ Runda 1 (Zakończona - kliknij, aby rozwinąć)", expanded=False):
            st.markdown(html1, unsafe_allow_html=True)
        
        html2, _ = render_round_html(2, round2_scores, cumul1)
        st.markdown(html2, unsafe_allow_html=True)

    # --- STATYSTYKI KOŃCOWE ---
    total_points = sum(get_num(s) for s in scores)
    percent = (total_points / (len(scores) * 10) * 100) if len(scores) > 0 else 0
    count_x = scores.count("X")
    count_10 = scores.count("10")
    
    st.markdown("### 📊 Wynik Całkowity (Mecz)")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Punkty", f"{total_points} / {max_total_score}")
    col_s2.metric("Strzały", f"{len(scores)} / {st.session_state.max_total_arrows}")
    col_s3.metric("Skuteczność", f"{percent:.1f}%")
    
    st.write(f"**Suma 10+X:** {count_10 + count_x} &nbsp;&nbsp;|&nbsp;&nbsp; **Same X:** {count_x}")
    st.write("")

    if st.button("Zakończ strzelanie (Wkrótce Google Sheets)", type="primary", use_container_width=True):
        reset()
        st.rerun()
