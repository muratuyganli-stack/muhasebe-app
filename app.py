import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Veritabanı (İsim v2 yapılarak hata giderildi)
def init_db():
    conn = sqlite3.connect('muhasebe_v2.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (tarih TEXT, tip TEXT, kisi TEXT, kategori TEXT, miktar REAL, aciklama TEXT, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="Görsel Muhasebe", page_icon="📸", layout="wide")

with st.sidebar:
    st.header("➕ Yeni Kayıt")
    with st.form("hesap_formu", clear_on_submit=True):
        tip = st.selectbox("İşlem Türü", ["Gelir", "Gider", "Alacak", "Borç"])
        kisi = st.text_input("Kişi / Müşteri Adı")
        miktar = st.number_input("Tutar (TL)", min_value=0.0)
        kategori = st.selectbox("Kategori", ["Satış", "Mal Alımı", "Yemek", "Yakıt", "Kira", "Diğer"])
        foto = st.file_uploader("Fatura/Fiş Fotoğrafı", type=['jpg', 'jpeg', 'png'])
        aciklama = st.text_input("Not")
        
        if st.form_submit_button("Kaydet"):
            foto_bytes = foto.read() if foto else None
            c = conn.cursor()
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
            # 7 sütun için tam 7 tane ? işareti
            c.execute("INSERT INTO islemler VALUES (?,?,?,?,?,?,?)", 
                      (tarih, tip, kisi, kategori, miktar, aciklama, foto_bytes))
            conn.commit()
            st.success("Başarıyla kaydedildi!")

st.title("📸 Görsel Cari Takip")
df = pd.read_sql_query("SELECT * FROM islemler ORDER BY tarih DESC", conn)

if not df.empty:
    for index, row in df.iterrows():
        with st.expander(f"📅 {row['tarih']} - {row['kisi']} - {row['miktar']} TL"):
            c1, c2 = st.columns([1, 2])
            with c1:
                if row['foto']:
                    st.image(row['foto'], use_container_width=True)
            with c2:
                st.write(f"**Tür:** {row['tip']} | **Kategori:** {row['kategori']}")
                st.write(f"**Not:** {row['aciklama']}")
else:
    st.info("Henüz kayıt yok.")
    
