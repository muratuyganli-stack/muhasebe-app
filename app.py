import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# Veritabanı (Fotoğraf sütunu eklendi)
def init_db():
    conn = sqlite3.connect('muhasebe.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (tarih TEXT, tip TEXT, kisi TEXT, kategori TEXT, miktar REAL, aciklama TEXT, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="Görsel Muhasebe", page_icon="📸", layout="wide")

# Fotoğrafı görüntülenebilir formata çevirme
def get_image_download_link(img_bytes):
    if img_bytes:
        encoded = base64.b64encode(img_bytes).decode()
        return f"data:image/jpeg;base64,{encoded}"
    return None

with st.sidebar:
    st.header("➕ Yeni Kayıt & Fotoğraf")
    with st.form("hesap_formu", clear_on_submit=True):
        tip = st.selectbox("İşlem Türü", ["Gelir", "Gider", "Alacak", "Borç"])
        kisi = st.text_input("Kişi / Müşteri Adı")
        miktar = st.number_input("Tutar (TL)", min_value=0.0)
        kategori = st.selectbox("Kategori", ["Satış", "Mal Alımı", "Yemek", "Yakıt", "Kira", "Diğer"])
        foto = st.file_uploader("Fatura/Fiş Fotoğrafı Çek veya Yükle", type=['jpg', 'jpeg', 'png'])
        aciklama = st.text_input("Not")
        
        if st.form_submit_button("Kaydet"):
            foto_bytes = None
            if foto:
                foto_bytes = foto.read()
            
            c = conn.cursor()
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO islemler VALUES (?,?,?,?,?,?,?)", 
                      (tarih, tip, kisi, kategori, miktar, aciklama, foto_bytes))
            conn.commit()
            st.success("Fotoğraflı kayıt eklendi!")

# Verileri ve Görselleri Listeleme
st.title("📸 Görsel Cari Takip Paneli")
df = pd.read_sql_query("SELECT * FROM islemler ORDER BY tarih DESC", conn)

if not df.empty:
    for index, row in df.iterrows():
        with st.expander(f"📅 {row['tarih']} - {row['kisi']} - {row['miktar']} TL ({row['tip']})"):
            col1, col2 = st.columns([1, 2])
            with col1:
                if row['foto']:
                    st.image(row['foto'], caption="İşlem Belgesi", use_container_width=True)
                else:
                    st.warning("Fotoğraf eklenmemiş.")
            with col2:
                st.write(f"**Kategori:** {row['kategori']}")
                st.write(f"**Açıklama:** {row['aciklama']}")
else:
    st.info("Henüz kayıt yok.")
    
