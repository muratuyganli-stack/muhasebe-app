import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Veritabanı v23 - Görünürlük Sorunları Giderildi
def init_db():
    conn = sqlite3.connect('muhasebe_v23.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# CSS: Butonların ve formların net görünmesini sağlar
st.markdown("""
    <style>
    .shop-title { text-align: center; color: #1E1E1E; font-family: 'Arial Black', sans-serif; font-size: clamp(24px, 8vw, 40px); font-weight: bold; border-bottom: 3px solid #007BFF; padding-bottom: 5px; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; font-weight: bold; height: 3.5em; background-color: #007BFF; color: white; }
    .delete-btn>button { background-color: #dc3545 !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="shop-title">🔨 HAVAS AHŞAP</div>', unsafe_allow_html=True)

# 1. YENİ MÜŞTERİ EKLEME (HER ZAMAN ÜSTTE GÖRÜNÜR)
with st.expander("👤 YENİ MÜŞTERİ / CARİ KART EKLE", expanded=False):
    with st.form("yeni_musteri_formu"):
        y_ad = st.text_input("Müşteri Adı Soyadı")
        y_tel = st.text_input("Telefon Numarası")
        if st.form_submit_button("Müşteriyi Kaydet"):
            if y_ad:
                conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (y_ad, y_tel))
                conn.commit()
                st.success("Müşteri başarıyla eklendi!")
                st.rerun()

st.divider()

# Verileri Çek
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# 2. MÜŞTERİ LİSTESİ VE DETAYLAR
if not df_m.empty:
    arama = st.text_input("🔍 Müşteri Ara...", placeholder="İsim yazmaya başlayın")
    for _, m in df_m.iterrows():
        if arama.lower() in m['ad'].lower():
            m_islemler = df_i[df_i['musteri_id'] == m['id']]
            bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1.5])
                c1.markdown(f"**{m['ad']}**")
                c2.markdown(f"<p style='text-align:right; color:{'#d9534f' if bakiye > 0 else '#5cb85c'}; font-weight:bold;'>{abs(bakiye):,.2f} TL</p>", unsafe_allow_html=True)
                if c3.button("İşlem Yap / Fotoğraf Ekle", key=f"btn_{m['id']}"):
                    st.session_state['aktif_id'] = m['id']
                    st.rerun()

# 3. İŞLEM VE FOTOĞRAF EKLEME PANELİ (BİR MÜŞTERİ SEÇİLDİĞİNDE AÇILIR)
if 'aktif_id' in st.session_state:
    m_id = st.session_state['aktif_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    st.markdown(f"---")
    col_kapat, col_sil = st.columns([4, 1])
    if col_kapat.button("❌ Paneli Kapat"):
        del st.session_state['aktif_id']; st.rerun()
    
    st.header(f"📋 {m_bilgi['ad']}")
    
    # FOTOĞRAF VE İŞLEM EKLEME FORMU
    with st.container(border=True):
        st.subheader("📷 Yeni İşlem ve Fotoğraf Ekle")
        with st.form(f"islem_f_{m_id}", clear_on_submit=True):
            f_tip = st.selectbox("İşlem Türü", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
            f_miktar = st.number_input("Tutar", min_value=0.0)
            f_not = st.text_input("Not/Açıklama")
            f_resimler = st.file_uploader("Fotoğrafları Seç (Çoklu)", accept_multiple_files=True)
            if st.form_submit_button("İŞLEMİ VE FOTOĞRAFLARI KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, f_miktar, f_tip, f_not))
                is_id = c.lastrowid
                for r in f_resimler:
                    c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, r.read()))
                conn.commit()
                st.success("Kayıt başarılı!")
                st.rerun()

    # Müşteriyi Silme Butonu (En Altta)
    if st.button("🗑️ BU CARİ KARTI TAMAMEN SİL", key="sil_ana"):
        conn.cursor().execute("DELETE FROM musteriler WHERE id=?", (m_id,))
        conn.commit()
        del st.session_state['aktif_id']; st.rerun()
    
