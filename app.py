import streamlit as st
import json
import os
import time
from datetime import datetime, date, timedelta
import pandas as pd
import altair as alt
import urllib.parse
from streamlit_option_menu import option_menu

# --- IMPORTY Z NASZYCH NOWYCH PLIKÓW ---
from config import NAZWA_ARKUSZA, ADRES_APLIKACJI, KOD_KLUBU, dystanse_lista, T
import database as db
import pro_features as pro 

st.set_page_config(page_title="SFT Schießzettel", layout="centered", initial_sidebar_state="collapsed")

# --- UKRYCIE INTERFEJSU STREAMLIT I SNAJPERSKI CSS DLA PRZYCISKÓW ---
st.markdown("""
    <style>
        header {visibility: hidden;}
        footer {visibility: hidden;}
        
        .block-container {
            padding-top: 1rem;
            /* Ogromny margines na dole zabezpiecza przed paskami nawigacji w smartfonach! */
            padding-bottom: 4rem !important; 
            max-width: 100% !important;
            overflow-x: hidden !important; 
        }
        .stDeployButton {display:none;}
        
        /* SNAJPERSKI CSS: Celuje TYLKO w bloki, które mają DOKŁADNIE 3 kolumny i zawierają przyciski */
        @media screen and (max-width: 768px) {
            div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3):last-child):has(.stButton) {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                width: 100% !important;
                gap: 4px !important; 
            }
            div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3):last-child):has(.stButton) > div[data-testid="column"] {
                width: 0 !important; 
                min-width: 0 !important;
                flex: 1 1 0% !important; 
                padding: 0 !important;
            }
            div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3):last-child):has(.stButton) .stButton {
                width: 100% !important;
            }
            div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3):last-child):has(.stButton) .stButton > button {
                width: 100% !important;
                padding: 0 !important;
                min-height: 44px !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }
            div[data-testid="stHorizontalBlock"]:has(> div[data-testid="column"]:nth-child(3):last-child):has(.stButton) .stButton > button p {
                font-size: 13px !important;
                margin: 0 !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: clip !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# --- INICJALIZACJA SESJI ---
if 'lang' not in st.session_state: st.session_state.lang = "DE" 
if 'zalogowany_zawodnik' not in st.session_state: st.session_state.zalogowany_zawodnik = None
if 'aktywne_dystanse' not in st.session_state: st.session_state.aktywne_dystanse = ["18m", "30m", "70m"]
if 'ostatni_kod' not in st.session_state: st.session_state.ostatni_kod = "" 
if 'started' not in st.session_state: 
    st.session_state.started = False
    st.session_state.scores = []
    st.session_state.extra_arrows = 0
    st.session_state.event_info = {} 
    st.session_state.pogoda_txt = ""
    st.session_state.pogoda_r2_pobrana = False

lang = st.session_state.lang

# --- FUNKCJE POMOCNICZE (LOKALNE) ---
def get_autosave_file(): return f"autosave_{st.session_state.zalogowany_zawodnik}.json"

def save_user_settings():
    if st.session_state.zalogowany_zawodnik:
        with open(f"settings_{st.session_state.zalogowany_zawodnik}.json", "w") as f:
            json.dump({
                "aktywne_dystanse": st.session_state.aktywne_dystanse, 
                "lang": st.session_state.lang,
                "ostatni_kod": st.session_state.ostatni_kod
            }, f)

def load_user_settings(zawodnik):
    plik = f"settings_{zawodnik}.json"
    if os.path.exists(plik):
        try:
            with open(plik, "r") as f:
                data = json.load(f)
                st.session_state.aktywne_dystanse = data.get("aktywne_dystanse", ["18m", "30m", "70m"])
                st.session_state.lang = data.get("lang", "DE") 
                st.session_state.ostatni_kod = data.get("ostatni_kod", "")
        except: pass

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
                    st.session_state.pogoda_txt = pro.pobierz_pogode() 
        except: pass
    
    zapisane_dane = db.pobierz_profil_sprzetu(czysta_nazwa)
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
    st.session_state.event_info = {}
    st.session_state.pogoda_txt = ""
    st.session_state.pogoda_r2_pobrana = False
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

# --- SPRAWDZENIE AKCJI W URL ---
if "del" in st.query_params:
    db.usun_kalendarz_osobisty(st.query_params["del"])
    del st.query_params["del"] 
    st.rerun()

if not st.session_state.zalogowany_zawodnik and "u" in st.query_params:
    wykonaj_logowanie(st.query_params["u"])

has_paused_session = bool(st.session_state.get('event_info', {}))

# --- INICJALIZACJA ZMIENNYCH SPRZĘTU (ZABEZPIECZENIE) ---
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
    konta = db.pobierz_uzytkownikow()
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
            elif db.dodaj_uzytkownika(nowy_zawodnik.strip(), nowy_pin):
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

    def get_num(s): return 10 if s in ["X", "10"] else (0 if s == "M" else int(s))

    info = st.session_state.event_info
    scores = st.session_state.scores
    arrows_per_end = info['StrzalWSerii']
    max_total_score = st.session_state.max_total_arrows * 10
    
    # --- AUTOMATYCZNY ZAPIS POŁOWY TURNIEJU I POGODA ---
    if len(scores) >= st.session_state.max_arrows_per_round and not st.session_state.pogoda_r2_pobrana:
        st.session_state.pogoda_txt = pro.pobierz_pogode()
        st.session_state.pogoda_r2_pobrana = True
        
        kod_meczu = info.get("KodMeczu", "")
        if kod_meczu:
            punkty_r1 = sum(get_num(s) for s in scores[:st.session_state.max_arrows_per_round])
            x_r1 = scores[:st.session_state.max_arrows_per_round].count("X")
            x10_r1 = scores[:st.session_state.max_arrows_per_round].count("10") + x_r1
            db.zapisz_wynik_grupowy(f"{st.session_state.zalogowany_zawodnik} (1/2)", kod_meczu, punkty_r1, x10_r1, x_r1)
    
    tytul = f"{info['Typ']}" + (f" - {info['Nazwa']}" if info['Nazwa'] != "-" else "")
    if info.get('KodMeczu', ""): tytul += f" [⚔️ {info['KodMeczu']}]"
    
    st.markdown(f"<div style='text-align: center; color: gray; font-size: 14px; margin-bottom: 5px;'>{tytul} | {info['Dystans']} <br> {st.session_state.pogoda_txt}</div>", unsafe_allow_html=True)

    with st.expander("⏱️ Timer / Stoppuhr"):
        pro.render_stopwatch(lang)

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

    # OBLICZENIA DO PODSUMOWANIA
    total_points = sum(get_num(s) for s in scores)
    percent = (total_points / (len(scores) * 10) * 100) if len(scores) > 0 else 0
    total_arrows_shot = len(scores) + st.session_state.extra_arrows
    count_x = scores.count("X")
    count_10 = scores.count("10")
    count_9 = scores.count("9")
    count_m = scores.count("M")
    count_10_total = count_10 + count_x 

    st.markdown(f"""
    <div style='background-color: #f9f9f9; padding: 15px; border-radius: 8px; border-left: 5px solid #2E8B57; border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
        <p style='margin: 0 0 10px 0; font-size: 16px; font-weight: bold;'>📊 {T[lang]['total_score']}</p>
        <div style='display: flex; justify-content: space-between; text-align: center; border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 10px;'>
            <div><span style='font-size: 12px; color: gray;'>{T[lang]['pts']}</span><br><b style='font-size: 18px;'>{total_points}</b><span style='font-size:12px; color:gray;'>/{max_total_score}</span></div>
            <div><span style='font-size: 12px; color: gray;'>{T[lang]['arrow_cnt']}</span><br><b style='font-size: 18px;'>{total_arrows_shot}</b></div>
            <div><span style='font-size: 12px; color: gray;'>{T[lang]['eff']}</span><br><b style='font-size: 18px; color: #2E8B57;'>{percent:.1f}%</b></div>
        </div>
        <div style='display: flex; justify-content: space-around; text-align: center;'>
            <div><b style='color: #D4AC0D; font-size: 14px;'>X</b><br><span style='font-size: 16px; font-weight: bold;'>{count_x}</span></div>
            <div><b style='color: #D4AC0D; font-size: 14px;'>10</b><br><span style='font-size: 16px; font-weight: bold;'>{count_10}</span></div>
            <div><b style='color: #FBC02D; font-size: 14px;'>9</b><br><span style='font-size: 16px; font-weight: bold;'>{count_9}</span></div>
            <div><b style='color: gray; font-size: 14px;'>M</b><br><span style='font-size: 16px; font-weight: bold;'>{count_m}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    wykres = pro.wykres_zmeczenia(scores, lang)
    if wykres is not None:
        st.altair_chart(wykres, use_container_width=True)

    st.markdown(f"<div style='font-size:13px; color:gray; margin-bottom: 2px; margin-top: 5px; text-align: center; font-weight: bold;'>{T[lang]['warmup']}</div>", unsafe_allow_html=True)
    cw1, cw2, cw3 = st.columns(3)
    cw1.button(T[lang]["add_6"], on_click=add_extra_arrows, args=(6,), use_container_width=True)
    cw2.button(T[lang]["add_1"], on_click=add_extra_arrows, args=(1,), use_container_width=True)
    cw3.button(T[lang]["undo"], on_click=add_extra_arrows, args=(-1,), use_container_width=True)

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    c_save, c_pause, c_cancel = st.columns(3)
    if c_save.button(T[lang]["finish"], type="primary", use_container_width=True):
        statystyki_koncowe = {"Punkty": total_points, "Max": max_total_score, "Skuteczność": percent, "Strzały": total_arrows_shot, "10_i_X": count_10_total, "X": count_x, "10": count_10_total, "9": count_9, "M": count_m}
        if db.zapisz_do_arkusza(st.session_state.zalogowany_zawodnik, st.session_state.event_info, statystyki_koncowe):
            kod_meczu = st.session_state.event_info.get("KodMeczu", "")
            if kod_meczu: db.zapisz_wynik_grupowy(st.session_state.zalogowany_zawodnik, kod_meczu, total_points, count_10_total, count_x)
            st.success("✅ Gespeichert!" if lang=="DE" else "✅ Zapisano!")
            time.sleep(1.5)
        reset()
        st.rerun()
        
    if c_pause.button(T[lang]["pause_btn"], use_container_width=True):
        st.session_state.started = False 
        st.rerun()
        
    if c_cancel.button(T[lang]["cancel_btn"], use_container_width=True):
        reset()
        st.rerun()

    # --- TABELA RANKINGOWA W TRAKCIE TURNIEJU (PO POŁOWIE) ---
    kod_meczu = info.get("KodMeczu", "")
    if kod_meczu and len(scores) >= st.session_state.max_arrows_per_round:
        st.write("")
        tytul_rank = "🏆 Zwischenstand (Halbzeit)" if lang == "DE" else "🏆 Wyniki na półmetku"
        with st.expander(tytul_rank, expanded=True):
            if st.button("🔄 Refresh", use_container_width=True, key="ref_halbzeit"):
                db.pobierz_ranking.clear() 
            
            df_rank = db.pobierz_ranking()
            if df_rank.empty: 
                st.info(T[lang]["rank_empty"])
            else:
                df_rank["Datetime"] = pd.to_datetime(df_rank["DataCzas"], format="%Y-%m-%d %H:%M:%S", errors='coerce')
                df_rank = df_rank.dropna(subset=['Datetime'])
                limit_czasu = datetime.now() - timedelta(hours=12)
                
                df_filtrowane = df_rank[(df_rank["Datetime"] >= limit_czasu) & (df_rank["Kod"].astype(str) == str(kod_meczu))]
                
                if df_filtrowane.empty: 
                    st.info(T[lang]["rank_empty"])
                else:
                    df_filtrowane["Punkty"] = pd.to_numeric(df_filtrowane["Punkty"])
                    df_filtrowane["10_i_X"] = pd.to_numeric(df_filtrowane["10_i_X"])
                    df_filtrowane["Same X"] = pd.to_numeric(df_filtrowane["Same X"])
                    df_filtrowane = df_filtrowane.sort_values(by=["Punkty", "10_i_X", "Same X"], ascending=[False, False, False]).reset_index(drop=True)
                    
                    for idx, row in df_filtrowane.iterrows():
                        m = "🥇" if idx == 0 else ("🥈" if idx == 1 else ("🥉" if idx == 2 else f"**{idx+1}.**"))
                        c_bg = "#FFF9C4" if idx == 0 else "#f9f9f9" 
                        c_b = "#D4AC0D" if idx == 0 else "#ccc"
                        st.markdown(f"""
                        <div style='background-color: {c_bg}; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid {c_b};'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <h4 style='margin: 0; color: #333; font-size: 15px;'>{m} {row['Zawodnik']}</h4>
                                <b style='font-size: 16px;'>{row['Punkty']} <span style='font-size:12px; font-weight:normal; color:gray;'>pts</span></b>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

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
                "container": {"padding": "5px !important", "background-color": "#ffffff", "border": "1px solid #ddd", "border-radius": "10px", "margin-bottom": "20px"},
                "icon": {"color": "#D4AC0D", "font-size": "15px"}, 
                "nav-link": {"font-size": "12px", "text-align": "center", "margin":"2px", "padding": "10px 5px", "--hover-color": "#f4f4f4"},
                "nav-link-selected": {"background-color": "#2E8B57", "font-weight": "bold", "color": "white"},
            }
        )

    # --- ZAKŁADKA: HOME ---
    if wybrana_zakladka == T[lang]["menu_home"]:
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 18px; font-weight: bold;'>🏠 {T[lang]['home_welcome']}, {st.session_state.zalogowany_zawodnik}! 🎯</p></div>", unsafe_allow_html=True)
        
        df_historia = db.pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
        
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
        df_my_cal = db.pobierz_kalendarz_osobisty(st.session_state.zalogowany_zawodnik)
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
            if c_r.button(T[lang]["resume_btn"], type="primary"):
                st.session_state.started = True
                st.rerun()
            if c_d.button(T[lang]["discard_btn"]):
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
                st.session_state.pogoda_txt = pro.pobierz_pogode() 
                st.session_state.pogoda_r2_pobrana = False
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
            if c_rm.button(T[lang]["resume_btn"], type="primary", key="res_multi"):
                st.session_state.started = True
                st.rerun()
            if c_dm.button(T[lang]["discard_btn"], key="disc_multi"):
                reset()
                st.rerun()
        else:
            st.write(f"**{T[lang]['room_code']}**")
            kod_meczu = st.text_input("Kod Pokoju", max_chars=2, placeholder="np. 07", label_visibility="collapsed")
            
            st.write(T[lang]["choose_dist"])
            dystans_multi = st.radio("Dystans Multi", st.session_state.aktywne_dystanse, horizontal=True, label_visibility="collapsed")

            st.write("")
            if st.button(T[lang]["start_multi_btn"], type="primary", use_container_width=True):
                if not kod_meczu.strip(): 
                    st.error("Bitte gib einen Code ein!" if lang == "DE" else "Podaj kod!")
                else:
                    df_rank = db.pobierz_ranking()
                    juz_gral = False
                    if not df_rank.empty:
                        df_rank["Datetime"] = pd.to_datetime(df_rank["DataCzas"], format="%Y-%m-%d %H:%M:%S", errors='coerce')
                        limit_czasu = datetime.now() - timedelta(hours=12)
                        df_filtrowane = df_rank[(df_rank["Datetime"] >= limit_czasu) & (df_rank["Kod"].astype(str) == str(kod_meczu.strip())) & (df_rank["Zawodnik"] == st.session_state.zalogowany_zawodnik)]
                        if not df_filtrowane.empty:
                            juz_gral = True
                            
                    if juz_gral:
                        st.error("❌ Już brałeś udział w tym pokoju!" if lang == "PL" else "❌ Du hast an diesem Raum bereits teilgenommen!")
                    else:
                        st.session_state.ostatni_kod = kod_meczu.strip()
                        save_user_settings() 
                        
                        czesci = []
                        if st.session_state[f'aus_{dystans_multi}']: czesci.append(f"A:{st.session_state[f'aus_{dystans_multi}']}")
                        if st.session_state[f'hoehe_{dystans_multi}']: czesci.append(f"H:{st.session_state[f'hoehe_{dystans_multi}']}")
                        if st.session_state[f'seite_{dystans_multi}']: czesci.append(f"S:{st.session_state[f'seite_{dystans_multi}']}")
                        
                        st.session_state.event_info = {
                            "Data": date.today().strftime("%d.%m.%Y"), "Typ": T[lang]["training"], "Nazwa": "Mini-Turnier",
                            "StrzalWSerii": 6, "SeriiWRundzie": 6, "Dystans": dystans_multi, "KodMeczu": kod_meczu.strip(),
                            "CelownikSkala": " | ".join(czesci) if czesci else "-"
                        }
                        st.session_state.pogoda_txt = pro.pobierz_pogode() 
                        st.session_state.pogoda_r2_pobrana = False
                        st.session_state.max_arrows_per_round = 36
                        st.session_state.max_total_arrows = 72
                        st.session_state.started = True
                        save_backup()
                        st.rerun()
                
        st.write("")
        st.markdown(f"<div style='background-color: #f9f9f9; padding: 10px 15px; border-radius: 8px; border-left: 5px solid #2E8B57; margin-bottom: 15px;'><p style='margin: 0; font-size: 16px; font-weight: bold;'>{T[lang]['rank_title']}</p></div>", unsafe_allow_html=True)
        
        col_r1, col_r2 = st.columns([2,1])
        szukany_kod = col_r1.text_input("Szukaj Kodu", max_chars=2, value=st.session_state.ostatni_kod, key="search_code", placeholder="z.B. 12", label_visibility="collapsed")
        
        if col_r2.button(T[lang]["rank_btn"], type="secondary", use_container_width=True):
            if not szukany_kod: st.warning("Bitte gib den Raumcode ein!" if lang == "DE" else "Podaj kod pokoju!")
            else:
                df_rank = db.pobierz_ranking()
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
        
        df = db.pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
        
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
                        db.dodaj_kalendarz_osobisty(st.session_state.zalogowany_zawodnik, nowa_data, nowa_nazwa, nowy_adres, "")
                        st.rerun()
                    else:
                        st.error("Podaj nazwę!" if lang == "PL" else "Bitte Namen eingeben!")
                        
            df_my_cal = db.pobierz_kalendarz_osobisty(st.session_state.zalogowany_zawodnik)
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
                        adres_html = f"<br><span style='font-size: 13px; color: gray;'>🏠 {adres_text}</span> <a href='{maps_url}' target='_blank' style='display: inline-block; margin-left: 8px; background-color: #e3f2fd; border: 1px solid #bbdefb; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>📍</a>"
                        
                    del_link = f"?u={urllib.parse.quote(st.session_state.zalogowany_zawodnik)}&del={row['ID']}"
                    trash_btn = f"<a href='{del_link}' target='_self' style='text-decoration: none; display: flex; justify-content: center; align-items: center; width: 44px; height: 44px; background-color: #fff; border: 1px solid #ffcdd2; color: #d32f2f; border-radius: 8px; font-size: 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); transition: 0.2s;'>🗑️</a>"
                    
                    st.markdown(f"""
                    <div style='background-color: #ffffff; border: 1px solid #eee; padding: 12px; border-radius: 8px; border-left: 5px solid #1E88E5; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div style='flex-grow: 1; padding-right: 10px;'>
                                <b style='color: #1E88E5; font-size: 14px;'>🗓️ {row['Data']}</b><br>
                                <span style='font-size: 15px; font-weight: 500; color: #333;'>{row['Nazwa']}</span>
                                {adres_html}
                            </div>
                            <div>
                                {trash_btn}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        with tab_diary:
            df_hist = db.pobierz_dane_z_arkusza(st.session_state.zalogowany_zawodnik)
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
        
        for d in dystanse_lista:
            c1, c2, c3, c4 = st.columns([0.8, 1, 1, 1])
            c1.checkbox(d, value=(d in st.session_state.aktywne_dystanse), key=f"chk_{d}", on_change=zmiana_dystansow)
            c2.text_input(f"Aus {d}", placeholder=st.session_state[f"aus_{d}"] or "Ausleger", key=f"ui_aus_{d}", label_visibility="collapsed")
            c3.text_input(f"Höhe {d}", placeholder=st.session_state[f"hoehe_{d}"] or "Höhe", key=f"ui_hoehe_{d}", label_visibility="collapsed")
            c4.text_input(f"Seite {d}", placeholder=st.session_state[f"seite_{d}"] or "Seite", key=f"ui_seite_{d}", label_visibility="collapsed")
        
        st.write("")
        if st.button("💾 Profil in der Cloud speichern" if lang == "DE" else "💾 Zapisz profil w chmurze", use_container_width=True):
            dane_sprzetu = {"zuggewicht": st.session_state["zuggewicht"], "standhoehe": st.session_state["standhoehe"], "tiller": st.session_state["tiller"], "nockpunkt": st.session_state["nockpunkt"], "pfeil_modell": st.session_state["pfeil_modell"], "pfeil_spine": st.session_state["pfeil_spine"], "pfeil_laenge": st.session_state["pfeil_laenge"], "pfeil_spitze": st.session_state["pfeil_spitze"]}
            for d in dystanse_lista:
                for k in ["aus", "hoehe", "seite"]:
                    nw = st.session_state[f"ui_{k}_{d}"].strip()
                    if nw: st.session_state[f"{k}_{d}"] = nw
                    dane_sprzetu[f"{k}_{d}"] = st.session_state[f"{k}_{d}"]
                
            if db.zapisz_profil_sprzetu(st.session_state.zalogowany_zawodnik, dane_sprzetu):
                st.success("✅ Gespeichert!" if lang=="DE" else "✅ Zapisano!")
                time.sleep(1)
                st.rerun()
                
        st.write("")
        if st.button("🚪 Abmelden / Logout" if lang == "DE" else "🚪 Wyloguj / Logout", use_container_width=True): wyloguj()
