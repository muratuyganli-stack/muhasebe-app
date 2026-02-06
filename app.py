import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import urllib.parse

# Veritabanı v12
def init_db():
    conn = sqlite3.connect('muhasebe_v12.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, tip TEXT, kisi TEXT, tel TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="Cari Takip & WhatsApp", layout="wide")

df = pd.read_sql_query("SELECT * FROM islemler", conn)

st.title("📂 Müşteri Cari Rehberi & WhatsApp")

if not df.empty:
    musteriler = sorted(df['kisi'].unique())
    arama = st.text_input("🔍 Müşteri veya Telefon Ara...", "").lower()
    
    for m in musteriler:
        m_df = df[df['kisi'] == m]
        telefon = m_df['tel'].iloc[0] if 'tel' in m_df.columns else ""
        
        if arama in m.lower() or arama in str(telefon):
            satis = m_df[m_df['tip'] == "Satis (Alacak Yaz)"]['miktar'].sum()
            tahsilat = m_df[m_df['tip'] == "Tahsilat (Borctan Dus)"]['miktar'].sum()
            bakiye = satis - tahsilat
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1.5])
                with col1:
                    st.markdown(f"### {m}")
                    if telefon:
                        st.markdown(f"📞 [Ara: {telefon}](tel:{telefon})")
                with col2:
                    renk = "red" if bakiye > 0 else "green"
                    st.markdown(f"<h3 style='color:{renk}; text-align:right;'>{abs(bakiye):,.2f} TL</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:right; color:grey;'>{'BORÇLU' if bakiye > 0 else 'ALACAKLI'}</p>", unsafe_allow_html=True)
                with col3:
                    if st.button("Detaylar", key=f"btn_{m}"):
                        st.session_state['detay_kisi'] = m
                        st.rerun()
                    
                    # WhatsApp Hatırlatma Butonu
                    if bakiye > 0 and telefon:
                        mesaj = f"Merhaba {m}, güncel borç bakiyeniz {bakiye:,.2f} TL'dir. İyi çalışmalar dileriz."
                        msg_encoded = urllib.parse.quote(mesaj)
                        wa_url = f"https://wa.me/9{telefon}?text={msg_encoded}"
                        st.markdown(f"[💬 WhatsApp Hatırlat]( {wa_url} )")

# Detay Görünümü ve Çoklu Fotoğraf (Aynı şekilde korundu)
if 'detay_kisi' in st.session_state:
    kisi = st.session_state['detay_kisi']
    st.divider()
    if st.button("⬅️ Rehbere Dön"):
        del st.session_state['detay_kisi']
        st.rerun()
    
    st.header(f"📋 {kisi} - İşlem Geçmişi")
    k_df = df[df['kisi'] == kisi].sort_values(by='id', ascending=False)
    
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
            st.write(f"**Not:** {row['aciklama']}")
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, f_row in f_df.iterrows():
                    cols[i].image(f_row['foto'], use_container_width=True)

# Yan Menü: Yeni Kayıt ve Çoklu Fotoğraf Yükleme
with st.sidebar:
    st.header("➕ Yeni İşlem")
    with st.form("yeni_islem", clear_on_submit=True):
        f_kisi = st.text_input("Müşteri Adı").strip().title()
        f_tel = st.text_input("Telefon (Örn: 05xxxxxxxxx)")
        f_tip = st.selectbox("İşlem", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
        f_miktar = st.number_input("Tutar", min_value=0.0)
        f_not = st.text_input("Not")
        f_fotos = st.file_uploader("Fotoğrafları Seç (Çoklu)", accept_multiple_files=True)
        
        if st.form_submit_button("Kaydet"):
            if f_kisi:
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (tarih, tip, kisi, tel, miktar, aciklama) VALUES (?,?,?,?,?,?)", 
                          (tarih, f_tip, f_kisi, f_tel, f_miktar, f_not))
                is_id = c.lastrowid
                for f in f_fotos:
                    c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit()
                st.rerun()
                
