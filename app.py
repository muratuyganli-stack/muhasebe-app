import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Veresiye Defteri", layout="centered")

st.title("📑 Dijital Veresiye Defteri")

# Google Sheets Bağlantısı (URL kısmına kendi tablo linkini yapıştırabilirsin)
url = "BURAYA_GOOGLE_SHEET_LINKINI_YAPISTIR"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url)
    
    # Arayüz İşlemleri
    with st.sidebar:
        st.header("Yeni Kayıt")
        isim = st.text_input("Müşteri Adı")
        miktar = st.number_input("Tutar (TL)", min_value=0.0)
        
        if st.button("Kaydet"):
            st.success(f"{isim} için işlem yapıldı!")
            # Not: Yazma işlemi için Google Cloud Console ayarı gerekir.
            
    st.subheader("Borçlu Listesi")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.warning("Lütfen requirements.txt dosyasını kontrol et ve Google Sheet linkini ekle.")
    
