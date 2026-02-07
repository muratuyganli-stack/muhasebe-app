import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pickle
import io
from PIL import Image

# --- AYARLAR ---
# Google Drive klasör linkindeki son karmaşık kodu buraya yapıştır:
FOLDER_ID = "KLASOR_ID_BURAYA" 

st.set_page_config(page_title="Otomatik Yedekli Cari Takip", layout="wide")

# Uygulama Hafızasını Başlat
if 'cariler' not in st.session_state:
    st.session_state.cariler = {}

# --- GOOGLE DRIVE YEDEKLEME FONKSİYONU ---
def drive_otomatik_yedekle():
    try:
        # Secrets'tan anahtarı çek
        info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(info)
        service = build('drive', 'v3', credentials=creds)
        
        # Veriyi hazırla (Görsellerle birlikte tüm sözlüğü paketle)
        data = pickle.dumps(st.session_state.cariler)
        fh = io.BytesIO(data)
        media = MediaIoBaseUpload(fh, mimetype='application/octet-stream')
        
        file_metadata = {'name': 'veresiye_otomatik_yedek.dat', 'parents': [FOLDER_ID]}
        
        # Drive'a yükle (Her seferinde yeni dosya oluşturur, istersen güncelleyebiliriz)
        service.files().create(body=file_metadata, media_body=media).execute()
        st.toast("✅ Google Drive'a otomatik yedeklendi!")
    except Exception as e:
        st.error(f"Yedekleme Hatası: {e}")

# --- ARAYÜZ ---
st.title("📂 Otomatik Yedekli Cari Takip")

sekme1, sekme2 = st.tabs(["📇 Cari Kart Tanımla", "💰 İşlem Yap ve Görüntüle"])

with sekme1:
    with st.form("cari_form"):
        isim = st.text_input("Müşteri / Firma Adı")
        tel = st.text_input("Telefon")
        limit = st.number_input("Borç Limiti (TL)", min_value=0, step=1)
        if st.form_submit_button("Kartı Oluştur") and isim:
            if isim not in st.session_state.cariler:
                st.session_state.cariler[isim] = {"Telefon": tel, "Limit": limit, "Islemler": []}
                st.success(f"{isim} kaydedildi.")
                drive_otomatik_yedekle() # Müşteri açılınca yedekle

with sekme2:
    if not st.session_state.cariler:
        st.info("Henüz müşteri kaydı yok.")
    else:
        secilen = st.selectbox("Müşteri Seç", list(st.session_state.cariler.keys()))
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("İşlem Ekle")
            tur = st.radio("Tür", ["Borçlandır", "Tahsilat"])
            tutar = st.number_input("Tutar (TL)", min_value=0, step=1)
            not_al = st.text_area("Açıklama")
            fotolar = st.file_uploader("Görseller", accept_multiple_files=True, type=['jpg','png'])
            
            if st.button("Kaydet ve Drive'a Gönder"):
                yeni_islem = {
                    "Tarih": pd.Timestamp.now().strftime("%d-%m-%Y %H:%M"),
                    "Tür": "Borç" if tur == "Borçlandır" else "Ödeme",
                    "Tutar": int(tutar),
                    "Not": not_al,
                    "Görseller": [Image.open(f) for f in fotolar] if fotolar else []
                }
                st.session_state.cariler[secilen]["Islemler"].append(yeni_islem)
                # İŞLEM BİTİNCE OTOMATİK YEDEKLE
                drive_otomatik_yedekle()
                st.success("Kayıt tamam!")

        with col2:
            st.subheader(f"Ekstre: {secilen}")
            bilgi = st.session_state.cariler[secilen]
            for islem in reversed(bilgi["Islemler"]):
                with st.expander(f"{islem['Tarih']} | {islem['Tür']} | {islem['Tutar']} TL"):
                    st.write(f"**Not:** {islem['Not']}")
                    if islem["Görseller"]:
                        cols = st.columns(4)
                        for idx, img in enumerate(islem["Görseller"]):
                            cols[idx % 4].image(img, use_container_width=True)

            islem_df = pd.DataFrame(bilgi["Islemler"])
            if not islem_df.empty:
                bakiye = islem_df[islem_df["Tür"]=="Borç"]["Tutar"].sum() - islem_df[islem_df["Tür"]=="Ödeme"]["Tutar"].sum()
                st.metric("Güncel Bakiye", f"{int(bakiye)} TL")
