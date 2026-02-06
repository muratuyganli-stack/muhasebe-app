import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Veritabanı Kurulumu
def init_db():
    conn = sqlite3.connect('muhasebe.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS islemler (tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="Muhasebe", page_icon="💰")
st.title("📱 Mobil Muhasebe")

# Kayıt Formu
with st.form("hesap_formu", clear_on_submit=True):
    tip = st.selectbox("İşlem Türü", ["Gelir", "Gider"])
    miktar = st.number_input("Tutar (TL)", min_value=0.0)
    aciklama = st.text_input("Açıklama")
    kaydet = st.form_submit_button("Sisteme İşle")
    
    if kaydet:
        c = conn.cursor()
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
        c.execute("INSERT INTO islemler VALUES (?,?,?,?)", (tarih, tip, miktar, aciklama))
        conn.commit()
        st.success("Kayıt başarılı!")

# Özet Tablo
st.subheader("Geçmiş Kayıtlar")
df = pd.read_sql_query("SELECT * FROM islemler ORDER BY tarih DESC", conn)
st.dataframe(df, use_container_width=True)
      
