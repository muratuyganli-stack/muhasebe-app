import streamlit as st
import pandas as pd

st.set_page_config(page_title="Veresiye Defteri", page_icon="📝")

# Uygulama başladığında boş bir liste oluştur
if 'veriler' not in st.session_state:
    st.session_state.veriler = []

st.title("📑 Dijital Veresiye Defteri")

# Giriş Alanları
with st.sidebar:
    st.header("Yeni İşlem")
    musteri = st.text_input("Müşteri Adı")
    tutar = st.number_input("Tutar (TL)", min_value=0.0)
    
    col1, col2 = st.columns(2)
    if col1.button("Borç Yaz"):
        if musteri:
            st.session_state.veriler.append({"Müşteri": musteri, "Tür": "Borç", "Miktar": tutar})
            st.toast("Borç kaydedildi!")
    
    if col2.button("Ödeme Al"):
        if musteri:
            st.session_state.veriler.append({"Müşteri": musteri, "Tür": "Ödeme", "Miktar": tutar})
            st.toast("Ödeme alındı!")

# Tabloyu Göster
if st.session_state.veriler:
    df = pd.DataFrame(st.session_state.veriler)
    st.table(df)
    
    # Hesaplama
    borc = df[df["Tür"] == "Borç"]["Miktar"].sum()
    odeme = df[df["Tür"] == "Ödeme"]["Miktar"].sum()
    st.metric("Kalan Alacak", f"{borc - odeme} TL")
else:
    st.info("Henüz kayıt bulunmuyor. Sol menüden ekleme yapabilirsin.")
    
