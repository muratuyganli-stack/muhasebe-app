import streamlit as st
import pandas as pd
from PIL import Image

st.set_page_config(page_title="Görsel Destekli Cari Takip", layout="wide")

if 'cariler' not in st.session_state:
    st.session_state.cariler = {} 

st.title("📸 Görsel Destekli Cari Takip")

sekme1, sekme2 = st.tabs(["📇 Cari Kart Tanımla", "💰 Borç/Alacak İşlemi"])

# --- SEKME 1: CARİ KART TANIMLAMA ---
with sekme1:
    st.header("Yeni Müşteri (Cari) Kartı")
    with st.form("cari_form"):
        isim = st.text_input("Müşteri / Firma Adı")
        tel = st.text_input("Telefon Numarası")
        limit = st.number_input("Borç Limiti (TL)", min_value=0, value=0, step=1)
        submit = st.form_submit_button("Kartı Oluştur")
        
        if submit and isim:
            if isim not in st.session_state.cariler:
                st.session_state.cariler[isim] = {"Telefon": tel, "Limit": limit, "Islemler": []}
                st.success(f"{isim} için cari kart açıldı.")

# --- SEKME 2: İŞLEM VE GÖRSEL YÜKLEME ---
with sekme2:
    if not st.session_state.cariler:
        st.info("Önce bir cari kart tanımlayın.")
    else:
        secilen_musteri = st.selectbox("Müşteri Seçin", list(st.session_state.cariler.keys()))
        
        col1, col2 = st.columns([1, 1.5]) # Sağ tarafı görseller için biraz daha genişlettik
        
        with col1:
            st.subheader("İşlem Detayı")
            islem_turu = st.radio("İşlem Türü", ["Borçlandır", "Tahsilat Yap"])
            tutar = st.number_input("Tutar (TL)", min_value=0, value=0, step=1)
            aciklama = st.text_area("Açıklama (Ürünler, Notlar vb.)")
            
            # --- ÇOKLU GÖRSEL YÜKLEME ALANI ---
            yuklenen_dosyalar = st.file_uploader("İşlemle ilgili görselleri seçin (Fiş, Ürün vb.)", 
                                                accept_multiple_files=True, 
                                                type=['png', 'jpg', 'jpeg'])
            
            if st.button("İşlemi Kaydet"):
                is_tipi = "Borç" if islem_turu == "Borçlandır" else "Ödeme"
                
                # Görselleri listeye al
                gorsel_listesi = []
                if yuklenen_dosyalar:
                    for dosya in yuklenen_dosyalar:
                        img = Image.open(dosya)
                        gorsel_listesi.append(img)

                st.session_state.cariler[secilen_musteri]["Islemler"].append({
                    "Tarih": pd.Timestamp.now().strftime("%d-%m-%Y %H:%M"),
                    "Tür": is_tipi,
                    "Tutar": int(tutar),
                    "Açıklama": aciklama,
                    "Görseller": gorsel_listesi
                })
                st.toast("Kayıt ve görseller başarıyla eklendi!")

        with col2:
            st.subheader(f"Ekstre ve Kanıtlar: {secilen_musteri}")
            bilgi = st.session_state.cariler[secilen_musteri]
            
            if bilgi["Islemler"]:
                for i, islem in enumerate(reversed(bilgi["Islemler"])):
                    with st.expander(f"{islem['Tarih']} - {islem['Tür']}: {islem['Tutar']} TL"):
                        st.write(f"**Not:** {islem['Açıklama']}")
                        
                        # Eğer görsel varsa yan yana göster
                        if islem["Görseller"]:
                            st.write("📸 **Ekli Görseller:**")
                            cols = st.columns(len(islem["Görseller"]))
                            for idx, gorsel in enumerate(islem["Görseller"]):
                                with cols[idx]:
                                    st.image(gorsel, use_container_width=True)
                
                st.divider()
                df = pd.DataFrame(bilgi["Islemler"])
                bakiye = int(df[df["Tür"] == "Borç"]["Tutar"].sum() - df[df["Tür"] == "Ödeme"]["Tutar"].sum())
                st.metric("Güncel Bakiye", f"{bakiye} TL")
                                                             
