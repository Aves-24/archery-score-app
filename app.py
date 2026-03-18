import streamlit as st
import json
import os
import time
from datetime import datetime, date, timedelta
import gspread
import pandas as pd
import altair as alt

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
        "menu_home": "🏠 Home",
        "menu_score": "🎯 Schießzettel",
        "menu_multi": "⚔️ Mini-Turniej",
        "menu_settings": "⚙️ Ustawienia",
        "home_welcome": "Witaj z powrotem",
        "home_last_training": "Twoje ostatnie strzelanie:",
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
        "rank_title": "🏆 Tabela Wyników na Żywo (Ważna 12 godzin!)",
        "rank_btn": "🔄 Odśwież tabelę",
        "rank_empty": "Brak wyników z ostatnich 12 godzin dla tego kodu. Bądź pierwszy!"
    },
    "DE": {
        "title": "🏹 Schießzettel",
        "menu_home": "🏠 Home",
        "menu_score": "🎯 Schießzettel",
        "menu_multi": "⚔️ Mini-Turnier",
        "menu_settings": "⚙️ Einstellungen",
        "home_welcome": "Willkommen zurück",
        "home_last_training": "Dein letztes Training:",
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
        "rank_title": "🏆 Live-Rangliste (12 Stunden gültig!)",
        "rank_btn": "🔄 Tabelle aktualisieren",
        "rank_empty": "Keine Ergebnisse aus den letzten 12 Stunden für diesen Code. Sei der Erste!"
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
                
                # Przywracanie kopii zapasowej
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

# Nagłówek wspólny
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
    if st.button(T[lang]["finish"], type="primary", use_container_width=True):
        statystyki_koncowe = {"Punkty": total_points, "Max": max_total_score, "Skuteczność": percent, "Strzały": total_arrows_shot, "10_i_X": count_10_total, "X": count_x, "10": count_10_total, "9": scores.count("9"), "M": scores.count("M")}
        if zapisz_do_arkusza(st.session_state.event_info, statystyki_koncowe):
            kod_meczu = st.session_state.event_info.get("KodMeczu", "")
            if kod_meczu: zapisz_wynik_grupowy(st.session_state.zalogowany_zawodnik, kod_meczu, total_points, count_10_total, count_x)
            st.success("✅ Gespeichert!" if lang=="DE" else "✅ Zapisano!")
            time.sleep(1.5)
        reset()
        st.rerun()

# ---------------------------------------------------------------------
# NOWE MENU GŁÓWNE (DASHBOARD) - KIEDY NIE STRZELASZ
# ---------------------------------------------------------------------
else:
    tab_home, tab_score, tab_multi, tab_settings = st.tabs([
        T[lang]["menu_home"], T[lang]["menu_score"], T[lang]["menu_multi"], T[lang]["menu_settings"]
    ])

    # --- ZAKŁADKA: HOME ---
    with tab_home:
        st.markdown(f"### {T[lang]['home_welcome']}, {st.session_state.zalogowany_zawodnik}! 🎯")
        st.divider()
        st.write(f"**{T[lang]['home_last_training']}**")
        df_historia = pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
        
        if df_historia.empty:
            st.info(T[lang]["home_no_data"])
        else:
            ostatni = df_historia.iloc[-1]
            c1, c2, c3 = st.columns(3)
            c1.metric("Datum", ostatni['Data'])
            c2.metric("Distanz", ostatni['Dystans'])
            c3.metric("Punkte", f"{ostatni['Punkty']}")
            
            # Mini wykres skuteczności z ostatnich 5 treningów
            st.write("")
            ostatnie_5 = df_historia.tail(5).copy()
            ostatnie_5["Trening"] = range(1, len(ostatnie_5) + 1)
            chart = alt.Chart(ostatnie_5).mark_line(point=True, color='#2E8B57').encode(
                x=alt.X('Trening:O', axis=alt.Axis(labels=False, title='Letzte 5 Sessions')),
                y=alt.Y('Skuteczność %:Q', title='Trefferquote %', scale=alt.Scale(zero=False)),
                tooltip=['Data', 'Punkty', 'Dystans', 'Skuteczność %']
            ).properties(height=200)
            st.altair_chart(chart, use_container_width=True)
            
        st.write("")
        btn_wa_txt = "🟢 App über WhatsApp teilen" if lang == "DE" else "🟢 Udostępnij aplikację przez WhatsApp"
        st.markdown(f"""
            <div style='text-align: center; margin-top: 20px;'>
                <a href="whatsapp://send?text=Hallo! 👋 Schau dir unsere Vereins-App an: {ADRES_APLIKACJI}" target="_blank" style="text-decoration: none; background-color: #25D366; color: white; padding: 10px 20px; border-radius: 8px; font-weight: bold; font-size: 14px;">
                    {btn_wa_txt}
                </a>
            </div>
        """, unsafe_allow_html=True)

    # --- ZAKŁADKA: SCHIESSZETTEL ---
    with tab_score:
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
    with tab_multi:
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
                
        st.divider()
        st.markdown(f"### {T[lang]['rank_title']}")
        
        col_r1, col_r2 = st.columns([2,1])
        szukany_kod = col_r1.text_input("Szukaj Kodu", max_chars=2, key="search_code", placeholder="z.B. 12", label_visibility="collapsed")
        
        if col_r2.button(T[lang]["rank_btn"], type="secondary", use_container_width=True):
            if not szukany_kod: st.warning("Bitte gib den Raumcode ein!" if lang == "DE" else "Podaj kod pokoju!")
            else:
                df_rank = pobierz_ranking()
                if df_rank.empty: st.info(T[lang]["rank_empty"])
                else:
                    # LOGIKA 12 GODZIN!
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
                            c_bg = "#FFF9C4" if idx == 0 else "#f9f9f9" # Złoty kolor dla zwycięzcy
                            c_b = "#D4AC0D" if idx == 0 else "#ccc"
                            st.markdown(f"""
                            <div style='background-color: {c_bg}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 5px solid {c_b};'>
                                <h3 style='margin: 0; color: #333;'>{m} {row['Zawodnik']}</h3>
                                <p style='margin: 5px 0 0 0; font-size: 18px;'><b>{row['Punkty']}</b> Punkte &nbsp; <span style='font-size: 14px; color: gray;'>(10+X: {row['10_i_X']} | X: {row['Same X']})</span></p>
                                <p style='margin: 0; font-size: 10px; color: gray;'>Beendet: {row['Datetime'].strftime('%H:%M Uhr')}</p>
                            </div>
                            """, unsafe_allow_html=True)

    # --- ZAKŁADKA: EINSTELLUNGEN ---
    with tab_settings:
        st.write(f"**{T[lang]['lang_label']}**")
        st.radio("Język", ["DE", "PL"], index=0 if lang=="DE" else 1, horizontal=True, key="lang_sel", on_change=zmiana_jezyka, label_visibility="collapsed")
        st.divider()
        
        st.markdown(f"#### {T[lang]['bow_setup']}")
        c_bow1, c_bow2 = st.columns(2)
        c_bow1.text_input(T[lang]['draw_weight'], key="zuggewicht")
        c_bow2.text_input(T[lang]['brace_height'], key="standhoehe")
        c_bow1.text_input(T[lang]['tiller'], key="tiller")
        c_bow2.text_input(T[lang]['nock_point'], key="nockpunkt")
        
        st.write("")
        st.markdown(f"#### {T[lang]['arrows_setup']}")
        c_arr1, c_arr2 = st.columns(2)
        c_arr1.text_input(T[lang]['arr_model'], key="pfeil_modell")
        c_arr2.text_input(T[lang]['arr_spine'], key="pfeil_spine")
        c_arr1.text_input(T[lang]['arr_len'], key="pfeil_laenge")
        c_arr2.text_input(T[lang]['arr_point'], key="pfeil_spitze")
        
        st.write("")
        st.markdown(f"#### {T[lang]['visier']}")
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
