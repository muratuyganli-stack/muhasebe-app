import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Google Sheets Bağlantısı
conn = st.connection("gsheets", type=GSheetsConnection)

# Verileri Oku
df = conn.read(worksheet="Sayfa1")

# Yeni veri ekleme fonksiyonu
def kaydet(yeni_satir):
    # Tabloya ekleme mantığı buraya gelecek
    pass
