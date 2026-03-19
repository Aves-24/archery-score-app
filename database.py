import streamlit as st
import json
import time
from datetime import datetime, timedelta, date
import gspread
import pandas as pd
from config import NAZWA_ARKUSZA, dystanse_lista

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

def zapisz_do_arkusza(zawodnik, dane_treningu, statystyki):
    try:
        klucz_tekst = st.secrets["google_credentials"]
        gc = gspread.service_account_from_dict(json.loads(klucz_tekst))
        sh = gc.open(NAZWA_ARKUSZA)
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
