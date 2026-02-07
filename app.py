import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cari Takip Sistemi", layout="wide")

# Veri saklama (Sayfa yenilenene kadar tutar)
if 'cariler' not in st.session_state:
    st.session_state.cariler = {} # { "Müşteri Adı": {"Telefon": "...", "Limit": 0, "İşlemler": []} }

st.title("📂 Profesyonel Cari Takip")

# Sekmeler oluşturuyoruz
sekme1, sekme2 = st.tabs(["📇 Cari Kart Tanımla", "💰 Borç/Alacak İşlemi"])

# --- SEKME 1: CARİ KART TANIMLAMA ---
with sekme1:
    st.header("Yeni Müşteri (Cari) Kartı")
    with st.form("cari_form"):
        isim = st.text_input("Müşteri / Firma Adı")
        tel = st.text_input("Telefon Numarası")
        limit = st.number_input("Borç Limiti (TL)", min_value=0)
        submit = st.form_submit_button("Kartı Oluştur")
        
        if submit and isim:
            if isim not in st.session_state.cariler:
                st.session_state.cariler[isim] = {"Telefon": tel, "Limit": limit, "Islemler": []}
                st.success(f"{isim} için cari kart açıldı.")
            else:
                st.warning("Bu müşteri zaten kayıtlı!")

# --- SEKME 2: İŞLEM VE RAPOR ---
with sekme2:
    if not st.session_state.cariler:
        st.info("İşlem yapmak için önce bir cari kart tanımlayın.")
    else:
        secilen_musteri = st.selectbox("Müşteri Seçin", list(st.session_state.cariler.keys()))
        
        col1, col2 = st.columns(2)
        with col1:
            islem_turu = st.radio("İşlem Türü", ["Borçlandır", "Tahsilat Yap"])
            tutar = st.number_input("Tutar", min_value=0.0)
            aciklama = st.text_input("Açıklama (Örn: Ürün satışı)")
            
            if st.button("İşlemi Kaydet"):
                islem_tipi = "Borç" if islem_turu == "Borçlandır" else "Ödeme"
                st.session_state.cariler[secilen_musteri]["Islemler"].append({
                    "Tarih": pd.Timestamp.now().strftime("%d-%m-%Y %H:%M"),
                    "Tür": islem_tipi,
                    "Tutar": tutar,
                    "Açıklama": aciklama
                })
                st.toast("Kayıt başarılı!")

        with col2:
            st.subheader(f"Kart Bilgisi: {secilen_musteri}")
            bilgi = st.session_state.cariler[secilen_musteri]
            st.write(f"📞 **Tel:** {bilgi['Telefon']}")
            st.write(f"🛡️ **Limit:** {bilgi['Limit']} TL")
            
            # İşlem Geçmişi Tablosu
            if bilgi["Islemler"]:
                islem_df = pd.DataFrame(bilgi["Islemler"])
                st.dataframe(islem_df, use_container_width=True)
                
                toplam_borc = islem_df[islem_df["Tür"] == "Borç"]["Tutar"].sum()
                toplam_odeme = islem_df[islem_df["Tür"] == "Ödeme"]["Tutar"].sum()
                st.metric("Güncel Bakiye", f"{toplam_borc - toplam_odeme} TL")
                
