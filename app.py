import streamlit as st
import pandas as pd
from datetime import date

# Konfiguracja strony pod smartfony
st.set_page_config(page_title="Łucznik - Licznik", layout="centered")

# --- CUSTOM CSS (Dla lepszego wyglądu przycisków graficznych) ---
st.markdown("""
<style>
    div.stButton > button:first-child {
        height: 100px;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        background-color: white;
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:first-child:hover {
        border-color: #ff4b4b;
        background-color: #fff5f5;
        transform: scale(1.02);
    }
    div.stButton > button:first-child:active {
        background-color: #ffe0e0;
    }
    /* Styl dla mniejszych przycisków punktacji */
    .stDataFrame div[data-testid="stTable"] {
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- INICJALIZACJA ZMIENNYCH SESJI ---
if 'started' not in st.session_state:
    st.session_state.started = False
if 'scores' not in st.session_state:
    st.session_state.scores = []
if 'max_arrows' not in st.session_state:
    st.session_state.max_arrows = 36
if 'arrows_per_end' not in st.session_state:
    st.session_state.arrows_per_end = 6
if 'event_info' not in st.session_state:
    st.session_state.event_info = {}

def add_score(val):
    if len(st.session_state.scores) < st.session_state.max_arrows:
        st.session_state.scores.append(val)

def undo_score():
    if len(st.session_state.scores) > 0:
        st.session_state.scores.pop()

def reset():
    st.session_state.started = False
    st.session_state.scores = []

# --- EKRAN STARTOWY (GRAFICZNA KONFIGURACJA) ---
if not st.session_state.started:
    st.title("🏹 Dziennik Łucznika")
    
    st.subheader("1. Ustawienia ogólne")
    event_type = st.radio("Rodzaj strzelania:", ["Trening", "Turniej"], horizontal=True)
    
    event_name = ""
    if event_type == "Turniej":
        event_name = st.text_input("Nazwa turnieju:", placeholder="np. Mistrzostwa Polski")
        
    arrows_per_end = st.radio("Strzał w rundzie (serii):", [3, 6], index=1, horizontal=True)
    rounds = st.number_input("Ilość rund:", min_value=1, max_value=20, value=6)
    
    st.divider()
    st.subheader("2. Wybierz Dystans i Tarczę (Kliknij tarczę, aby zacząć)")

    # Przygotowanie danych do zapisu
    max_arrows = arrows_per_end * rounds
    base_info = {
        "Data": date.today().strftime("%d.%m.%Y"),
        "Typ": event_type,
        "Nazwa": event_name if event_type == "Turniej" else "-",
        "Rundy": rounds,
        "StrzalWRundzie": arrows_per_end
    }

    # --- Układ Graficzny ---
    col1, col2, col3 = st.columns(3)

    with col1:
        # Reprezentacja 18m Spot (3 tarcze w pionie)
        st.markdown("<h3 style='text-align: center;'>18m</h3>", unsafe_allow_html=True)
        # Używamy emoji tarczy 🎯
        html_target_18 = "<div style='text-align: center; font-size: 30px;'>🎯<br>🎯<br>🎯</div>"
        st.markdown(html_target_18, unsafe_allow_html=True)
        if st.button("Spot (Trójak)", key="btn_18m", use_container_width=True):
            if event_type == "Turniej" and not event_name:
                st.error("Wpisz nazwę turnieju!")
            else:
                st.session_state.event_info = base_info
                st.session_state.event_info["Dystans"] = "18m (Trójak)"
                st.session_state.max_arrows = max_arrows
                st.session_state.arrows_per_end = arrows_per_end
                st.session_state.started = True
                st.rerun()

    with col2:
        # Reprezentacja 30m / 80cm
        st.markdown("<h3 style='text-align: center;'>30m</h3>", unsafe_allow_html=True)
        # Jedna, większa tarcza
        html_target_30 = "<div style='text-align: center; font-size: 60px; margin: 15px 0;'>🎯</div>"
        st.markdown(html_target_30, unsafe_allow_html=True)
        if st.button("Tarcza 80cm", key="btn_30m", use_container_width=True):
            if event_type == "Turniej" and not event_name:
                st.error("Wpisz nazwę turnieju!")
            else:
                st.session_state.event_info = base_info
                st.session_state.event_info["Dystans"] = "30m (80cm)"
                st.session_state.max_arrows = max_arrows
                st.session_state.arrows_per_end = arrows_per_end
                st.session_state.started = True
                st.rerun()

    with col3:
        # Reprezentacja 70m / 120cm
        st.markdown("<h3 style='text-align: center;'>70m</h3>", unsafe_allow_html=True)
        # Jedna, duża tarcza (wielkość emoji taka sama, ale opis inny)
        html_target_70 = "<div style='text-align: center; font-size: 60px; margin: 15px 0;'>🎯</div>"
        st.markdown(html_target_70, unsafe_allow_html=True)
        if st.button("Tarcza 120cm", key="btn_70m", use_container_width=True):
            if event_type == "Turniej" and not event_name:
                st.error("Wpisz nazwę turnieju!")
            else:
                st.session_state.event_info = base_info
                st.session_state.event_info["Dystans"] = "70m (120cm)"
                st.session_state.max_arrows = max_arrows
                st.session_state.arrows_per_end = arrows_per_end
                st.session_state.started = True
                st.rerun()

# --- EKRAN TARCZY (PUNKTACJA) - Bez zmian w logice, dodano tylko CSS ---
else:
    info = st.session_state.event_info
    
    # Nagłówek informacji
    st.write(f"**{info['Typ']}** {('- ' + info['Nazwa']) if info['Nazwa'] != '-' else ''}")
    st.write(f"**Dystans:** {info['Dystans']} | **Data:** {info['Data']}")
    
    st.divider()
    
    # Panel wprowadzania punktów
    st.subheader("Wprowadź punkty:")
    
    # Układ przycisków (X, 10, 9, 8, 7...)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.button("X", on_click=add_score, args=("X",), use_container_width=True, type="primary")
    with col2: st.button("10", on_click=add_score, args=("10",), use_container_width=True)
    with col3: st.button("9", on_click=add_score, args=("9",), use_container_width=True)
    with col4: st.button("8", on_click=add_score, args=("8",), use_container_width=True)
    with col5: st.button("7", on_click=add_score, args=("7",), use_container_width=True)
    
    col6, col7, col8, col9, col10 = st.columns(5)
    with col6: st.button("6", on_click=add_score, args=("6",), use_container_width=True)
    with col7: st.button("5", on_click=add_score, args=("5",), use_container_width=True)
    with col8: st.button("4", on_click=add_score, args=("4",), use_container_width=True)
    with col9: st.button("3", on_click=add_score, args=("3",), use_container_width=True)
    with col10: st.button("2", on_click=add_score, args=("2",), use_container_width=True)
    
    col11, col12, col13 = st.columns([2, 1, 2])
    with col11: st.button("1", on_click=add_score, args=("1",), use_container_width=True)
    with col12: st.button("M", on_click=add_score, args=("M",), use_container_width=True)
    with col13: st.button("Cofnij ↩", on_click=undo_score, use_container_width=True)
    
    st.divider()
    
    # --- LOGIKA TABELI I PODSUMOWAŃ ---
    scores = st.session_state.scores
    arrows_per_end = st.session_state.arrows_per_end
    
    def get_num_value(s):
        if s == "X": return 10
        if s == "M": return 0
        return int(s)
    
    table_data = []
    total_score = 0
    
    # Grupowanie w rundy
    for i in range(0, len(scores), arrows_per_end):
        end_scores = scores[i:i+arrows_per_end]
        end_values = [get_num_value(s) for s in end_scores]
        end_sum = sum(end_values)
        total_score += end_sum
        
        # Wypełnianie pustych miejsc w bieżącej serii
        row = end_scores + [""] * (arrows_per_end - len(end_scores))
        row.append(end_sum)
        row.append(total_score)
        table_data.append(row)
        
    if table_data:
        columns = [f"S{j+1}" for j in range(arrows_per_end)] + ["Runda", "Suma"]
        df = pd.DataFrame(table_data, columns=columns)
        df.index += 1 # Rundy od 1
        st.table(df)
        
    # Szybkie statystyki
    col_a, col_b = st.columns(2)
    col_a.metric(label="Całkowity Wynik", value=total_score)
    col_b.metric(label="Strzały", value=f"{len(scores)} / {st.session_state.max_arrows}")
    
    if st.button("Zakończ strzelanie", type="secondary", use_container_width=True):
        reset()
        st.rerun()
