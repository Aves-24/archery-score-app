import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import altair as alt
import requests

# ==========================================
# 1. PROFESJONALNY STOPER ŁUCZNICZY (JS)
# ==========================================
def render_stopwatch(lang="DE"):
    txt_prep = "Przygotowanie" if lang == "PL" else "Vorbereitung"
    txt_shoot = "Strzelanie" if lang == "PL" else "Schießen"
    txt_end = "Koniec Czasu!" if lang == "PL" else "Zeit abgelaufen!"
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            text-align: center; 
            margin: 0; 
            padding: 10px; 
            background-color: transparent;
        }}
        #timer_box {{
            padding: 20px;
            border-radius: 15px;
            border: 3px solid #ddd;
            background-color: #f9f9f9;
            transition: background-color 0.5s, color 0.5s;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        #status {{ font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; color: #333; }}
        #time {{ font-size: 70px; font-weight: 900; margin: 0; line-height: 1; }}
        .btn-row {{ margin-top: 15px; display: flex; justify-content: center; gap: 10px; }}
        button {{
            font-size: 16px; padding: 12px 20px; cursor: pointer; border-radius: 8px; 
            border: none; background-color: #1E88E5; color: white; font-weight: bold; width: 100%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        button:active {{ transform: scale(0.95); }}
        #btn_stop {{ background-color: #E53935; }}
        
        /* KOLORY FAZ TURNIEJOWYCH */
        .phase-prep {{ background-color: #FFEB3B !important; color: #000 !important; border-color: #FBC02D !important; }}
        .phase-shoot {{ background-color: #4CAF50 !important; color: #fff !important; border-color: #388E3C !important; }}
        .phase-warn {{ background-color: #FFC107 !important; color: #000 !important; border-color: #FFA000 !important; }}
        .phase-end {{ background-color: #F44336 !important; color: #fff !important; border-color: #D32F2F !important; }}
    </style>
    </head>
    <body>
        <div id="timer_box">
            <div id="status">TIMER</div>
            <div id="time">00:00</div>
            <div class="btn-row">
                <button onclick="startTimer(120)">120s (3 🏹)</button>
                <button onclick="startTimer(240)">240s (6 🏹)</button>
                <button id="btn_stop" onclick="stopTimer()">STOP</button>
            </div>
        </div>

        <script>
            let timerInterval;
            let phase = 0; // 0=idle, 1=prep, 2=shoot
            let timeLeft = 0;
            let wakeLock = null;

            const timeDisplay = document.getElementById('time');
            const statusDisplay = document.getElementById('status');
            const timerBox = document.getElementById('timer_box');

            // Magia zapobiegająca wyłączaniu ekranu w telefonie!
            async function requestWakeLock() {{
                try {{
                    if ('wakeLock' in navigator) {{
                        wakeLock = await navigator.wakeLock.request('screen');
                    }}
                }} catch (err) {{ console.log(err); }}
            }}

            function releaseWakeLock() {{
                if (wakeLock !== null) {{
                    wakeLock.release().then(() => {{ wakeLock = null; }});
                }}
            }}

            function startTimer(shootSeconds) {{
                stopTimer();
                requestWakeLock();
                phase = 1;
                timeLeft = 10; // 10 sekund przygotowania
                updateUI(shootSeconds);
                
                timerInterval = setInterval(() => {{
                    timeLeft--;
                    if (timeLeft <= 0) {{
                        if (phase === 1) {{
                            phase = 2; // Przejście do strzelania
                            timeLeft = shootSeconds;
                        }} else if (phase === 2) {{
                            phase = 0; // Koniec
                            clearInterval(timerInterval);
                            releaseWakeLock();
                        }}
                    }}
                    updateUI(shootSeconds);
                }}, 1000);
            }}

            function stopTimer() {{
                clearInterval(timerInterval);
                phase = 0;
                timeLeft = 0;
                updateUI(0);
                releaseWakeLock();
            }}

            function updateUI(totalShootTime) {{
                let m = Math.floor(timeLeft / 60).toString().padStart(2, '0');
                let s = (timeLeft % 60).toString().padStart(2, '0');
                timeDisplay.innerText = `${{m}}:${{s}}`;

                timerBox.className = ''; // Reset kolorów
                
                if (phase === 0) {{
                    if (timeDisplay.innerText === "00:00" && totalShootTime > 0) {{
                         statusDisplay.innerText = "{txt_end}";
                         timerBox.classList.add('phase-end');
                    }} else {{
                         statusDisplay.innerText = "READY";
                         timeDisplay.innerText = "00:00";
                         statusDisplay.style.color = "#333";
                    }}
                }} else if (phase === 1) {{
                    statusDisplay.innerText = "{txt_prep}";
                    timerBox.classList.add('phase-prep');
                }} else if (phase === 2) {{
                    if (timeLeft <= 10) {{
                        statusDisplay.innerText = "{txt_shoot} (10s!)";
                        timerBox.classList.add('phase-warn');
                    }} else {{
                        statusDisplay.innerText = "{txt_shoot}";
                        timerBox.classList.add('phase-shoot');
                    }}
                }}
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=230)

# ==========================================
# 2. POBIERANIE POGODY (Open-Meteo API)
# ==========================================
def pobierz_pogode():
    try:
        # Pobieramy pogodę dla centralnej Europy (Niemcy) jako domyślną
        res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=51.33&longitude=6.34&current_weather=true", timeout=2)
        dane = res.json()
        temp = dane['current_weather']['temperature']
        wiatr = dane['current_weather']['windspeed']
        return f"⛅ {temp}°C | 💨 {wiatr} km/h"
    except:
        return "⛅ Pogoda niedostępna"

# ==========================================
# 3. ANALIZA ZMĘCZENIA (Runda 1 vs Runda 2)
# ==========================================
def wykres_zmeczenia(scores, lang="DE"):
    if len(scores) < 6: # Rysuj tylko jeśli oddano przynajmniej jedną serię
        return None
        
    def get_val(s): return 10 if s in ["X", "10"] else (0 if s == "M" else int(s))
    
    dane = []
    for i, s in enumerate(scores):
        runda = "Runda 1" if i < 36 else "Runda 2"
        runda_de = "Runde 1" if i < 36 else "Runde 2"
        nazwa = runda if lang == "PL" else runda_de
        dane.append({"Punkty": get_val(s), "Runda": nazwa})
        
    df = pd.DataFrame(dane)
    srednie = df.groupby("Runda")["Punkty"].mean().reset_index()
    
    wykres = alt.Chart(srednie).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("Runda:N", title="", sort=None),
        y=alt.Y("Punkty:Q", title="Ø Punkte / Pfeil" if lang == "DE" else "Ø Punktów / Strzałę"),
        color=alt.Color("Runda:N", legend=None, scale=alt.Scale(range=["#2E8B57", "#D4AC0D"])),
        tooltip=["Runda", "Punkty"]
    ).properties(height=200)
    
    return wykres
