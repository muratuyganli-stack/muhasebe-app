import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# Veritabanı v13 (Müşteriler ve İşlemler Ayrıldı)
def init_db():
    conn = sqlite3.connect('muhasebe_v13.db', check_same_thread=False)
    c = conn.cursor()
    # Müşteri Rehberi Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT UNIQUE, tel TEXT)''')
    # İşlemler Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    # Fotoğraflar Tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="Profesyonel Cari Takip", layout="wide")

# --- YAN MENÜ: MÜŞTERİ VE İŞLEM EKLEME ---
with st.sidebar:
    st.header("👤 Müşteri Yönetimi")
    # 1. ADIM: Müşteri Kaydet (Bir kez yapılır)
    with st.expander("✨ Yeni Müşteri Tanımla"):
        with st.form("musteri_form", clear_on_submit=True):
            y_ad = st.text_input("Müşteri Adı Soyadı").strip().title()
            y_tel = st.text_input("Telefon Numarası")
            if st.form_submit_button("Müşteriyi Kaydet"):
                if y_ad:
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (y_ad, y_tel))
                        conn.commit()
                        st.success(f"{y_ad} Rehbere Eklendi!")
                        st.rerun()
                    except: st.error("Bu müşteri zaten kayıtlı!")

    st.divider()
    
    # 2. ADIM: İşlem Yap (Sadece kayıtlı müşterilere)
    st.header("💰 Yeni İşlem Gir")
    musteri_listesi = pd.read_sql_query("SELECT * FROM musteriler", conn)
    if not musteri_listesi.empty:
        with st.form("islem_form", clear_on_submit=True):
            secilen_m = st.selectbox("Müşteri Seç", musteri_listesi['ad'].tolist())
            f_tip = st.selectbox("İşlem Tipi", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
            f_miktar = st.number_input("Tutar", min_value=0.0)
            f_not = st.text_input("Not / Açıklama")
            f_fotos = st.file_uploader("Fotoğrafları Seç (Birden Fazla)", accept_multiple_files=True)
            
            if st.form_submit_button("İşlemi Kaydet"):
                c = conn.cursor()
                m_id = musteri_listesi[musteri_listesi['ad'] == secilen_m]['id'].values[0]
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, tip, miktar, aciklama) VALUES (?,?,?,?,?)", 
                          (int(m_id), tarih, f_tip, f_miktar, f_not))
                is_id = c.lastrowid
                for f in f_fotos:
                    c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit()
                st.success("İşlem Başarıyla Kaydedildi!")
                st.rerun()
    else:
        st.warning("Önce bir müşteri tanımlamalısınız!")

# --- ANA SAYFA: CARİ KARTLAR ---
st.title("📂 Müşteri Cari Rehberi")
df_musteri = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_islem = pd.read_sql_query("SELECT * FROM islemler", conn)

if not df_musteri.empty:
    arama = st.text_input("🔍 İsim veya Telefonla Ara...", "").lower()
    
    for _, m_row in df_musteri.iterrows():
        m_id = m_row['id']
        m_ad = m_row['ad']
        m_tel = m_row['tel']
        
        # Müşterinin İşlemlerini Süz
        m_islemler = df_islem[df_islem['musteri_id'] == m_id]
        satis = m_islemler[m_islemler['tip'] == "Satis (Alacak Yaz)"]['miktar'].sum()
        tahsilat = m_islemler[m_islemler['tip'] == "Tahsilat (Borctan Dus)"]['miktar'].sum()
        bakiye = satis - tahsilat
        
        if arama in m_ad.lower() or arama in str(m_tel):
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1.5])
                with col1:
                    st.markdown(f"### {m_ad}")
                    if m_tel: st.markdown(f"📞 [Ara: {m_tel}](tel:{m_tel})")
                with col2:
                    renk = "red" if bakiye > 0 else "green"
                    st.markdown(f"<h3 style='color:{renk}; text-align:right;'>{abs(bakiye):,.2f} TL</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:right; color:grey;'>{'BORÇLU' if bakiye > 0 else 'ALACAKLI'}</p>", unsafe_allow_html=True)
                with col3:
                    if st.button("Detaylar", key=f"det_{m_id}"):
                        st.session_state['detay_id'] = m_id
                        st.rerun()
                    
                    if bakiye > 0 and m_tel:
                        mesaj = f"Merhaba {m_ad}, güncel borç bakiyeniz {bakiye:,.2f} TL'dir."
                        wa_url = f"https://wa.me/9{m_tel}?text={urllib.parse.quote(mesaj)}"
                        st.markdown(f"[💬 WhatsApp]({wa_url})")

# --- DETAY PANELİ ---
if 'detay_id' in st.session_state:
    m_id = st.session_state['detay_id']
    m_bilgi = df_musteri[df_musteri['id'] == m_id].iloc[0]
    st.divider()
    if st.button("⬅️ Listeye Dön"):
        del st.session_state['detay_id']
        st.rerun()
    
    st.header(f"📋 {m_bilgi['ad']} - Geçmiş İşlemler")
    k_df = df_islem[df_islem['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
            st.write(f"**Not:** {row['aciklama']}")
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, f_row in f_df.iterrows():
                    cols[i].image(f_row['foto'], use_container_width=True)
    
