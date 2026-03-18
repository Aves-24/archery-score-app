import streamlit as st
import json
import os
import time
from datetime import datetime, date, timedelta
import gspread
import pandas as pd
import altair as alt
from streamlit_option_menu import option_menu

st.set_page_config(page_title="SFT Schießzettel", layout="centered")

# --- KONFIGURACJA GŁÓWNA ---
NAZWA_ARKUSZA = "Karta_Punktowa" 
ADRES_APLIKACJI = "https://sft-schiesszettel.streamlit.app/"

# TARCZA ANTY-BOTOWA! 
KOD_KLUBU = "SFT"

# --- DYSTANSE ---
dystanse_lista = ["18m", "20m", "30m", "40m", "50m", "60m", "70m"]

# --- SŁOWNIK JĘZYKOWY (PL / DE) ---
T = {
    "PL": {
        "title": "🏹 Karta Punktowa",
        "menu_home": "Home",
        "menu_score": "Schießzettel",
        "menu_multi": "Mini-Turniej",
        "menu_stats": "Statystyki",
        "menu_settings": "Ustawienia",
        "home_welcome": "Witaj",
        "home_last_training": "Ostatni trening:",
        "home_record": "Twój rekord na",
        "home_no_data": "Nie masz jeszcze żadnych wyników. Czas na trening!",
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
        "finish": "💾 Zakończ i Zapisz w Google Sheets",
        "sum_10_x": "Suma 10+X:",
        "only_x": "Same X:",
        "round_fin": "✅ Runda 1 (Zakończona - kliknij, aby rozwinąć)",
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
        "dl_equip_txt": "📥 Pobierz profil sprzętu (TXT)",
        "dl_stats_csv": "📥 Pobierz statystyki (CSV)",
        "rank_title": "🏆 Tabela Wyników na Żywo (Ważna 12 godzin!)",
        "rank_btn": "🔄 Odśwież tabelę",
        "rank_empty": "Brak wyników z ostatnich 12 godzin dla tego kodu. Bądź pierwszy!",
        "stat_no_data": "Brak danych dla tego dystansu. Idź postrzelać! 🏹",
        "stat_metric": "Pokaż na wykresie:"
    },
    "DE": {
        "title": "🏹 Schießzettel",
        "menu_home": "Home",
        "menu_score": "Schießzettel",
        "menu_multi": "Mini-Turnier",
        "menu_stats": "Statistiken",
        "menu_settings": "Einstellungen",
        "home_welcome": "Willkommen",
        "home_last_training": "Dein letztes Training:",
        "home_record": "Dein Rekord auf",
        "home_no_data": "Noch keine Ergebnisse vorhanden. Zeit für ein Training!",
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
        "sum_10_x": "Summe 10+X:",
        "only_x": "Nur X:",
        "round_fin": "✅ Runde 1 (Beendet - zum Aufklappen klicken)",
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
        "stat_metric": "Zeige im Diagramm:"
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

lang = st.session_state.lang

# --- BAZA I USTAWIENIA ---
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

def wyloguj():
    st.session_state.zalogowany_zawodnik = None
    st.session_state.started = False
    st.session_state.scores = []
    st.session_state.extra_arrows = 0
    st.rerun()

def zmiana_dystansow():
    nowe_aktywne = [d for d in dystanse_lista if st.session_state.get(f"chk_{d}", False)]
    if not nowe_aktywne: nowe_aktywne = ["18m"] 
    st.session_state.aktywne_dystanse = nowe_aktywne
    save_user_settings()

def zmiana_jezyka():
    st.session_state.lang = st.session_state.lang_sel
    save_user_settings()

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

# --- MULTIPLAYER (Z LOGIKĄ 12 GODZIN) ---
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

# --- INICJALIZACJA ZMIENNYCH SPRZĘTU ---
for d in dystanse_lista:
    if f"aus_{d}" not in st.session_state: st.session_state[f"aus_{d}"] = ""
    if f"hoehe_{d}" not in st.session_state: st.session_state[f"hoehe_{d}"] = ""
    if f"seite_{d}" not in st.session_state: st.session_state[f"seite_{d}"] = ""
for z in ["zuggewicht", "standhoehe", "tiller", "nockpunkt", "pfeil_modell", "pfeil_spine", "pfeil_laenge", "pfeil_spitze"]:
    if z not in st.session_state: st.session_state[z] = ""

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
                st.session_state.zalogowany_zawodnik = czysta_nazwa
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
    
    tytul = f"{info['Typ']}" + (f
