import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# Veritabanı v15
def init_db():
    conn = sqlite3.connect('muhasebe_v15.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT UNIQUE, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
# Tarayıcı sekme başlığını da güncelledik
st.set_page_config(page_title="HAVAS AHŞAP - Cari Takip", layout="wide")

# --- CSS İLE MAVİ BUTON VE GÖRSELLİK ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background-color: #007BFF;
        color: white;
        font-weight: bold;
        font-size: 18px;
        border: none;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background-color: #0056b3;
        color: white;
    }
    .shop-title {
        text-align: center;
        color: #1E1E1E;
        font-family: 'Arial Black', Gadget, sans-serif;
        font-size: 45px;
        letter-spacing: 2px;
        margin-bottom: 10px;
        border-bottom: 3px solid #007BFF;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ANA SAYFA BAŞLIK ---
st.markdown('<div class="shop-title">🔨 HAVAS AHŞAP</div>', unsafe_allow_html=True)

# Mavi Buton
if st.button("➕ YENİ MÜŞTERİ EKLE"):
    st.session_state['yeni_musteri_modu'] = True

if st.session_state.get('yeni_musteri_modu'):
    with st.container(border=True):
        st.subheader("👤 Yeni Müşteri Tanımla")
        y_ad = st.text_input("Ad Soyad")
        y_tel = st.text_input("Telefon")
        col_kaydet, col_iptal = st.columns(2)
        if col_kaydet.button("Kaydet", key="m_kaydet"):
            if y_ad:
                try:
                    c = conn.cursor()
                    c.execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (y_ad, y_tel))
                    conn.commit()
                    st.success("Müşteri eklendi!")
                    st.session_state['yeni_musteri_modu'] = False
                    st.rerun()
                except: st.error("Bu isim zaten var!")
        if col_iptal.button("Vazgeç"):
            st.session_state['yeni_musteri_modu'] = False
            st.rerun()

st.divider()

# --- VERİLERİ ÇEK ---
df_musteri = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_islem = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- CARİ KARTLAR ---
if not df_musteri.empty:
    arama = st.text_input("🔍 Müşteri ara...", placeholder="İsim veya telefon yazın")
    
    for _, m in df_musteri.iterrows():
        if arama.lower() in m['ad'].lower() or arama in str(m['tel']):
            m_islemler = df_islem[df_islem['musteri_id'] == m['id']]
            bakiye = m_islemler[m_islemler['tip'] == "Satis (Alacak Yaz)"]['miktar'].sum() - \
                     m_islemler[m_islemler['tip'] == "Tahsilat (Borctan Dus)"]['miktar'].sum()
            
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1.5])
                with c1:
                    st.markdown(f"### {m['ad']}")
                    if m['tel']: st.markdown(f"📞 [Ara: {m['tel']}](tel:{m['tel']})")
                with c2:
                    renk = "#d9534f" if bakiye > 0 else "#5cb85c"
                    st.markdown(f"<h2 style='color:{renk}; text-align:right; margin:0;'>{abs(bakiye):,.2f} TL</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:right; color:grey; margin:0;'>{'BORÇLU' if bakiye > 0 else 'ALACAKLI'}</p>", unsafe_allow_html=True)
                with c3:
                    if st.button("Detay / İşlem", key=f"det_{m['id']}"):
                        st.session_state['detay_id'] = m['id']
                        st.rerun()
                    if bakiye > 0 and m['tel']:
                        wa_url = f"https://wa.me/9{m['tel']}?text=Merhaba {m['ad']}, HAVAS AHŞAP güncel bakiyeniz {bakiye:,.2f} TL'dir."
                        st.markdown(f"[💬 WhatsApp]({urllib.parse.quote(wa_url, safe=':/=?&')})")

# --- DETAY PANELİ ---
if 'detay_id' in st.session_state:
    m_id = st.session_state['detay_id']
    m_info = df_musteri[df_musteri['id'] == m_id].iloc[0]
    st.divider()
    if st.button("⬅️ Listeye Dön"):
        del st.session_state['detay_id']; st.rerun()
    
    st.header(f"📋 {m_info['ad']} - Hesap Dökümü")
    
    with st.expander("➕ Yeni İşlem Gir"):
        with st.form("islem_form", clear_on_submit=True):
            f_tip = st.selectbox("İşlem", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
            f_miktar = st.number_input("Tutar", min_value=0.0)
            f_not = st.text_input("Açıklama")
            f_fotos = st.file_uploader("Fotoğraflar (Çoklu)", accept_multiple_files=True)
            if st.form_submit_button("Kaydet"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, tip, miktar, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, f_tip, f_miktar, f_not))
                is_id = c.lastrowid
                for f in f_fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.success("İşlem kaydedildi!"); st.rerun()

    k_df = df_islem[df_islem['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
            st.write(f"**Not:** {row['aciklama']}")
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)
                    
