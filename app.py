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
            r_xs = round_scores.count("X")
            r_10s = round_scores.count("10") + r_xs
            r_9s = round_scores.count("9")
            r_max_current = len(round_scores) * 10
            r_percent = (r_points / r_max_current * 100) if r_max_current > 0 else 0
            
            html = f"<div style='margin-bottom: 20px; font-family: Arial, sans-serif; background-color: #ffffff; color: #000000; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>"
            html += f"<div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 5px;'><b>Runde {round_num}</b><span style='font-weight: bold;'>{info['Dystans']}</span></div>"
            html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black;'>"
            html += f"<tr style='background-color: #f2f2f2; color: #000000; border-bottom: 1px solid black;'><th rowspan='2' style='border: 1px solid black; border-right: 2px solid black; padding: 2px; width: 30px;'></th><th colspan='{arrows_per_end}' style='border: 1px solid black; padding: 2px; font-size: 14px;'>Pfeile</th><th colspan='2' style='border: 1px solid black; border-left: 2px solid black; padding: 2px; font-size: 14px;'>Summen</th></tr>"
            html += f"<tr style='background-color: #f2f2f2; color: #000000; border-bottom: 2px solid black;'>"
            for arr in range(1, arrows_per_end + 1):
                html += f"<th style='border: 1px solid black; padding: 2px; width: 30px; font-size: 12px;'>{arr}</th>"
            html += f"<th style='border: 1px solid black; border-left: 2px solid black; padding: 2px; font-size: 12px;'>Serie</th><th style='border: 1px solid black; padding: 2px; font-size: 12px;'>Übertrag</th></tr>"
            cumul_total = cumulative_start
            expected_ends = info['SeriiWRundzie']
            
            for end_idx in range(expected_ends):
                arrow_idx_start = end_idx * arrows_per_end
                end_scores = round_scores[arrow_idx_start:arrow_idx_start + arrows_per_end]
                if len(end_scores) > 0:
                    end_sum = sum(get_num(s) for s in end_scores)
                    cumul_total += end_sum
                else: end_sum = ""
                    
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
            html += f"<table style='width: 100%; border-collapse: collapse; text-align: center; border: 2px solid black; border-top: none; color: #000;'><tr>"
            html += f"<td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%;'>Xer:<br><b style='font-size: 14px;'>{r_xs}</b></td>"
            html += f"<td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%;'>10er:<br><b style='font-size: 14px;'>{r_10s}</b></td>"
            html += f"<td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%;'>9er:<br><b style='font-size: 14px;'>{r_9s}</b></td>"
            html += f"<td style='border: 1px solid black; padding: 4px; font-size: 12px; width: 25%; background-color: #f0f8ff;'>%:<br><b style='font-size: 14px;'>{r_percent:.1f}%</b></td>"
            html += f"</tr></table></div>"
            return html, cumul_total

        round1_scores = scores[:st.session_state.max_arrows_per_round]
        round2_scores = scores[st.session_state.max_arrows_per_round:]

        if len(round2_scores) == 0:
            if len(round1_scores) > 0 or not st.session_state.started:
                html1, cumul1 = render_round_html(1, round1_scores, 0)
                st.markdown(html1, unsafe_allow_html=True)
        else:
            html1, cumul1 = render_round_html(1, round1_scores, 0)
            with st.expander(T[lang]["round_fin"], expanded=False):
                st.markdown(html1, unsafe_allow_html=True)
            html2, _ = render_round_html(2, round2_scores, cumul1)
            st.markdown(html2, unsafe_allow_html=True)

        # --- STATYSTYKI KOŃCOWE ---
        total_points = sum(get_num(s) for s in scores)
        percent = (total_points / (len(scores) * 10) * 100) if len(scores) > 0 else 0
        total_arrows_shot = len(scores) + st.session_state.extra_arrows
        
        count_x = scores.count("X")
        count_10_czyste = scores.count("10")
        count_10_total = count_10_czyste + count_x 
        count_9 = scores.count("9")
        count_m = scores.count("M")
        
        st.markdown(T[lang]["total_score"])
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric(T[lang]["pts"], f"{total_points} / {max_total_score}")
        col_s2.metric(T[lang]["arrow_cnt"], f"{total_arrows_shot}")
        col_s3.metric(T[lang]["eff"], f"{percent:.1f}%")
        
        st.write(f"**{T[lang]['sum_10_x']}** {count_10_total} &nbsp;&nbsp;|&nbsp;&nbsp; **{T[lang]['only_x']}** {count_x}")
        st.write("")
        
        st.markdown(f"<span style='font-size:14px; color:gray;'>{T[lang]['warmup']}</span>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.button(T[lang]["add_6"], on_click=add_extra_arrows, args=(6,), use_container_width=True)
        c2.button(T[lang]["add_1"], on_click=add_extra_arrows, args=(1,), use_container_width=True)
        c3.button(T[lang]["undo"], on_click=add_extra_arrows, args=(-1,), use_container_width=True)

        st.write("")

        if st.button(T[lang]["finish"], type="primary", use_container_width=True):
            statystyki_koncowe = {
                "Punkty": total_points,
                "Max": max_total_score,
                "Skuteczność": percent,
                "Strzały": total_arrows_shot,
                "10_i_X": count_10_total, 
                "X": count_x,
                "10": count_10_total, 
                "9": count_9,
                "M": count_m
            }
            
            sukces = zapisz_do_arkusza(st.session_state.event_info, statystyki_koncowe)
            if sukces:
                st.success("✅ Zapisano!" if lang=="PL" else "✅ Gespeichert!")
                time.sleep(1.5)
            else:
                st.error("❌ Błąd!" if lang=="PL" else "❌ Fehler!")
                time.sleep(3)
            
            reset()
            st.rerun()

# --- ZAKŁADKA STATYSTYK ---
with tab_staty:
    st.markdown("""
    <style>
    div[data-testid="stVegaLiteChart"] {
        width: 100%;
        overflow-x: auto;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Wywołuje pobieranie danych TYLKO dla osoby zalogowanej
    df = pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
    
    if df.empty:
        st.info("Brak połączonego arkusza lub arkusz jest pusty." if lang=="PL" else "Keine Daten oder Sheet ist leer.")
    else:
        st.write(f"**{T[lang]['choose_dist']}**")
        wybrany_dystans = st.radio("Dystans stat", dystanse_lista, horizontal=True, label_visibility="collapsed")
        
        df_filtrowane = df[df["Dystans"] == wybrany_dystans]
        
        if df_filtrowane.empty:
            st.warning(T[lang]["stat_no_data"])
        else:
            st.divider()
            
            st.write(f"**{T[lang]['stat_metric']}**")
            
            opcje_metryk = {
                "Punkty": "Punkty", 
                "Same X": "Same X", 
                "Wszystkie 10": "10", 
                "9": "9", 
                "M (Pudła)": "M", 
                "Strzały (Suma)": "Strzały (Suma)"
            } if lang == "PL" else {
                "Punkte": "Punkty", 
                "Nur X": "Same X", 
                "Alle 10er": "10", 
                "9er": "9", 
                "M (Fehler)": "M", 
                "Pfeile (Summe)": "Strzały (Suma)"
            }
            
            wybrana_metryka_klucz = st.radio("Metryka", list(opcje_metryk.keys()), horizontal=True, label_visibility="collapsed")
            kolumna_y = opcje_metryk[wybrana_metryka_klucz]
            
            df_filtrowane = df_filtrowane.copy() 
            df_filtrowane["Sesja"] = df_filtrowane["Data"] + " (" + df_filtrowane["Czas"].astype(str).str[:5] + ")"
            
            df_filtrowane["Wydarzenie"] = df_filtrowane.apply(
                lambda row: f"{row['Typ']} - {row['Nazwa']}" if row['Nazwa'] != "-" else row['Typ'], axis=1
            )
            
            df_filtrowane['Typ'] = df_filtrowane['Typ'].replace({
                T["PL"]["training"]: T[lang]["training"],
                T["DE"]["training"]: T[lang]["training"],
                T["PL"]["tournament"]: T[lang]["tournament"],
                T["DE"]["tournament"]: T[lang]["tournament"]
            })
            
            domena_typow = [T[lang]["training"], T[lang]["tournament"]]
            zakres_kolorow = ['#2E8B57', '#1E88E5']
            kolory = alt.Scale(domain=domena_typow, range=zakres_kolorow)
            
            max_wartosc = df_filtrowane[kolumna_y].max()
            if kolumna_y == "Punkty":
                skala_y = alt.Scale(domain=[0, 720], nice=False) 
            else:
                skala_y = alt.Scale(domain=[0, max_wartosc * 1.25 if max_wartosc > 0 else 10], nice=False)
            
            baza = alt.Chart(df_filtrowane).encode(
                x=alt.X('Sesja:N', title='Data', sort=None, axis=alt.Axis(labelAngle=-45))
            )
            
            if lang == "PL":
                tt_punkty = "🎯 Punkty"
                tt_x = "🟡 Same X"
                tt_10 = "🔟 Wszystkie 10"
                tt_9 = "9️⃣ Dziewiątki"
                tt_m = "Ⓜ️ Pudła (M)"
                tt_wydarzenie = "🏹 Wydarzenie"
                tt_strzaly = "🎯 Ilość strzał"
                tt_data = "📅 Data"
                tt_czas = "⏰ Godzina"
            else:
                tt_punkty = "🎯 Punkte"
                tt_x = "🟡 Nur X"
                tt_10 = "🔟 Alle 10er"
                tt_9 = "9️⃣ 9er"
                tt_m = "Ⓜ️ Fehler (M)"
                tt_wydarzenie = "🏹 Ereignis"
                tt_strzaly = "🎯 Pfeilanzahl"
                tt_data = "📅 Datum"
                tt_czas = "⏰ Uhrzeit"

            narzedzia = [
                alt.Tooltip('Punkty:Q', title=tt_punkty),
                alt.Tooltip('Wydarzenie:N', title=tt_wydarzenie),
                alt.Tooltip('Strzały (Suma):Q', title=tt_strzaly),
                alt.Tooltip('Same X:Q', title=tt_x),
                alt.Tooltip('10:Q', title=tt_10),
                alt.Tooltip('9:Q', title=tt_9),
                alt.Tooltip('M:Q', title=tt_m),
                alt.Tooltip('Data:N', title=tt_data),
                alt.Tooltip('Czas:N', title=tt_czas)
            ]
            
            slupki = baza.mark_bar(opacity=0.9, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                y=alt.Y(f'{kolumna_y}:Q', title=wybrana_metryka_klucz, scale=skala_y), 
                color=alt.Color('Typ:N', scale=kolory, legend=alt.Legend(title="Typ", orient="bottom")),
                tooltip=narzedzia 
            )
            
            teksty = baza.mark_text(
                align='center',
                baseline='bottom',
                dy=-5, 
                fontWeight='bold',
                fontSize=12,
                clip=False 
            ).encode(
                y=alt.Y(f'{kolumna_y}:Q'),
                text=alt.Text(f'{kolumna_y}:Q') 
            )
            
            szerokosc_wykresu = max(350, len(df_filtrowane) * 45)
            
            wykres = (slupki + teksty).properties(
                width=szerokosc_wykresu,
                height=350
            )
            
            st.altair_chart(wykres, use_container_width=False)

# --- PRZYCISK UDOSTĘPNIANIA WHATSAPP NA DOLE STRONY ---
st.write("")
st.divider()
wiadomosc = f"Hej! 👋 Zobacz naszą nową klubową aplikację do punktacji łuczniczej: {ADRES_APLIKACJI}"
st.markdown(f"""
    <div style='text-align: center; margin-bottom: 20px;'>
        <a href="whatsapp://send?text={wiadomosc}" target="_blank" style="text-decoration: none; background-color: #25D366; color: white; padding: 12px 24px; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            🟢 Udostępnij aplikację przez WhatsApp
        </a>
    </div>
""", unsafe_allow_html=True)
