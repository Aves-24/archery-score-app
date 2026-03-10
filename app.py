import streamlit as st
import pandas as pd
from datetime import date

# Konfiguracja strony pod smartfony (wyśrodkowana)
st.set_page_config(page_title="Łucznictwo Recurve - Punktacja", layout="centered")

# --- INICJALIZACJA ZMIENNYCH ---
# Streamlit odświeża stronę przy każdym kliknięciu, dlatego musimy "zapamiętać" stan
if 'started' not in st.session_state:
    st.session_state.started = False
if 'scores' not in st.session_state:
    st.session_state.scores = []
if 'max_arrows' not in st.session_state:
    st.session_state.max_arrows = 36
if 'arrows_per_end' not in st.session_state:
    st.session_state.arrows_per_end = 6

def start_session():
    st.session_state.started = True
    st.session_state.scores = []

def add_score(val):
    if len(st.session_state.scores) < st.session_state.max_arrows:
        st.session_state.scores.append(val)

def undo_score():
    if len(st.session_state.scores) > 0:
        st.session_state.scores.pop()

def reset():
    st.session_state.started = False
    st.session_state.scores = []

# --- EKRAN STARTOWY (KONFIGURACJA) ---
if not st.session_state.started:
    st.title("🏹 Dziennik Strzelań")
    
    event_type = st.radio("Rodzaj strzelania:", ["Trening", "Turniej"], horizontal=True)
    
    event_name = ""
    if event_type == "Turniej":
        event_name = st.text_input("Nazwa turnieju:")
        
    distance = st.selectbox("Odległość i Tarcza:", [
        "18m - Tarcza Spot (Trójak)", 
        "30m - Tarcza 80cm", 
        "70m - Tarcza 120cm"
    ])
    
    arrows_per_end = st.radio("Ilość strzał w rundzie (serii):", [3, 6], index=1, horizontal=True)
    rounds = st.number_input("Ilość rund:", min_value=1, max_value=20, value=6)
    
    if st.button("Rozpocznij strzelanie", type="primary", use_container_width=True):
        # Zapisanie ustawień na czas trwania sesji
        st.session_state.max_arrows = arrows_per_end * rounds
        st.session_state.arrows_per_end = arrows_per_end
        st.session_state.event_info = {
            "Data": date.today().strftime("%d.%m.%Y"),
            "Typ": event_type,
            "Nazwa": event_name if event_type == "Turniej" else "-",
            "Dystans": distance,
            "Rundy": rounds
        }
        start_session()
        st.rerun()

# --- EKRAN TARCZY (PUNKTACJA) ---
else:
    info = st.session_state.event_info
    
    # Nagłówek informacji
    st.write(f"**{info['Typ']}** {('- ' + info['Nazwa']) if info['Nazwa'] != '-' else ''} | **Data:** {info['Data']}")
    st.write(f"**Dystans:** {info['Dystans']}")
    
    st.divider()
    
    # Panel wprowadzania punktów
    st.subheader("Wprowadź punkty:")
    
    # Układ przycisków
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.button("X", on_click=add_score, args=("X",), use_container_width=True)
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
        columns = [f"Strz. {j+1}" for j in range(arrows_per_end)] + ["Wynik rundy", "Suma"]
        df = pd.DataFrame(table_data, columns=columns)
        df.index += 1 # Rundy od 1, nie od 0
        st.table(df)
        
    # Szybkie statystyki
    col_a, col_b = st.columns(2)
    col_a.metric(label="Całkowity Wynik", value=total_score)
    col_b.metric(label="Oddane strzały", value=f"{len(scores)} / {st.session_state.max_arrows}")
    
    if st.button("Zakończ i wróć do menu", type="secondary"):
        reset()
        st.rerun()
