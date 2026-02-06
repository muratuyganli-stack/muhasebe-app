import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Veritabanı v22 - Cari kart silme özelliği eklendi
def init_db():
    conn = sqlite3.connect('muhasebe_v22.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- CSS VE BAŞLIK ---
st.markdown("""
    <style>
    .shop-title { text-align: center; color: #1E1E1E; font-family: 'Arial Black', sans-serif; font-size: clamp(24px, 8vw, 40px); font-weight: bold; border-bottom: 3px solid #007BFF; padding-bottom: 5px; margin-bottom: 15px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 3em; }
    .delete-card-btn>button { background-color: #dc3545; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="shop-title">🔨 HAVAS AHŞAP</div>', unsafe_allow_html=True)

# Veri Çekme ve Raporlama (Öncekiyle aynı)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)

if not df_i.empty:
    st.subheader("📊 Finansal Raporlar")
    df_i['tarih_dt'] = pd.to_datetime(df_i['tarih'], format="%d-%m-%Y %H:%M", errors='coerce')
    bugun = datetime.now()
    c_h, c_a, c_y = st.columns(3)
    for label, days, col in [('7 Gün', 7, c_h), ('30 Gün', 30, c_a), ('1 Yıl', 365, c_y)]:
        p_data = df_i[df_i['tarih_dt'] > (bugun - timedelta(days=days))]
        p_satis = p_data[p_data['tip'].str.contains("Satis")]['miktar'].sum()
        p_tahsilat = p_data[p_data['tip'].str.contains("Tahsilat")]['miktar'].sum()
        col.metric(label, f"{p_satis-p_tahsilat:,.2f} TL", f"Satış: {p_satis:,.0f}")

st.divider()

# --- MÜŞTERİ LİSTESİ ---
if not df_m.empty:
    arama = st.text_input("🔍 Müşteri Ara...")
    for _, m in df_m.iterrows():
        if arama.lower() in m['ad'].lower():
            m_islemler = df_i[df_i['musteri_id'] == m['id']]
            bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1.5])
                c1.markdown(f"**{m['ad']}**")
                c2.markdown(f"<p style='text-align:right; color:{'#d9534f' if bakiye > 0 else '#5cb85c'}; font-weight:bold;'>{abs(bakiye):,.2f} TL</p>", unsafe_allow_html=True)
                if c3.button("Detay", key=f"det_{m['id']}"):
                    st.session_state['secili_id'] = m['id']; st.rerun()

# --- DETAY VE SİLME PANELİ ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    st.divider()
    
    col_back, col_del = st.columns([4, 1])
    if col_back.button("⬅️ Listeye Dön"): del st.session_state['secili_id']; st.rerun()
    
    # MÜŞTERİ KARTINI SİLME BUTONU
    if col_del.button("🗑️ KARTI SİL", help="Müşteriyi ve tüm geçmişini siler"):
        c = conn.cursor()
        c.execute("DELETE FROM musteriler WHERE id=?", (m_id,))
        c.execute("DELETE FROM islemler WHERE musteri_id=?", (m_id,))
        # Fotoğrafları da temizle
        islem_ids = df_i[df_i['musteri_id'] == m_id]['id'].tolist()
        for iid in islem_ids: c.execute("DELETE FROM fotograflar WHERE islem_id=?", (iid,))
        conn.commit()
        del st.session_state['secili_id']; st.success("Cari kart silindi."); st.rerun()

    st.header(f"👤 {m_bilgi['ad']}")
    
    # Yeni İşlem ve Geçmiş Listesi (v21 ile aynı şekilde devam eder)
    # ... [Burada fotoğraf ve işlem ekleme kodları yer alır] ...
    
