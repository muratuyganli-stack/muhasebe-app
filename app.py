import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import urllib.parse

# Veritabanı v20 - Hatalar Giderildi ve Tüm Özellikler Birleştirildi
def init_db():
    conn = sqlite3.connect('muhasebe_v20.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT UNIQUE, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- CSS: ÖZEL TASARIM ---
st.markdown("""
    <style>
    .shop-title { text-align: center; color: #1E1E1E; font-family: 'Arial Black', sans-serif; font-size: clamp(24px, 8vw, 40px); font-weight: bold; border-bottom: 3px solid #007BFF; padding-bottom: 5px; margin-bottom: 15px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 3em; transition: 0.3s; }
    .report-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #007BFF; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="shop-title">🔨 HAVAS AHŞAP</div>', unsafe_allow_html=True)

# --- VERİLERİ ÇEK ---
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)

# --- RAPORLAMA PANELİ ---
if not df_i.empty:
    st.subheader("📊 Finansal Raporlar")
    # Tarih dönüşümü (Hata payını azaltmak için format belirtildi)
    df_i['tarih_dt'] = pd.to_datetime(df_i['tarih'], format="%d-%m-%Y %H:%M", errors='coerce')
    df_i = df_i.dropna(subset=['tarih_dt']) # Hatalı tarihleri temizle
    bugun = datetime.now()
    
    c_h, c_a, c_y = st.columns(3)
    periods = [('7 Gün', 7, c_h), ('30 Gün', 30, c_a), ('1 Yıl', 365, c_y)]
    
    for label, days, col in periods:
        p_data = df_i[df_i['tarih_dt'] > (bugun - timedelta(days=days))]
        p_satis = p_data[p_data['tip'].str.contains("Satis")]['miktar'].sum()
        p_tahsilat = p_data[p_data['tip'].str.contains("Tahsilat")]['miktar'].sum()
        col.markdown(f"<div class='report-card'><b>{label}</b><br>Satış: {p_satis:,.2f}<br>Tahsilat: {p_tahsilat:,.2f}</div>", unsafe_allow_html=True)

st.divider()

# --- MÜŞTERİ EKLEME ---
if st.button("➕ YENİ MÜŞTERİ EKLE", type="primary"):
    st.session_state['yeni_m'] = True

if st.session_state.get('yeni_m'):
    with st.form("m_form"):
        y_ad = st.text_input("Müşteri Ad Soyad").strip().title()
        y_tel = st.text_input("Telefon (05xx)")
        c1, c2 = st.columns(2)
        if c1.form_submit_button("✅ KAYDET"):
            if y_ad:
                try:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (y_ad, y_tel))
                    conn.commit(); st.rerun()
                except: st.error("Müşteri zaten var!")
        if c2.form_submit_button("❌ VAZGEÇ"): st.session_state['yeni_m'] = False; st.rerun()

# --- MÜŞTERİ LİSTESİ ---
if not df_m.empty:
    arama = st.text_input("🔍 Müşteri Ara...", placeholder="İsim yazın")
    for _, m in df_m.iterrows():
        if arama.lower() in m['ad'].lower():
            m_islemler = df_i[df_i['musteri_id'] == m['id']]
            bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1.5])
                with col1:
                    st.markdown(f"**{m['ad']}**")
                    if m['tel']: st.markdown(f"📞 [Ara](tel:{m['tel']})")
                with col2:
                    renk = "#d9534f" if bakiye > 0 else "#5cb85c"
                    st.markdown(f"<p style='color:{renk}; text-align:right; font-weight:bold;'>{abs(bakiye):,.2f} TL</p>", unsafe_allow_html=True)
                with col3:
                    if st.button("Detay / İşlem", key=f"det_{m['id']}"):
                        st.session_state['secili_id'] = m['id']; st.rerun()

# --- DETAY PANELİ ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    st.divider()
    if st.button("⬅️ LİSTEYE DÖN"): del st.session_state['secili_id']; st.rerun()
    
    # Yeni İşlem Formu (Fotoğraf Desteğiyle)
    with st.expander("➕ YENİ İŞLEM / FOTOĞRAF EKLE"):
        with st.form("y_islem", clear_on_submit=True):
            t = st.selectbox("İşlem Tipi", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
            m_tut = st.number_input("Tutar", min_value=0.0)
            a_not = st.text_input("Açıklama")
            f_list = st.file_uploader("Fotoğraflar (Çoklu Seçim)", accept_multiple_files=True)
            if st.form_submit_button("KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, m_tut, t, a_not))
                is_id = c.lastrowid
                for f in f_list: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # Geçmiş ve Düzenleme/Silme (Fotoğraflar Unutulmadı)
    k_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
            with st.form(f"edit_{row['id']}"):
                n_mik = st.number_input("Miktar", value=float(row['miktar']))
                n_not = st.text_input("Not", value=str(row['aciklama']))
                be1, be2 = st.columns(2)
                if be1.form_submit_button("GÜNCELLE"):
                    conn.cursor().execute("UPDATE islemler SET miktar=?, aciklama=? WHERE id=?", (n_mik, n_not, row['id']))
                    conn.commit(); st.rerun()
                if be2.form_submit_button("🗑️ SİL"):
                    conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()
            
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)
                    
