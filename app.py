import streamlit as st
import json
import os
import time
from datetime import datetime, date
import gspread
import pandas as pd
import altair as alt

st.set_page_config(page_title="Łucznik - Karta Punktowa", layout="centered")

# --- KONFIGURACJA GŁÓWNA ---
NAZWA_ARKUSZA = "Karta_Punktowa"
ADRES_APLIKACJI = "https://twoja-aplikacja.streamlit.app" # <-- Wpisz tu prawdziwy link do swojej apki!

# Baza zawodników (Zmień imiona i PIN-y)
ZAWODNICY = {
    "Rafael": "1234",
    "Tomek": "0000"
}

# --- PLIKI ZAPISU ---
AUTOSAVE_FILE = "autosave.json"
SETTINGS_FILE = "settings.json"

# --- SŁOWNIK JĘZYKOWY (PL / DE) ---
T = {
    "PL": {
        "title": "🏹 Karta Punktowa",
        "tab_score": "Karta Punktowa",
        "tab_stats": "Statystyki",
        "training": "Trening",
        "tournament": "Turniej",
        "event_name": "Nazwa turnieju:",
        "event_name_ph": "np. Mistrzostwa Klubu",
        "choose_dist": "🎯 **Wybierz dystans:**",
        "start_btn": "🚀 ROZPOCZNIJ STRZELANIE",
        "settings_exp": "⚙️ Ustawienia (Wizjer, Język, Wyloguj)",
        "lang_label": "Wybierz język / Sprache:",
        "dist": "Dystans",
        "hole": "Dziurka",
        "scale": "Skala",
        "total_score": "### 📊 Wynik Całkowity (Mecz)",
        "pts": "Punkty",
        "arrow_cnt": "Licznik strzał",
        "eff": "Skuteczność",
        "warmup": "Strzały próbne / rozgrzewka:",
        "add_6": "➕ 6 strzał",
        "add_1": "➕ 1 strzała",
        "undo": "➖ Cofnij",
        "finish": "💾 Zakończ i Zapisz w Google Sheets",
        "sum_10_x": "Suma 10+X:",
        "only_x": "Same X:",
        "round_fin": "✅ Runda 1 (Zakończona - kliknij, aby rozwinąć)",
        "stat_no_data": "Brak danych dla tego dystansu. Idź postrzelać! 🏹",
        "stat_metric": "Pokaż na wykresie:"
    },
    "DE": {
        "title": "🏹 Schießzettel",
        "tab_score": "Schießzettel",
        "tab_stats": "Statistiken",
        "training": "Training",
        "tournament": "Turnier",
        "event_name": "Turniername:",
        "event_name_ph": "z.B. Vereinsmeisterschaft",
        "choose_dist": "🎯 **Wähle Distanz:**",
        "start_btn": "🚀 SCHIESSEN STARTEN",
        "settings_exp": "⚙️ Einstellungen (Visier, Sprache, Logout)",
        "lang_label": "Sprache / Wybierz język:",
        "dist": "Distanz",
        "hole": "Loch",
        "scale": "Skala",
        "total_score": "### 📊 Gesamtergebnis (Match)",
        "pts": "Punkte",
        "arrow_cnt": "Pfeilzähler",
        "eff": "Trefferquote",
        "warmup": "Probepfeile / Aufwärmen:",
        "add_6": "➕ 6 Pfeile",
        "add_1": "➕ 1 Pfeil",
        "undo": "➖ Rückgängig",
        "finish": "💾 Beenden & in Google Sheets speichern",
        "sum_10_x": "Summe 10+X:",
        "only_x": "Nur X:",
        "round_fin": "✅ Runde 1 (Beendet - zum Aufklappen klicken)",
        "stat_no_data": "Keine Daten für diese Distanz. Geh schießen! 🏹",
        "stat_metric": "Zeige im Diagramm:"
    }
}

# --- FUNKCJE USTAWIEŃ, ZAPISU I LOGOWANIA ---
def load_settings():
    lang = "PL"
    zawodnik = None
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                lang = data.get("lang", "PL")
                zawodnik = data.get("zalogowany_zawodnik")
        except: pass
    return lang, zawodnik

def save_settings():
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "lang": st.session_state.lang, 
            "zalogowany_zawodnik": st.session_state.zalogowany_zawodnik
        }, f)

start_lang, start_zawodnik = load_settings()
if 'lang' not in st.session_state:
    st.session_state.lang = start_lang
if 'zalogowany_zawodnik' not in st.session_state:
    st.session_state.zalogowany_zawodnik = start_zawodnik

lang = st.session_state.lang

def wyloguj():
    st.session_state.zalogowany_zawodnik = None
    save_settings()
    st.rerun()

# --- EKRAN LOGOWANIA ---
if not st.session_state.zalogowany_zawodnik:
    st.markdown(f"""
    <div style='background-color: #2E8B57; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center;'>
        <h2 style='color: white; margin: 0;'>🏹 Logowanie Łucznika</h2>
    </div>
    """, unsafe_allow_html=True)
    
    wybrany_zawodnik = st.selectbox("Wybierz swoje imię:", list(ZAWODNICY.keys()))
    podany_pin = st.text_input("Podaj 4-cyfrowy PIN:", type="password")
    
    if st.button("Wejdź na strzelnicę", type="primary", use_container_width=True):
        if ZAWODNICY.get(wybrany_zawodnik) == podany_pin:
            st.session_state.zalogowany_zawodnik = wybrany_zawodnik
            save_settings() 
            st.success(f"Witaj, {wybrany_zawodnik}!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("❌ Błędny PIN! Spróbuj ponownie.")
    st.stop() 

# --- POBIERANIE DANYCH Z GOOGLE ---
@st.cache_data(ttl=15)
def pobierz_dane_z_arkusza(zawodnik):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        creds_dict = json.loads(klucz_tekst)
        gc = gspread.service_account_from_dict(creds_dict)
        sh = gc.open(NAZWA_ARKUSZA)
        
        # Próbuje otworzyć zakładkę konkretnego zawodnika
        try:
            worksheet = sh.worksheet(zawodnik)
        except:
            return pd.DataFrame() # Jeśli zakładka jeszcze nie istnieje, zwraca pustą tabelę
            
        zapisy = worksheet.get_all_records()
        
        if zapisy:
            df = pd.DataFrame(zapisy)
            df.columns = df.columns.astype(str).str.strip()
            
            kolumny_liczbowe = ["Punkty", "Same X", "10", "9", "M", "Strzały (Suma)"]
            for col in kolumny_liczbowe:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                else:
                    df[col] = 0
            
            if "Typ" in df.columns:
                df["Typ"] = df["Typ"].astype(str).str.strip()
                
            return df
        return pd.DataFrame()
    except Exception as e:
        print(f"Błąd odczytu: {e}")
        return pd.DataFrame()

# --- ZAPIS DO GOOGLE SHEETS ---
def zapisz_do_arkusza(dane_treningu, statystyki):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        creds_dict = json.loads(klucz_tekst)
        gc = gspread.service_account_from_dict(creds_dict)
        sh = gc.open(NAZWA_ARKUSZA)
        
        zawodnik = st.session_state.zalogowany_zawodnik
        
        # INTELIGENTNE TWORZENIE ZAKŁADEK!
        try:
            worksheet = sh.worksheet(zawodnik)
        except:
            # Jeśli zakładka nie istnieje, robot sam ją stworzy i doda nagłówki!
            worksheet = sh.add_worksheet(title=zawodnik, rows="100", cols="20")
            naglowki = ["Data", "Czas", "Typ", "Nazwa", "Dystans", "Punkty", "Max", "Skuteczność %", "Strzały (Suma)", "10+X", "Same X", "Wizjer Dziurka", "Wizjer Skala", "10", "9", "M"]
            worksheet.append_row(naglowki)
            
        now = datetime.now()
        wiersz = [
            dane_treningu["Data"],
            now.strftime("%H:%M:%S"),
            dane_treningu["Typ"],
            dane_treningu["Nazwa"],
            dane_treningu["Dystans"],
            statystyki["Punkty"],
            statystyki["Max"],
            f"{statystyki['Skuteczność']:.1f}%",
            statystyki["Strzały"],
            statystyki["10_i_X"],
            statystyki["X"],
            dane_treningu["CelownikDziurka"],
            dane_treningu["CelownikSkala"],
            statystyki["10"], 
            statystyki["9"],  
            statystyki["M"]
        ]
        
        worksheet.append_row(wiersz)
        st.cache_data.clear()
        return True
    except Exception as e:
        return False

# --- SYSTEM AUTO-SAVE ---
def save_backup():
    if st.session_state.get('started'):
        backup_data = {
            "started": True,
            "scores": st.session_state.scores,
            "extra_arrows": st.session_state.extra_arrows,
            "event_info": st.session_state.event_info,
            "max_arrows_per_round": st.session_state.max_arrows_per_round,
            "max_total_arrows": st.session_state.max_total_arrows
        }
        with open(AUTOSAVE_FILE, "w") as f:
            json.dump(backup_data, f)

def load_backup():
    if os.path.exists(AUTOSAVE_FILE):
        try:
            with open(AUTOSAVE_FILE, "r") as f:
                data = json.load(f)
                if data.get("started"):
                    st.session_state.started = True
                    st.session_state.scores = data.get("scores", [])
                    st.session_state.extra_arrows = data.get("extra_arrows", 0)
                    st.session_state.event_info = data.get("event_info", {})
                    st.session_state.max_arrows_per_round = data.get("max_arrows_per_round", 36)
                    st.session_state.max_total_arrows = data.get("max_total_arrows", 72)
                    return True
        except: pass
    return False

def clear_backup():
    if os.path.exists(AUTOSAVE_FILE):
        os.remove(AUTOSAVE_FILE)

# --- INICJALIZACJA ZMIENNYCH ---
dystanse_lista = ["18m", "30m", "70m"]

if 'started' not in st.session_state:
    if not load_backup():
        st.session_state.started = False
        st.session_state.scores = []
        st.session_state.extra_arrows = 0

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
        save_backup()

def undo_score():
    if len(st.session_state.scores) > 0:
        st.session_state.scores.pop()
        save_backup()

def add_extra_arrows(val):
    if st.session_state.extra_arrows + val >= 0:
        st.session_state.extra_arrows += val
        save_backup()

def reset():
    clear_backup()
    st.session_state.started = False
    st.session_state.scores = []
    st.session_state.extra_arrows = 0
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

def zmiana_jezyka():
    st.session_state.lang = st.session_state.lang_sel
    save_settings()

# --- GŁÓWNY INTERFEJS (ZAKŁADKI) ---
st.markdown(f"<div style='text-align: right; color: gray; font-size: 12px; margin-bottom: 5px;'>👤 Zalogowany: <b>{st.session_state.zalogowany_zawodnik}</b></div>", unsafe_allow_html=True)
tab_karta, tab_staty = st.tabs([f"🎯 {T[lang]['tab_score']}", f"📊 {T[lang]['tab_stats']}"])

with tab_karta:
    if not st.session_state.started:
        st.markdown(f"""
        <div style='background-color: #2E8B57; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <h2 style='color: white; margin: 0; font-size: 26px; font-weight: bold;'>{T[lang]["title"]}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        event_type = st.radio("typ_wydarzenia", [T[lang]["training"], T[lang]["tournament"]], horizontal=True, label_visibility="collapsed")
        
        event_name = "-"
        if event_type == T[lang]["tournament"]:
            event_name = st.text_input(T[lang]["event_name"], placeholder=T[lang]["event_name_ph"])
            
        st.write("") 
        
        st.write(T[lang]["choose_dist"])
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
        
        if st.button(T[lang]["start_btn"], type="primary", use_container_width=True):
            base_info["CelownikDziurka"] = st.session_state[f"dz_{dystans}"].strip() if st.session_state[f"dz_{dystans}"].strip() else "-"
            base_info["CelownikSkala"] = st.session_state[f"sk_{dystans}"].strip() if st.session_state[f"sk_{dystans}"].strip() else "-"
            
            st.session_state.event_info = base_info
            st.session_state.max_arrows_per_round = arrows_per_end * ends_per_round
            st.session_state.max_total_arrows = st.session_state.max_arrows_per_round * 2
            st.session_state.started = True
            save_backup()
            st.rerun()

        st.divider()

        with st.expander(T[lang]["settings_exp"], expanded=False):
            st.write(f"**{T[lang]['lang_label']}**")
            st.radio("Język", ["PL", "DE"], index=0 if lang=="PL" else 1, horizontal=True, key="lang_sel", on_change=zmiana_jezyka, label_visibility="collapsed")
            
            st.write("")
            st.write(f"**{T[lang]['settings_exp'].split('(')[0]}**")
            
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.markdown(f"<span style='font-size:12px; color:gray;'>{T[lang]['dist']}</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='font-size:12px; color:gray;'>{T[lang]['hole']}</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='font-size:12px; color:gray;'>{T[lang]['scale']}</span>", unsafe_allow_html=True)
            
            for d in dystanse_lista:
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.markdown(f"<div style='margin-top: 8px; font-weight: bold;'>{d}</div>", unsafe_allow_html=True)
                st.text_input(f"Dz {d}", key=f"dz_{d}", label_visibility="collapsed")
                st.text_input(f"Sk {d}", key=f"sk_{d}", label_visibility="collapsed")
            
            st.write("")
            if st.button("🚪 Wyloguj / Logout", use_container_width=True):
                wyloguj()

    else:
        st.markdown("""
        <style>
            div[data-testid="stRadio"] { margin-bottom: -20px !important; }
            div[role="radiogroup"] { gap: 4px !important; padding: 0 !important; justify-content: center !important; }
            div[role="radiogroup"] label p { font-size: 18px !important; font-weight: 900 !important; padding: 0 !important; }
            div[role="radiogroup"] label:nth-child(1) p, div[role="radiogroup"] label:nth-child(2) p, div[role="radiogroup"] label:nth-child(3) p { color: #D4AC0D !important; }
            div[role="radiogroup"] label:nth-child(4) p, div[role="radiogroup"] label:nth-child(5) p { color: #E53935 !important; }
            div[role="radiogroup"] label:nth-child(6) p, div[role="radiogroup"] label:nth-child(7) p { color: #1E88E5 !important; }
            div[role="radiogroup"] label:nth-child(8) p, div[role="radiogroup"] label:nth-child(9) p { color: #757575 !important; }
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
            
        st.markdown(f"<div style='text-align: center; color: gray; font-size: 14px; margin-bottom: 5px;'>{tytul} | {info['Data']} | {info['Dystans']}{celownik_tekst}</div>", unsafe_allow_html=True)

        st.radio("Punkty", options=["X", "10", "9", "8", "7", "6", "5", "4", "3", "2", "1", "M", "⌫"], horizontal=True, index=None, key="radio_input", on_change=handle_radio_click, label_visibility="collapsed")

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

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
            r_xs = round_scores.count
