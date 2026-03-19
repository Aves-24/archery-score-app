import streamlit as st
import json
import os
import time
from datetime import datetime, date, timedelta
import gspread
import pandas as pd
import altair as alt
import urllib.parse
from streamlit_option_menu import option_menu

st.set_page_config(page_title="SFT Schießzettel", layout="centered", initial_sidebar_state="collapsed")

# --- UKRYCIE INTERFEJSU STREAMLIT (WYGLĄD NATYWNEJ APLIKACJI) ---
st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stDeployButton {display:none;}
    </style>
""", unsafe_allow_html=True)

# --- KONFIGURACJA GŁÓWNA ---
NAZWA_ARKUSZA = "Karta_Punktowa" 
ADRES_APLIKACJI = "https://sft-schiesszettel.streamlit.app/"
KOD_KLUBU = "SFT"
dystanse_lista = ["18m", "20m", "30m", "40m", "50m", "60m", "70m"]

# --- SŁOWNIK JĘZYKOWY (PL / DE) ---
T = {
    "PL": {
        "title": "🏹 Karta Punktowa",
        "menu_home": "Home",
        "menu_score": "Schießzettel",
        "menu_multi": "Mini-Turniej",
        "menu_stats": "Statystyki",
        "menu_calendar": "Kalendarz",
        "menu_settings": "Ustawienia",
        "home_welcome": "Witaj",
        "home_last_training": "Ostatni trening:",
        "home_record": "Twój rekord na",
        "home_no_data": "Nie masz jeszcze żadnych wyników. Czas na trening!",
        "upcoming_events": "🗓️ Twoje nadchodzące wyjazdy/treningi",
        "no_events": "Brak zaplanowanych wydarzeń.",
        "training": "Trening",
        "tournament": "Turniej",
        "event_name": "Nazwa turnieju:",
        "event_name_ph": "np. Mistrzostwa Klubu",
        "choose_dist": "🎯 **Wybierz dystans:**",
        "room_code": "2-cyfrowy kod pokoju (np. 12):",
        "start_btn": "🚀 ROZPOCZNIJ STRZELANIE",
        "start_multi_btn": "⚔️ DOŁĄCZ I ROZPOCZNIJ",
        "lang_label": "Wybierz język / Sprache:",
        "dist": "Dystans",
        "total_score": "### 📊 Wynik Całkowity (Mecz)",
        "pts": "Punkty",
        "arrow_cnt": "Licznik strzał",
        "eff": "Skuteczność",
        "warmup": "Strzały próbne / rozgrzewka:",
        "add_6": "➕ 6 strzał",
        "add_1": "➕ 1 strzała",
        "undo": "➖ Cofnij",
        "finish": "💾 Zakończ i Zapisz",
        "pause_btn": "⏸️ Wstrzymaj (Menu)",
        "resume_btn": "▶️ Kontynuuj strzelanie",
        "discard_btn": "🗑️ Odrzuć sesję",
        "unfinished_msg": "⚠️ Masz wstrzymany trening w tle!",
        "cancel_btn": "❌ Anuluj",
        "sum_10_x": "Suma 10+X:",
        "only_x": "Same X:",
        "round_fin": "✅ Runda 1 (Zakończona)",
        "bow_setup": "🏹 Łuk (Bogen-Setup)",
        "draw_weight": "Siła (Zuggewicht) [lbs]",
        "brace_height": "Wys. cięciwy (Standhöhe) [cm/in]",
        "tiller": "Tiller [mm]",
        "nock_point": "P. siodełka (Nockpunkt) [mm]",
        "arrows_setup": "🎯 Strzały (Pfeile)",
        "arr_model": "Model (Modell)",
        "arr_spine": "Sztywność (Spine)",
        "arr_len": "Długość (Länge) [in]",
        "arr_point": "Waga grotu (Spitze) [gr]",
        "visier": "🔭 Celownik (Visier)",
        "choose_dist_settings": "Zaznacz widoczne dystanse na torze:",
        "dl_equip_txt": "📥 Pobierz profil sprzętu",
        "dl_stats_csv": "📥 Pobierz statystyki (CSV)",
        "rank_title": "🏆 Tabela Wyników (Ważna 12 godzin!)",
        "rank_btn": "🔄 Odśwież tabelę",
        "rank_empty": "Brak wyników z ostatnich 12 godzin dla tego kodu. Bądź pierwszy!",
        "stat_no_data": "Brak danych dla tego dystansu. Idź postrzelać! 🏹",
        "stat_metric": "Pokaż na wykresie:",
        "my_plan": "Mój Terminarz",
        "my_diary": "Mój Dziennik",
        "add_event": "➕ Dodaj wydarzenie",
        "event_date": "Data",
        "event_event_name": "Nazwa wydarzenia",
        "event_address": "Adres (opcjonalnie)",
        "nav_btn": "Nawiguj"
    },
    "DE": {
        "title": "🏹 Schießzettel",
        "menu_home": "Home",
        "menu_score": "Schießzettel",
        "menu_multi": "Mini-Turnier",
        "menu_stats": "Statistiken",
        "menu_calendar": "Kalender",
        "menu_settings": "Einstellungen",
        "home_welcome": "Willkommen",
        "home_last_training": "Dein letztes Training:",
        "home_record": "Dein Rekord auf",
        "home_no_data": "Noch keine Ergebnisse vorhanden. Zeit für ein Training!",
        "upcoming_events": "🗓️ Deine nächsten Termine",
        "no_events": "Keine geplanten Ereignisse.",
        "training": "Training",
        "tournament": "Turnier",
        "event_name": "Turniername:",
        "event_name_ph": "z.B. Vereinsmeisterschaft",
        "choose_dist": "🎯 **Wähle Distanz:**",
        "room_code": "2-stelliger Raumcode (z.B. 12):",
        "start_btn": "🚀 SCHIESSEN STARTEN",
        "start_multi_btn": "⚔️ BEITRETEN & STARTEN",
        "lang_label": "Sprache / Wybierz język:",
        "dist": "Distanz",
        "total_score": "### 📊 Gesamtergebnis (Match)",
        "pts": "Punkte",
        "arrow_cnt": "Pfeile",
        "eff": "Quote",
        "warmup": "Probepfeile / Aufwärmen:",
        "add_6": "➕ 6 Pfeile",
        "add_1": "➕ 1 Pfeil",
        "undo": "➖ Zurück",
        "finish": "💾 Beenden & Speichern",
        "pause_btn": "⏸️ Pause (Menü)",
        "resume_btn": "▶️ Schießen fortsetzen",
        "discard_btn": "🗑️ Sitzung verwerfen",
        "unfinished_msg": "⚠️ Du hast ein pausiertes Training im Hintergrund!",
        "cancel_btn": "❌ Abbrechen",
        "sum_10_x": "Summe 10+X:",
        "only_x": "Nur X:",
        "round_fin": "✅ Runde 1 (Beendet)",
        "bow_setup": "🏹 Bogen-Setup",
        "draw_weight": "Zuggewicht [lbs]",
        "brace_height": "Standhöhe [cm/in]",
        "tiller": "Tiller [mm]",
        "nock_point": "Nockpunkt [mm]",
        "arrows_setup": "🎯 Pfeile",
        "arr_model": "Modell",
        "arr_spine": "Spine-Wert",
        "arr_len": "Pfeillänge [in]",
        "arr_point": "Spitzengewicht [gr]",
        "visier": "🔭 Visier",
        "choose_dist_settings": "Sichtbare Distanzen markieren:",
        "dl_equip_txt": "📥 Ausrüstungsprofil herunterladen",
        "dl_stats_csv": "📥 Statistiken herunterladen (CSV)",
        "rank_title": "🏆 Live-Rangliste (12 Stunden gültig!)",
        "rank_btn": "🔄 Tabelle aktualisieren",
        "rank_empty": "Keine Ergebnisse aus den letzten 12 Stunden für diesen Code. Sei der Erste!",
        "stat_no_data": "Keine Daten für diese Distanz. Geh schießen! 🏹",
        "stat_metric": "Zeige im Diagramm:",
        "my_plan": "Mein Terminplan",
        "my_diary": "Mein Tagebuch",
        "add_event": "➕ Ereignis hinzufügen",
        "event_date": "Datum",
        "event_event_name": "Name des Ereignisses",
        "event_address": "Adresse (optional)",
        "nav_btn": "Route starten"
    }
}

# --- INICJALIZACJA SESJI ---
if 'lang' not in st.session_state: st.session_state.lang = "DE" 
if 'zalogowany_zawodnik' not in st.session_state: st.session_state.zalogowany_zawodnik = None
if 'aktywne_dystanse' not in st.session_state: st.session_state.aktywne_dystanse = ["18m", "30m", "70m"]
if 'started' not in st.session_state: 
    st.session_state.started = False
    st.session_state.scores = []
    st.session_state.extra_arrows = 0
    st.session_state.event_info = {} # Inicjalizacja pustego info o treningu

lang = st.session_state.lang

def get_autosave_file(): return f"autosave_{st.session_state.zalogowany_zawodnik}.json"

def save_user_settings():
    if st.session_state.zalogowany_zawodnik:
        with open(f"settings_{st.session_state.zalogowany_zawodnik}.json", "w") as f:
            json.dump({"aktywne_dystanse": st.session_state.aktywne_dystanse, "lang": st.session_state.lang}, f)

def load_user_settings(zawodnik):
    plik = f"settings_{zawodnik}.json"
    if os.path.exists(plik):
        try:
            with open(plik, "r") as f:
                data = json.load(f)
                st.session_state.aktywne_dystanse = data.get("aktywne_dystanse", ["18m", "30m", "70m"])
                st.session_state.lang = data.get("lang", "DE") 
        except: pass

# --- FUNKCJE GOOGLE SHEETS ---
@st.cache_data(ttl=30)
def pobierz_uzytkownikow():
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        sh = gc.open(NAZWA_ARKUSZA)
        try: ws = sh.worksheet("Konta")
        except:
            ws = sh.add_worksheet(title="Konta", rows="100", cols="2")
            ws.append_row(["Zawodnik", "PIN"])
            return {}
        return {str(r["Zawodnik"]).strip(): str(r["PIN"]).strip().lstrip("'") for r in ws.get_all_records()}
    except: return {}

def dodaj_uzytkownika(nazwa, pin):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        gc.open(NAZWA_ARKUSZA).worksheet("Konta").append_row([nazwa, f"'{pin}"])
        st.cache_data.clear() 
        return True
    except: return False

def pobierz_profil_sprzetu(zawodnik):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        zapisy = gc.open(NAZWA_ARKUSZA).worksheet("Profil_Sprzetu").get_all_records()
        if not zapisy: return None
        df_zawodnik = pd.DataFrame(zapisy)
        df_zawodnik = df_zawodnik[df_zawodnik["Zawodnik"] == zawodnik]
        return df_zawodnik.iloc[-1].to_dict() if not df_zawodnik.empty else None
    except: return None

def zapisz_profil_sprzetu(zawodnik, dane):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        sh = gc.open(NAZWA_ARKUSZA)
        try: ws = sh.worksheet("Profil_Sprzetu")
        except:
            ws = sh.add_worksheet(title="Profil_Sprzetu", rows="100", cols="31")
            naglowki = ["Data", "Zawodnik", "Zuggewicht", "Standhoehe", "Tiller", "Nockpunkt", "Pfeil_Modell", "Pfeil_Spine", "Pfeil_Laenge", "Pfeil_Spitze"]
            for d in dystanse_lista: naglowki.extend([f"aus_{d}", f"hoehe_{d}", f"seite_{d}"])
            ws.append_row(naglowki)
            
        wiersz = [datetime.now().strftime("%d.%m.%Y %H:%M"), zawodnik, dane['zuggewicht'], dane['standhoehe'], dane['tiller'], dane['nockpunkt'], dane['pfeil_modell'], dane['pfeil_spine'], dane['pfeil_laenge'], dane['pfeil_spitze']]
        for d in dystanse_lista: wiersz.extend([dane[f"aus_{d}"], dane[f"hoehe_{d}"], dane[f"seite_{d}"]])
        ws.append_row(wiersz)
        return True
    except: return False

@st.cache_data(ttl=15)
def pobierz_dane_z_arkusza(zawodnik):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        zapisy = gc.open(NAZWA_ARKUSZA).worksheet(zawodnik).get_all_records()
        if zapisy:
            df = pd.DataFrame(zapisy)
            df.columns = df.columns.astype(str).str.strip()
            for col in ["Punkty", "Same X", "10", "9", "M", "Strzały (Suma)"]:
                if col in df.columns: df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
                else: df[col] = 0
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def zapisz_do_arkusza(dane_treningu, statystyki):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        sh = gc.open(NAZWA_ARKUSZA)
        zawodnik = st.session_state.zalogowany_zawodnik
        try: ws = sh.worksheet(zawodnik)
        except:
            ws = sh.add_worksheet(title=zawodnik, rows="100", cols="20")
            ws.append_row(["Data", "Czas", "Typ", "Nazwa", "Dystans", "Punkty", "Max", "Skuteczność %", "Strzały (Suma)", "10+X", "Same X", "Wizjer Dziurka", "Wizjer Skala", "10", "9", "M"])
            
        ws.append_row([
            dane_treningu["Data"], datetime.now().strftime("%H:%M:%S"), dane_treningu["Typ"], dane_treningu["Nazwa"],
            dane_treningu["Dystans"], statystyki["Punkty"], statystyki["Max"], f"{statystyki['Skuteczność']:.1f}%",
            statystyki["Strzały"], statystyki["10_i_X"], statystyki["X"], "-", dane_treningu["CelownikSkala"],
            statystyki["10"], statystyki["9"], statystyki["M"]
        ])
        st.cache_data.clear()
        return True
    except: return False

def zapisz_wynik_grupowy(zawodnik, kod, punkty, x10, x):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        sh = gc.open(NAZWA_ARKUSZA)
        try: ws = sh.worksheet("Wyniki_Grupowe_V2")
        except:
            ws = sh.add_worksheet(title="Wyniki_Grupowe_V2", rows="1000", cols="6")
            ws.append_row(["DataCzas", "Kod", "Zawodnik", "Punkty", "10_i_X", "Same X"])
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([now_str, str(kod).strip(), zawodnik, punkty, x10, x])
        st.cache_data.clear()
    except: pass

@st.cache_data(ttl=5)
def pobierz_ranking():
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        return pd.DataFrame(gc.open(NAZWA_ARKUSZA).worksheet("Wyniki_Grupowe_V2").get_all_records())
    except: return pd.DataFrame()

@st.cache_data(ttl=5)
def pobierz_kalendarz_osobisty(zawodnik):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        sh = gc.open(NAZWA_ARKUSZA)
        try: ws = sh.worksheet("Kalendarz_Osobisty")
        except:
            ws = sh.add_worksheet(title="Kalendarz_Osobisty", rows="100", cols="6")
            ws.append_row(["ID", "Zawodnik", "Data", "Nazwa", "Adres", "Link"])
            return pd.DataFrame()
            
        zapisy = ws.get_all_values()
        if len(zapisy) > 1:
            headers = ["ID", "Zawodnik", "Data", "Nazwa", "Adres", "Link"]
            data = []
            for r in zapisy[1:]:
                row_data = r + [""] * (6 - len(r))
                data.append(row_data[:6])
            df = pd.DataFrame(data, columns=headers)
            return df[df["Zawodnik"] == zawodnik]
        return pd.DataFrame()
    except: return pd.DataFrame()

def dodaj_kalendarz_osobisty(zawodnik, data, nazwa, adres, link):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        ws = gc.open(NAZWA_ARKUSZA).worksheet("Kalendarz_Osobisty")
        event_id = f"EV-{int(time.time() * 1000)}"
        ws.append_row([event_id, zawodnik, data.strftime("%d.%m.%Y"), nazwa, adres, link])
        st.cache_data.clear()
        return True
    except: return False

def usun_kalendarz_osobisty(event_id):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        ws = gc.open(NAZWA_ARKUSZA).worksheet("Kalendarz_Osobisty")
        
        zapisy = ws.get_all_values()
        for i, row in enumerate(zapisy):
            if str(row[0]) == str(event_id):
                ws.delete_rows(i + 1) 
                st.cache_data.clear()
                return True
        return False
    except: return False

# --- FUNKCJE POMOCNICZE LOGOWANIA ---
if "del" in st.query_params:
    usun_kalendarz_osobisty(st.query_params["del"])
    del st.query_params["del"] 
    st.rerun()

def wykonaj_logowanie(czysta_nazwa):
    st.session_state.zalogowany_zawodnik = czysta_nazwa
    st.query_params["u"] = czysta_nazwa 
    load_user_settings(czysta_nazwa)
    
    plik = get_autosave_file()
    if os.path.exists(plik):
        try:
            with open(plik, "r") as f:
                data = json.load(f)
                if data.get("started"):
                    st.session_state.started = True
                    st.session_state.scores = data.get("scores", [])
                    st.session_state.extra_arrows = data.get("extra_arrows", 0)
                    st.session_state.event_info = data.get("event_info", {})
                    st.session_state.max_arrows_per_round = data.get("max_arrows_per_round", 36)
                    st.session_state.max_total_arrows = data.get("max_total_arrows", 72)
        except: pass
    
    zapisane_dane = pobierz_profil_sprzetu(czysta_nazwa)
    if zapisane_dane:
        for d in dystanse_lista:
            st.session_state[f"aus_{d}"] = str(zapisane_dane.get(f"aus_{d}", ""))
            st.session_state[f"hoehe_{d}"] = str(zapisane_dane.get(f"hoehe_{d}", ""))
            st.session_state[f"seite_{d}"] = str(zapisane_dane.get(f"seite_{d}", ""))
        for z, k in zip(["zuggewicht", "standhoehe", "tiller", "nockpunkt", "pfeil_modell", "pfeil_spine", "pfeil_laenge", "pfeil_spitze"], 
                        ["Zuggewicht", "Standhoehe", "Tiller", "Nockpunkt", "Pfeil_Modell", "Pfeil_Spine", "Pfeil_Laenge", "Pfeil_Spitze"]):
            st.session_state[z] = str(zapisane_dane.get(k, ""))

def wyloguj():
    st.session_state.zalogowany_zawodnik = None
    st.session_state.started = False
    st.session_state.scores = []
    st.session_state.extra_arrows = 0
    if "u" in st.query_params:
        del st.query_params["u"]
    st.rerun()

def zmiana_dystansow():
    nowe_aktywne = [d for d in dystanse_lista if st.session_state.get(f"chk_{d}", False)]
    if not nowe_aktywne: nowe_aktywne = ["18m"] 
    st.session_state.aktywne_dystanse = nowe_aktywne
    save_user_settings()

def zmiana_jezyka():
    st.session_state.lang = st.session_state.lang_sel
    save_user_settings()

# --- SYSTEM PUNKTACJI W TLE ---
def save_backup():
    if st.session_state.get('started') and st.session_state.zalogowany_zawodnik:
        with open(get_autosave_file(), "w") as f: 
            json.dump({"started": True, "scores": st.session_state.scores, "extra_arrows": st.session_state.extra_arrows, "event_info": st.session_state.event_info, "max_arrows_per_round": st.session_state.max_arrows_per_round, "max_total_arrows": st.session_state.max_total_arrows}, f)

def reset():
    plik = get_autosave_file()
    if os.path.exists(plik): os.remove(plik)
    st.session_state.started = False
    st.session_state.scores = []
    st.session_state.extra_arrows = 0
    st.session_state.event_info = {} # Pamięta, żeby wyczyścić sesję w 100%
    if 'radio_input' in st.session_state: del st.session_state['radio_input']

def handle_radio_click():
    if 'radio_input' in st.session_state:
        val = st.session_state.radio_input
        if val == "⌫" and len(st.session_state.scores) > 0: 
            st.session_state.scores.pop()
            save_backup()
        elif val is not None and val != "⌫" and len(st.session_state.scores) < st.session_state.max_total_arrows:
            st.session_state.scores.append(val)
            save_backup()
        st.session_state.radio_input = None 

def add_extra_arrows(val):
    if st.session_state.extra_arrows + val >= 0:
        st.session_state.extra_arrows += val
        save_backup()

# Zmienna pomocnicza do sprawdzania wstrzymanej sesji
has_paused_session = bool(st.session_state.get('event_info', {}))

# =====================================================================
# SPRAWDZENIE AUTO-LOGINU
# =====================================================================
if not st.session_state.zalogowany_zawodnik and "u" in st.query_params:
    wykonaj_logowanie(st.query_params["u"])

# =====================================================================
# EKRAN LOGOWANIA
# =====================================================================
if not st.session_state.zalogowany_zawodnik:
    st.markdown(f"<div style='background-color: #2E8B57; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center;'><h2 style='color: white; margin: 0;'>🏹 Schützenprofil</h2></div>", unsafe_allow_html=True)
    konta = pobierz_uzytkownikow()
    tab_log, tab_rej = st.tabs(["🔐 Einloggen", "📝 Konto erstellen"])
    
    with tab_log:
        podana_nazwa = st.text_input("Dein Name / Spitzname:", key="log_nazwa")
        podany_pin = st.text_input("Gib deine 4-stellige PIN ein:", type="password", key="log_pin")
        st.write("")
        if st.button("Schießstand betreten", type="primary", use_container_width=True):
            czysta_nazwa = podana_nazwa.strip()
            if czysta_nazwa in konta and (konta[czysta_nazwa] == podany_pin or konta[czysta_nazwa].zfill(len(podany_pin)) == podany_pin):
                wykonaj_logowanie(czysta_nazwa)
                st.rerun()
            else: st.error("❌ Falscher Name oder PIN!")
                    
    with tab_rej:
        nowy_zawodnik = st.text_input("Dein Name / Spitzname:", key="rej_nazwa")
        nowy_pin = st.text_input("Erfinde eine 4-stellige PIN:", type="password", key="rej_pin")
        podany_kod_klubu = st.text_input("Geheimer Vereins-Code:", type="password", key="rej_kod")
        if st.button("Konto erstellen", type="primary", use_container_width=True):
            if podany_kod_klubu != KOD_KLUBU: st.error("❌ Falscher Vereins-Code!")
            elif nowy_zawodnik.strip() in konta: st.warning("Dieser Schütze existiert bereits!")
            elif dodaj_uzytkownika(nowy_zawodnik.strip(), nowy_pin):
                st.success("✅ Konto erfolgreich erstellt!")
                time.sleep(2)
                st.rerun()
    st.stop() 

# =====================================================================
# GŁÓWNA APLIKACJA
# =====================================================================

st.markdown(f"<div style='text-align: right; color: gray; font-size: 12px; margin-bottom: 5px;'>👤 {st.session_state.zalogowany_zawodnik}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# TRYB SKUPIENIA (TRWA STRZELANIE)
# ---------------------------------------------------------------------
if st.session_state.started:
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
    max_total_score = st.session_state.max_total_arrows * 10
    
    def get_num(s): return 10 if s in ["X", "10"] else (0 if s == "M" else int(s))
    
    tytul = f"{info['Typ']}" + (f" - {info['Nazwa']}" if info['Nazwa'] != "-" else "")
    if info.get('KodMeczu', ""): tytul += f" [⚔️ {info['KodMeczu']}]"
    st.markdown(f"<div style='text-align: center; color: gray; font-size: 14px; margin-bottom: 5px;'>{tytul} | {info['Dystans']}</div>", unsafe_allow_html=True)

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
        r_xs = round_scores.count("X")
        r_10s = round_scores.count("10") + r_xs
        
        html = f"<div style='margin-bottom: 20px; font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
        html += f"<div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 5px;'><b>Runde {round_num}</b><span style='font-weight: bold;'>{info['Dystans']}</span></div>"
        html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black;'>"
        html += f"<tr style='background-color: #f2f2f2; border-bottom: 1px solid black;'><th rowspan='2' style='border: 1px solid black; border-right: 2px solid black; width: 30px;'></th><th colspan='{arrows_per_end}' style='border: 1px solid black; font-size: 14px;'>Pfeile</th><th colspan='2' style='border: 1px solid black; border-left: 2px solid black; font-size: 14px;'>Summen</th></tr>"
        html += f"<tr style='background-color: #f2f2f2; border-bottom: 2px solid black;'>"
        for arr in range(1, arrows_per_end + 1): html += f"<th style='border: 1px solid black; padding: 2px; width: 30px; font-size: 12px;'>{arr}</th>"
        html += f"<th style='border: 1px solid black; border-left: 2px solid black; font-size: 12px;'>Serie</th><th style='border: 1px solid black; font-size: 12px;'>Übertrag</th></tr>"
        cumul_total = cumulative_start
        
        for end_idx in range(info['SeriiWRundzie']):
            arrow_idx_start = end_idx * arrows_per_end
            end_scores = round_scores[arrow_idx_start:arrow_idx_start + arrows_per_end]
            end_sum = sum(get_num(s) for s in end_scores) if len(end_scores) > 0 else ""
            if end_sum != "": cumul_total += end_sum
                
            html += "<tr>"
            html += f"<td style='border: 1px solid black; border-right: 2px solid black; padding: 4px; font-weight: bold;'>{(end_idx + 1) * arrows_per_end}</td>"
            for j in range(arrows_per_end):
                if j < len(end_scores):
                    val = end_scores[j]
                    circle = f"<div style='width: 22px; height: 22px; border-radius: 50%; {get_color_style(val)} display: inline-flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; margin: 0 auto; border: 1px solid #aaa;'>{val}</div>"
                    html += f"<td style='border: 1px solid black; padding: 2px;'>{circle}</td>"
                else: html += "<td style='padding: 2px; border: 1px solid black;'></td>"
            html += f"<td style='border: 1px solid black; border-left: 2px solid black; font-weight: bold;'>{end_sum}</td>"
            html += f"<td style='border: 1px solid black; font-weight: bold;'>{cumul_total if len(end_scores)>0 else ''}</td></tr>"
            
        html += f"<tr style='border-top: 2px solid black; background-color: #f9f9f9;'><td colspan='{arrows_per_end + 1}' style='text-align: right; padding: 5px; font-weight: bold; border-right: 2px solid black;'>Summe:</td><td colspan='2' style='font-weight: bold; font-size: 16px;'>{r_points}</td></tr></table></div>"
        return html, cumul_total

    round1_scores = scores[:st.session_state.max_arrows_per_round]
    round2_scores = scores[st.session_state.max_arrows_per_round:]

    if len(round2_scores) == 0:
        html1, cumul1 = render_round_html(1, round1_scores, 0)
        st.markdown(html1, unsafe_allow_html=True)
    else:
        html1, cumul1 = render_round_html(1, round1_scores, 0)
        with st.expander(T[lang]["round_fin"], expanded=False): st.markdown(html1, unsafe_allow_html=True)
        html2, _ = render_round_html(2, round2_scores, cumul1)
        st.markdown(html2, unsafe_allow_html=True)

    total_points = sum(get_num(s) for s in scores)
    percent = (total_points / (len(scores) * 10) * 100) if len(scores) > 0 else 0
    total_arrows_shot = len(scores) + st.session_state.extra_arrows
    count_x = scores.count("X")
    count_10_total = scores.count("10") + count_x 
    
    st.markdown(T[lang]["total_score"])
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric(T[lang]["pts"], f"{total_points} / {max_total_score}")
    col_s2.metric(T[lang]["arrow_cnt"], f"{total_arrows_shot}")
    col_s3.metric(T[lang]["eff"], f"{percent:.1f}%")
    
    st.write("")
    st.markdown(f"<span style='font-size:14px; color:gray;'>{T[lang]['warmup']}</span>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.button(T[lang]["add_6"], on_click=add_extra_arrows, args=(6,), use_container_width=True)
    c2.button(T[lang]["add_1"], on_click=add_extra_arrows, args=(1,), use_container_width=True)
    c3.button(T[lang]["undo"], on_click=add_extra_arrows, args=(-1,), use_container_width=True)

    st.write("")
    
    # --- NOWE PRZYCISKI DO ZARZĄDZANIA SESJĄ NA DOLE ---
    if st.button(T[lang]["finish"], type="primary", use_container_width=True):
        statystyki_koncowe = {"Punkty": total_points, "Max": max_total_score, "Skuteczność": percent, "Strzały": total_arrows_shot, "10_i_X": count_10_total, "X": count_x, "10": count_10_total, "9": scores.count("9"), "M": scores.count("M")}
        if zapisz_do_arkusza(st.session_state.event_info, statystyki_koncowe):
            kod_meczu = st.session_state.event_info.get("KodMeczu", "")
            if kod_meczu: zapisz_wynik_grupowy(st.session_state.zalogowany_zawodnik, kod_meczu, total_points, count_10_total, count_x)
            st.success("✅ Gespeichert!" if lang=="DE" else "✅ Zapisano!")
            time.sleep(1.5)
        reset()
        st.rerun()
        
    c_p, c_c = st.columns(2)
    if c_p.button(T[lang]["pause_btn"], use_container_width=True):
        st.session_state.started = False # Wychodzimy z trybu skupienia, ale NIE usuwamy wyniku!
        st.rerun()
    if c_c.button(T[lang]["cancel_btn"], use_container_width=True):
        reset()
        st.rerun()

# ---------------------------------------------------------------------
# NOWE MENU GŁÓWNE (DASHBOARD) - KIEDY NIE STRZELASZ
# ---------------------------------------------------------------------
else:
    with st.container():
        wybrana_zakladka = option_menu(
            menu_title=None,
            options=[T[lang]["menu_home"], T[lang]["menu_score"], T[lang]["menu_multi"], T[lang]["menu_stats"], T[lang]["menu_calendar"], T[lang]["menu_settings"]], 
            icons=['house', 'bullseye', 'trophy', 'graph-up', 'calendar-date', 'gear'], 
            default_index=0, 
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#ffffff", "border": "1px solid #ddd", "border-radius": "10px", "margin-bottom": "20px"},
                "icon": {"color": "#D4AC0D", "font-size": "15px"}, 
                "nav-link": {"font-size": "12px", "text-align": "center", "margin":"0px", "padding": "10px 5px", "--hover-color": "#f4f4f4"},
                "nav-link-selected": {"background-color": "#2E8B57", "font-weight": "bold", "color": "white"},
            }
        )

    # --- ZAKŁADKA: HOME ---
    if wybrana_zakladka == T[lang]["menu_home"]:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 18px; font-weight: bold;'>🏠 {T[lang]['home_welcome']}, {st.session_state.zalogowany_zawodnik}! 🎯</p></div>", unsafe_allow_html=True)
        
        df_historia = pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
        
        if df_historia.empty:
            st.info(T[lang]["home_no_data"])
        else:
            ostatni = df_historia.iloc[-1]
            ostatni_dystans = ostatni['Dystans']
            ostatnie_punkty = ostatni['Punkty']
            ostatnia_data = ostatni['Data']
            
            rekord = df_historia[df_historia['Dystans'] == ostatni_dystans]['Punkty'].max()

            st.markdown(f"""
            <div style='background-color: #f9f9f9; padding: 12px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 20px;'>
                <p style='margin: 0; font-size: 14px; color: gray;'>{T[lang]['home_last_training']}</p>
                <p style='margin: 5px 0; font-size: 16px; font-weight: bold;'>🗓️ {ostatnia_data}  |  🎯 {ostatni_dystans}  |  🏅 {ostatnie_punkty} pts</p>
                <hr style='margin: 8px 0; border: none; border-top: 1px solid #ddd;'>
                <p style='margin: 0; font-size: 14px; color: #D4AC0D;'>🏆 {T[lang]['home_record']} <b>{ostatni_dystans}</b>: <b>{rekord} pts</b></p>
            </div>
            """, unsafe_allow_html=True)
            
        st.write(f"**{T[lang]['upcoming_events']}**")
        df_my_cal = pobierz_kalendarz_osobisty(st.session_state.zalogowany_zawodnik)
        if df_my_cal.empty:
            st.info(T[lang]["no_events"])
        else:
            df_my_cal['Datetime'] = pd.to_datetime(df_my_cal['Data'], format='%d.%m.%Y', errors='coerce')
            df_my_cal = df_my_cal.dropna(subset=['Datetime'])
            limit_czasu = pd.to_datetime(date.today())
            df_my_cal = df_my_cal[df_my_cal['Datetime'] >= limit_czasu].sort_values('Datetime')
            
            if df_my_cal.empty:
                st.info(T[lang]["no_events"])
            else:
                top3 = df_my_cal.head(3)
                for _, row in top3.iterrows():
                    adres_text = str(row.get("Adres", "")).strip()
                    adres_html = ""
                    if adres_text:
                        encoded_adres = urllib.parse.quote(adres_text)
                        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_adres}"
                        adres_html = f"<div style='margin-top: 6px;'><span style='font-size: 13px; color: gray;'>🏠 {adres_text}</span> <a href='{maps_url}' target='_blank' style='text-decoration: none; display: inline-block; margin-left: 8px; background-color: #e3f2fd; border: 1px solid #bbdefb; padding: 4px 8px; border-radius: 6px; font-size: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>📍</a></div>"
                    
                    st.markdown(f"""
                    <div style='background-color: #ffffff; border: 1px solid #eee; padding: 12px; border-radius: 8px; border-left: 5px solid #D4AC0D; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                        <b style='font-size: 14px; color: #333;'>🗓️ {row['Data']}</b> | <span style='font-size: 15px; color: #000; font-weight: 500;'>{row['Nazwa']}</span>
                        {adres_html}
                    </div>
                    """, unsafe_allow_html=True)

        st.write("")
        btn_wa_txt = "🟢 App über WhatsApp teilen" if lang == "DE" else "🟢 Udostępnij aplikację przez WhatsApp"
        st.markdown(f"""
            <div style='text-align: center; margin-top: 10px;'>
                <a href="whatsapp://send?text=Hallo! 👋 Schau dir unsere Vereins-App an: {ADRES_APLIKACJI}" target="_blank" style="text-decoration: none; background-color: #25D366; color: white; padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 14px;">
                    {btn_wa_txt}
                </a>
            </div>
        """, unsafe_allow_html=True)

    # --- ZAKŁADKA: SCHIESSZETTEL ---
    elif wybrana_zakladka == T[lang]["menu_score"]:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 16px; font-weight: bold;'>🎯 {T[lang]['menu_score']} Setup</p></div>", unsafe_allow_html=True)
        
        if has_paused_session:
            st.warning(T[lang]["unfinished_msg"])
            c_r, c_d = st.columns(2)
            if c_r.button(T[lang]["resume_btn"], type="primary", use_container_width=True):
                st.session_state.started = True
                st.rerun()
            if c_d.button(T[lang]["discard_btn"], use_container_width=True):
                reset()
                st.rerun()
        else:
            event_type = st.radio("typ_wydarzenia", [T[lang]["training"], T[lang]["tournament"]], horizontal=True, label_visibility="collapsed")
            event_name = "-"
            if event_type == T[lang]["tournament"]:
                event_name = st.text_input(T[lang]["event_name"], placeholder=T[lang]["event_name_ph"])
                
            st.write("") 
            st.write(T[lang]["choose_dist"])
            dystans = st.radio("Dystans", st.session_state.aktywne_dystanse, horizontal=True, label_visibility="collapsed")

            st.write("")
            if st.button(T[lang]["start_btn"], type="primary", use_container_width=True):
                czesci = []
                if st.session_state[f'aus_{dystans}']: czesci.append(f"A:{st.session_state[f'aus_{dystans}']}")
                if st.session_state[f'hoehe_{dystans}']: czesci.append(f"H:{st.session_state[f'hoehe_{dystans}']}")
                if st.session_state[f'seite_{dystans}']: czesci.append(f"S:{st.session_state[f'seite_{dystans}']}")
                
                st.session_state.event_info = {
                    "Data": date.today().strftime("%d.%m.%Y"), "Typ": event_type, "Nazwa": event_name if event_name.strip() else "-",
                    "StrzalWSerii": 6, "SeriiWRundzie": 6, "Dystans": dystans, "KodMeczu": "",
                    "CelownikSkala": " | ".join(czesci) if czesci else "-"
                }
                st.session_state.max_arrows_per_round = 36
                st.session_state.max_total_arrows = 72
                st.session_state.started = True
                save_backup()
                st.rerun()

    # --- ZAKŁADKA: MINI-TURNIER ---
    elif wybrana_zakladka == T[lang]["menu_multi"]:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 16px; font-weight: bold;'>⚔️ {T[lang]['menu_multi']} Setup</p></div>", unsafe_allow_html=True)
        
        if has_paused_session:
            st.warning(T[lang]["unfinished_msg"])
            c_rm, c_dm = st.columns(2)
            if c_rm.button(T[lang]["resume_btn"], type="primary", use_container_width=True, key="res_multi"):
                st.session_state.started = True
                st.rerun()
            if c_dm.button(T[lang]["discard_btn"], use_container_width=True, key="disc_multi"):
                reset()
                st.rerun()
        else:
            st.write(f"**{T[lang]['room_code']}**")
            kod_meczu = st.text_input("Kod Pokoju", max_chars=2, placeholder="np. 07", label_visibility="collapsed")
            
            st.write(T[lang]["choose_dist"])
            dystans_multi = st.radio("Dystans Multi", st.session_state.aktywne_dystanse, horizontal=True, label_visibility="collapsed")

            st.write("")
            if st.button(T[lang]["start_multi_btn"], type="primary", use_container_width=True):
                if not kod_meczu.strip(): st.error("Bitte gib einen Code ein!" if lang == "DE" else "Podaj kod!")
                else:
                    czesci = []
                    if st.session_state[f'aus_{dystans_multi}']: czesci.append(f"A:{st.session_state[f'aus_{dystans_multi}']}")
                    if st.session_state[f'hoehe_{dystans_multi}']: czesci.append(f"H:{st.session_state[f'hoehe_{dystans_multi}']}")
                    if st.session_state[f'seite_{dystans_multi}']: czesci.append(f"S:{st.session_state[f'seite_{dystans_multi}']}")
                    
                    st.session_state.event_info = {
                        "Data": date.today().strftime("%d.%m.%Y"), "Typ": T[lang]["training"], "Nazwa": "Mini-Turnier",
                        "StrzalWSerii": 6, "SeriiWRundzie": 6, "Dystans": dystans_multi, "KodMeczu": kod_meczu.strip(),
                        "CelownikSkala": " | ".join(czesci) if czesci else "-"
                    }
                    st.session_state.max_arrows_per_round = 36
                    st.session_state.max_total_arrows = 72
                    st.session_state.started = True
                    save_backup()
                    st.rerun()
                
        st.write("")
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 16px; font-weight: bold;'>{T[lang]['rank_title']}</p></div>", unsafe_allow_html=True)
        
        col_r1, col_r2 = st.columns([2,1])
        szukany_kod = col_r1.text_input("Szukaj Kodu", max_chars=2, key="search_code", placeholder="z.B. 12", label_visibility="collapsed")
        
        if col_r2.button(T[lang]["rank_btn"], type="secondary", use_container_width=True):
            if not szukany_kod: st.warning("Bitte gib den Raumcode ein!" if lang == "DE" else "Podaj kod pokoju!")
            else:
                df_rank = pobierz_ranking()
                if df_rank.empty: st.info(T[lang]["rank_empty"])
                else:
                    df_rank["Datetime"] = pd.to_datetime(df_rank["DataCzas"], format="%Y-%m-%d %H:%M:%S", errors='coerce')
                    df_rank = df_rank.dropna(subset=['Datetime'])
                    limit_czasu = datetime.now() - timedelta(hours=12)
                    
                    df_filtrowane = df_rank[(df_rank["Datetime"] >= limit_czasu) & (df_rank["Kod"].astype(str) == str(szukany_kod))]
                    
                    if df_filtrowane.empty: st.info(T[lang]["rank_empty"])
                    else:
                        df_filtrowane["Punkty"] = pd.to_numeric(df_filtrowane["Punkty"])
                        df_filtrowane["10_i_X"] = pd.to_numeric(df_filtrowane["10_i_X"])
                        df_filtrowane["Same X"] = pd.to_numeric(df_filtrowane["Same X"])
                        df_filtrowane = df_filtrowane.sort_values(by=["Punkty", "10_i_X", "Same X"], ascending=[False, False, False]).reset_index(drop=True)
                        
                        st.markdown("---")
                        for idx, row in df_filtrowane.iterrows():
                            m = "🥇" if idx == 0 else ("🥈" if idx == 1 else ("🥉" if idx == 2 else f"**{idx+1}.**"))
                            c_bg = "#FFF9C4" if idx == 0 else "#f9f9f9" 
                            c_b = "#D4AC0D" if idx == 0 else "#ccc"
                            st.markdown(f"""
                            <div style='background-color: {c_bg}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid {c_b};'>
                                <h3 style='margin: 0; color: #333;'>{m} {row['Zawodnik']}</h3>
                                <p style='margin: 5px 0 0 0; font-size: 18px;'><b>{row['Punkty']}</b> Punkte   <span style='font-size: 14px; color: gray;'>(10+X: {row['10_i_X']} | X: {row['Same X']})</span></p>
                                <p style='margin: 0; font-size: 10px; color: gray;'>Beendet: {row['Datetime'].strftime('%H:%M Uhr')}</p>
                            </div>
                            """, unsafe_allow_html=True)

    # --- ZAKŁADKA: STATYSTYKI ---
    elif wybrana_zakladka == T[lang]["menu_stats"]:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 16px; font-weight: bold;'>📊 {T[lang]['menu_stats']}</p></div>", unsafe_allow_html=True)
        st.markdown("""<style>div[data-testid="stVegaLiteChart"] { width: 100%; overflow-x: auto; }</style>""", unsafe_allow_html=True)
        
        df = pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
        
        if df.empty:
            st.info(T[lang]["stat_no_data"])
        else:
            st.write(f"**{T[lang]['choose_dist']}**")
            wybrany_dystans = st.radio("Dystans stat", st.session_state.aktywne_dystanse, horizontal=True, label_visibility="collapsed")
            df_filtrowane = df[df["Dystans"] == wybrany_dystans]
            
            if df_filtrowane.empty: st.warning(T[lang]["stat_no_data"])
            else:
                st.divider()
                st.write(f"**{T[lang]['stat_metric']}**")
                opcje_metryk = {
                    "Punkty": "Punkty", "Same X": "Same X", "Wszystkie 10": "10", 
                    "9": "9", "M (Pudła)": "M", "Strzały (Suma)": "Strzały (Suma)"
                } if lang == "PL" else {
                    "Punkte": "Punkty", "Nur X": "Same X", "Alle 10er": "10", 
                    "9er": "9", "M (Fehler)": "M", "Pfeile (Summe)": "Strzały (Suma)"
                }
                
                wybrana_metryka_klucz = st.radio("Metryka", list(opcje_metryk.keys()), horizontal=True, label_visibility="collapsed")
                kolumna_y = opcje_metryk[wybrana_metryka_klucz]
                
                df_filtrowane = df_filtrowane.copy() 
                df_filtrowane["Sesja"] = df_filtrowane["Data"] + " (" + df_filtrowane["Czas"].astype(str).str[:5] + ")"
                df_filtrowane["Wydarzenie"] = df_filtrowane.apply(lambda row: f"{row['Typ']} - {row['Nazwa']}" if row['Nazwa'] != "-" else row['Typ'], axis=1)
                df_filtrowane['Typ'] = df_filtrowane['Typ'].replace({
                    T["PL"]["training"]: T[lang]["training"], T["DE"]["training"]: T[lang]["training"],
                    T["PL"]["tournament"]: T[lang]["tournament"], T["DE"]["tournament"]: T[lang]["tournament"]
                })
                
                domena_typow = [T[lang]["training"], T[lang]["tournament"]]
                kolory = alt.Scale(domain=domena_typow, range=['#2E8B57', '#1E88E5'])
                
                max_wartosc = df_filtrowane[kolumna_y].max()
                skala_y = alt.Scale(domain=[0, 720], nice=False) if kolumna_y == "Punkty" else alt.Scale(domain=[0, max_wartosc * 1.25 if max_wartosc > 0 else 10], nice=False)
                
                baza = alt.Chart(df_filtrowane).encode(x=alt.X('Sesja:N', title='Data', sort=None, axis=alt.Axis(labelAngle=-45)))
                
                narzedzia = [
                    alt.Tooltip('Punkty:Q', title="🎯 Punkty" if lang=="PL" else "🎯 Punkte"),
                    alt.Tooltip('Wydarzenie:N', title="🏹 Wydarzenie" if lang=="PL" else "🏹 Ereignis"),
                    alt.Tooltip('Strzały (Suma):Q', title="🎯 Ilość strzał" if lang=="PL" else "🎯 Pfeilanzahl"),
                    alt.Tooltip('Same X:Q', title="🟡 Same X" if lang=="PL" else "🟡 Nur X"),
                    alt.Tooltip('10:Q', title="🔟 Wszystkie 10" if lang=="PL" else "🔟 Alle 10er"),
                    alt.Tooltip('9:Q', title="9️⃣ Dziewiątki" if lang=="PL" else "9️⃣ 9er"),
                    alt.Tooltip('M:Q', title="Ⓜ️ Pudła (M)" if lang=="PL" else "Ⓜ️ Fehler (M)"),
                    alt.Tooltip('Data:N', title="🗓️ Data" if lang=="PL" else "🗓️ Datum"),
                    alt.Tooltip('Czas:N', title="⏰ Godzina" if lang=="PL" else "⏰ Uhrzeit")
                ]
                
                slupki = baza.mark_bar(opacity=0.9, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    y=alt.Y(f'{kolumna_y}:Q', title=wybrana_metryka_klucz, scale=skala_y), 
                    color=alt.Color('Typ:N', scale=kolory, legend=alt.Legend(title="Typ", orient="bottom")), tooltip=narzedzia)
                teksty = baza.mark_text(align='center', baseline='bottom', dy=-5, fontWeight='bold', fontSize=12, clip=False).encode(
                    y=alt.Y(f'{kolumna_y}:Q'), text=alt.Text(f'{kolumna_y}:Q')) 
                
                szerokosc_wykresu = max(350, len(df_filtrowane) * 45)
                wykres = (slupki + teksty).properties(width=szerokosc_wykresu, height=350)
                st.altair_chart(wykres, use_container_width=False)

                st.write("")
                df_export = df_filtrowane.copy()
                df_export.drop(columns=[k for k in ["Wizjer Dziurka", "Wizjer Skala", "Zawodnik", "Sesja", "Wydarzenie"] if k in df_export.columns], inplace=True)
                    
                if lang == "DE":
                    df_export.rename(columns={
                        "Data": "Datum", "Czas": "Uhrzeit", "Typ": "Ereignis",
                        "Nazwa": "Name", "Dystans": "Distanz", "Punkty": "Punkte",
                        "Skuteczność %": "Trefferquote %", "Strzały (Suma)": "Pfeilanzahl",
                        "Same X": "Nur X"
                    }, inplace=True)
                    
                st.download_button(
                    label=T[lang]["dl_stats_csv"], 
                    data=df_export.to_csv(index=False).encode('utf-8'), 
                    file_name=f"Statystyki_{st.session_state.zalogowany_zawodnik}_{wybrany_dystans}.csv", 
                    mime='text/csv', 
                    use_container_width=True
                )

    # --- ZAKŁADKA: KALENDARZ ---
    elif wybrana_zakladka == T[lang]["menu_calendar"]:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 16px; font-weight: bold;'>🗓️ {T[lang]['menu_calendar']}</p></div>", unsafe_allow_html=True)
        
        tab_my_plan, tab_diary = st.tabs([T[lang]["my_plan"], T[lang]["my_diary"]])
                    
        with tab_my_plan:
            with st.form("add_my_event", clear_on_submit=True):
                c1, c2 = st.columns([1, 2])
                nowa_data = c1.date_input(T[lang]["event_date"], format="DD.MM.YYYY")
                nowa_nazwa = c2.text_input(T[lang]["event_event_name"])
                nowy_adres = st.text_input(T[lang]["event_address"])
                
                if st.form_submit_button(T[lang]["add_event"]):
                    if nowa_nazwa.strip():
                        dodaj_kalendarz_osobisty(st.session_state.zalogowany_zawodnik, nowa_data, nowa_nazwa, nowy_adres, "")
                        st.rerun()
                    else:
                        st.error("Podaj nazwę!" if lang == "PL" else "Bitte Namen eingeben!")
                        
            df_my_cal = pobierz_kalendarz_osobisty(st.session_state.zalogowany_zawodnik)
            if df_my_cal.empty:
                st.info(T[lang]["no_events"])
            else:
                df_my_cal['Datetime'] = pd.to_datetime(df_my_cal['Data'], format='%d.%m.%Y', errors='coerce')
                df_my_cal = df_my_cal.sort_values('Datetime')
                
                for _, row in df_my_cal.iterrows():
                    adres_text = str(row.get("Adres", "")).strip()
                    adres_html = ""
                    if adres_text:
                        encoded_adres = urllib.parse.quote(adres_text)
                        maps_url = f"https://www.google.com/maps/dir/?api=1&destination={encoded_adres}"
                        adres_html = f"<br><span style='font-size: 13px; color: gray;'>🏠 {adres_text}</span> <a href='{maps_url}' target='_blank' style='text-decoration: none; display: inline-block; margin-left: 8px; background-color: #e3f2fd; border: 1px solid #bbdefb; padding: 4px 8px; border-radius: 6px; font-size: 14px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);'>📍</a>"
                        
                    del_link = f"?u={urllib.parse.quote(st.session_state.zalogowany_zawodnik)}&del={row['ID']}"
                    trash_btn = f"<a href='{del_link}' target='_self' style='text-decoration: none; display: flex; justify-content: center; align-items: center; width: 44px; height: 44px; background-color: #fff; border: 1px solid #ffcdd2; color: #d32f2f; border-radius: 8px; font-size: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: 0.2s;'>🗑️</a>"
                    
                    st.markdown(f"""
                    <div style='background-color: #ffffff; border: 1px solid #eee; padding: 12px; border-radius: 8px; border-left: 5px solid #1E88E5; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                        <div style='display: flex; justify-content: space-between; align-items: flex-end;'>
                            <div style='flex-grow: 1; padding-right: 10px;'>
                                <b style='color: #1E88E5; font-size: 14px;'>🗓️ {row['Data']}</b><br>
                                <span style='font-size: 15px; font-weight: 500; color: #333;'>{row['Nazwa']}</span>
                                {adres_html}
                            </div>
                            <div style='display: flex; align-items: center;'>
                                {trash_btn}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with tab_diary:
            df_hist = pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
            if df_hist.empty:
                st.info(T[lang]["home_no_data"])
            else:
                ostatnie = df_hist.tail(10).iloc[::-1]
                for _, row in ostatnie.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #ffffff; border: 1px solid #ddd; padding: 10px; border-radius: 5px; border-left: 5px solid #2E8B57; margin-bottom: 8px;'>
                        <div style='display: flex; justify-content: space-between;'>
                            <b>🗓️ {row['Data']}</b>
                            <span style='color: gray; font-size: 12px;'>{row['Czas']}</span>
                        </div>
                        <div style='margin-top: 5px; font-size: 15px;'>
                            🎯 <b>{row['Dystans']}</b> | 🏅 <b>{row['Punkty']}</b> pts | 📈 {row.get('Skuteczność %', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # --- ZAKŁADKA: EINSTELLUNGEN ---
    elif wybrana_zakladka == T[lang]["menu_settings"]:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 16px; font-weight: bold;'>⚙️ {T[lang]['menu_settings']}</p></div>", unsafe_allow_html=True)
        
        st.write(f"**{T[lang]['lang_label']}**")
        st.radio("Język", ["DE", "PL"], index=0 if lang=="DE" else 1, horizontal=True, key="lang_sel", on_change=zmiana_jezyka, label_visibility="collapsed")
        
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #2E8B57; margin: 15px 0 10px 0;'><b style='font-size: 15px;'>{T[lang]['bow_setup']}</b></div>", unsafe_allow_html=True)
        c_bow1, c_bow2 = st.columns(2)
        c_bow1.text_input(T[lang]['draw_weight'], key="zuggewicht")
        c_bow2.text_input(T[lang]['brace_height'], key="standhoehe")
        c_bow1.text_input(T[lang]['tiller'], key="tiller")
        c_bow2.text_input(T[lang]['nock_point'], key="nockpunkt")
        
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #2E8B57; margin: 15px 0 10px 0;'><b style='font-size: 15px;'>{T[lang]['arrows_setup']}</b></div>", unsafe_allow_html=True)
        c_arr1, c_arr2 = st.columns(2)
        c_arr1.text_input(T[lang]['arr_model'], key="pfeil_modell")
        c_arr2.text_input(T[lang]['arr_spine'], key="pfeil_spine")
        c_arr1.text_input(T[lang]['arr_len'], key="pfeil_laenge")
        c_arr2.text_input(T[lang]['arr_point'], key="pfeil_spitze")
        
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 8px 12px; border-radius: 6px; border-left: 4px solid #2E8B57; margin: 15px 0 10px 0;'><b style='font-size: 15px;'>{T[lang]['visier']}</b></div>", unsafe_allow_html=True)
        st.markdown(f"<span style='font-size:12px; color:gray;'>{T[lang]['choose_dist_settings']}</span>", unsafe_allow_html=True)
        
        c_vis1, c_vis2, c_vis3, c_vis4 = st.columns([0.8, 1, 1, 1])
        c_vis1.markdown(f"<span style='font-size:12px; color:gray;'>Dist.</span>", unsafe_allow_html=True)
        c_vis2.markdown(f"<span style='font-size:12px; color:gray;'>Ausleger</span>", unsafe_allow_html=True)
        c_vis3.markdown(f"<span style='font-size:12px; color:gray;'>Höhe</span>", unsafe_allow_html=True)
        c_vis4.markdown(f"<span style='font-size:12px; color:gray;'>Seite</span>", unsafe_allow_html=True)
        
        for d in dystanse_lista:
            c1, c2, c3, c4 = st.columns([0.8, 1, 1, 1])
            c1.checkbox(d, value=(d in st.session_state.aktywne_dystanse), key=f"chk_{d}", on_change=zmiana_dystansow)
            c2.text_input(f"Aus {d}", placeholder=st.session_state[f"aus_{d}"] or "Ausl.", key=f"ui_aus_{d}", label_visibility="collapsed")
            c3.text_input(f"Höhe {d}", placeholder=st.session_state[f"hoehe_{d}"] or "Höhenv.", key=f"ui_hoehe_{d}", label_visibility="collapsed")
            c4.text_input(f"Seite {d}", placeholder=st.session_state[f"seite_{d}"] or "Seitenv.", key=f"ui_seite_{d}", label_visibility="collapsed")
        
        st.write("")
        if st.button("💾 Profil in der Cloud speichern" if lang == "DE" else "💾 Zapisz profil w chmurze", use_container_width=True):
            dane_sprzetu = {"zuggewicht": st.session_state["zuggewicht"], "standhoehe": st.session_state["standhoehe"], "tiller": st.session_state["tiller"], "nockpunkt": st.session_state["nockpunkt"], "pfeil_modell": st.session_state["pfeil_modell"], "pfeil_spine": st.session_state["pfeil_spine"], "pfeil_laenge": st.session_state["pfeil_laenge"], "pfeil_spitze": st.session_state["pfeil_spitze"]}
            for d in dystanse_lista:
                for k in ["aus", "hoehe", "seite"]:
                    nw = st.session_state[f"ui_{k}_{d}"].strip()
                    if nw: st.session_state[f"{k}_{d}"] = nw
                    dane_sprzetu[f"{k}_{d}"] = st.session_state[f"{k}_{d}"]
                
            if zapisz_profil_sprzetu(st.session_state.zalogowany_zawodnik, dane_sprzetu):
                st.success("✅ Gespeichert!" if lang=="DE" else "✅ Zapisano!")
                time.sleep(1)
                st.rerun()
                
        st.write("")
        if st.button("🚪 Abmelden / Logout" if lang == "DE" else "🚪 Wyloguj / Logout", use_container_width=True): wyloguj()
