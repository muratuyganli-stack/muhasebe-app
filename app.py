import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

# Veritabanı v19
def init_db():
    conn = sqlite3.connect('muhasebe_v19.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT UNIQUE, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- CSS: TASARIM ---
st.markdown("""
    <style>
    .shop-title { text-align: center; color: #1E1E1E; font-family: 'Arial Black', sans-serif; font-size: clamp(24px, 8vw, 40px); font-weight: bold; border-bottom: 3px solid #007BFF; padding-bottom: 5px; margin-bottom: 15px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 3em; }
    .report-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="shop-title">🔨 HAVAS AHŞAP</div>', unsafe_allow_html=True)

# --- RAPORLAMA PANELİ ---
st.header("📊 Finansal Raporlar")
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
if not df_i.empty:
    # Tarih formatını dönüştür (Gün-Ay-Yıl formatından)
    df_i['tarih_dt'] = pd.to_datetime(df_i['tarih'], format="%d-%m-%Y %H:%M")
    bugun = datetime.now()
    
    col_h, col_a, col_y = st.columns(3)
    
    # Haftalık Rapor
    h_data = df_i[df_i['tarih_dt'] > (bugun - timedelta(days=7))]
    h_satis = h_data[h_data['tip'].str.contains("Satis")]['miktar'].sum()
    h_tahsilat = h_data[h_data['tip'].str.contains("Tahsilat")]['miktar'].sum()
    with col_h:
        st.markdown(f"<div class='report-card'><b>📅 Son 7 Gün</b><br>Satış: {h_satis:,.2f} TL<br>Tahsilat: {h_tahsilat:,.2f} TL</div>", unsafe_allow_html=True)

    # Aylık Rapor
    a_data = df_i[df_i['tarih_dt'] > (bugun - timedelta(days=30))]
    a_satis = a_data[a_data['tip'].str.contains("Satis")]['miktar'].sum()
    a_tahsilat = a_data[a_data['tip'].str.contains("Tahsilat")]['miktar'].sum()
    with col_a:
        st.markdown(f"<div class='report-card'><b>🗓️ Son 30 Gün</b><br>Satış: {a_satis:,.2f} TL<br>Tahsilat: {a_tahsilat:,.2f} TL</div>", unsafe_allow_html=True)

    # Yıllık Rapor
    y_data = df_i[df_i['tarih_dt'] > (bugun - timedelta(days=365))]
    y_satis = y_data[y_data['tip'].str.contains("Satis")]['miktar'].sum()
    y_tahsilat = y_data[y_data['tip'].str.contains("Tahsilat")]['miktar'].sum()
    with col_y:
        st.markdown(f"<div class='report-card'><b>🏢 Son 1 Yıl</b><br>Satış: {y_satis:,.2f} TL<br>Tahsilat: {y_tahsilat:,.2f} TL</div>", unsafe_allow_html=True)
else:
    st.info("Henüz raporlanacak veri bulunmuyor.")

st.divider()

# --- MÜŞTERİ YÖNETİMİ ---
if st.button("➕ YENİ MÜŞTERİ EKLE", type="primary"):
    st.session_state['yeni_m'] = True

if st.session_state.get('yeni_m'):
    with st.form("m_form", clear_on_submit=True):
        y_ad = st.text_input("Müşteri Ad Soyad")
        y_tel = st.text_input("Telefon")
        c1, c2 = st.columns(2)
        if c1.form_submit_button("✅ KAYDET"):
            if y_ad:
                try:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (y_ad, y_tel))
                    conn.commit(); st.session_state['yeni_m'] = False; st.rerun()
                except: st.error("Müşteri zaten var!")
        if c2.form_submit_button("❌ VAZGEÇ"): st.session_state['yeni_m'] = False; st.rerun()

# Müşteri Kartları (Önceki versiyondaki gibi devam eder...)
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
if not df_m.empty:
    arama = st.text_input("🔍 Ara...", placeholder="Müşteri ismi...")
    for _, m in df_m.iterrows():
        if arama.lower() in m['ad'].lower():
            # (Kart tasarımı ve detaylar burada yer alır)
            # ... [Önceki kodun aynısı] ...
            pass
            
