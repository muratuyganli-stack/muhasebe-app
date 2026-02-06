import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Veritabanı v4 (Temiz bir başlangıç için)
def init_db():
    conn = sqlite3.connect('muhasebe_v4.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (tarih TEXT, tip TEXT, kisi TEXT, miktar REAL, aciklama TEXT, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="Cari Takip Pro", page_icon="👥", layout="wide")

# Verileri Çek
df = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- YAN MENÜ: KAYIT ---
with st.sidebar:
    st.header("➕ Yeni İşlem")
    with st.form("kayit_formu", clear_on_submit=True):
        tip = st.selectbox("İşlem Türü", ["Satış (Alacak Yaz)", "Tahsilat (Borçtan Düş)"])
        kisi = st.text_input("Müşteri Adı").strip().title()
        miktar = st.number_input("Tutar (TL)", min_value=0.0)
        foto = st.file_uploader("Belge Fotoğrafı", type=['jpg', 'jpeg', 'png'])
        aciklama = st.text_area("Not")
        
        if st.form_submit_button("Kaydet"):
            if kisi:
                foto_bytes = foto.read() if foto else None
                c = conn.cursor()
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO islemler VALUES (?,?,?,?,?,?)", 
                          (tarih, tip, kisi, miktar, aciklama, foto_bytes))
                conn.commit()
                st.success(f"{kisi} kaydı eklendi!")
                st.rerun()

# --- ANA SAYFA: CARİ ANALİZ ---
st.title("👥 Müşteri Cari Yönetimi")

if not df.empty:
    tum_kisiler = sorted(df['kisi'].unique())
    secilen_kisi = st.selectbox("🔍 Müşteri Seçin", ["Tümü"] + tum_kisiler)

    if secilen_kisi != "Tümü":
        kisi_df = df[df['kisi'] == secilen_kisi].sort_values(by='tarih', ascending=False)
        
        # Bakiye Hesaplama
        # Satışlar müşterinin borcudur (senin alacağın), Tahsilatlar borcun ödenmesidir.
        toplam_satis = kisi_df[kisi_df['tip'] == "Satış (Alacak Yaz)"]['miktar'].sum()
        toplam_tahsilat = kisi_df[kisi_df['tip'] == "Tahsilat (Borçtan Düş)"]['miktar'].sum()
        guncel_borc = toplam_satis - toplam_tahsilat
        
        # --- RENKLİ GÖSTERGE ---
        if guncel_borc > 0:
            # Müşteri borçlu (Kırmızı)
            st.error(f"### ⚠️ {secilen_kisi} Toplam Borcu: {guncel_borc:,.2f} TL")
        elif guncel_borc < 0:
            # Müşteri alacaklı (Yeşil)
            st.success(f"### ✅ {secilen_kisi} Alacak Bakiyesi: {abs(guncel_borc):,.2f} TL")
        else:
            # Borç sıfır (Mavi/Nötr)
            st.info(f"### ℹ️ {secilen_kisi} Hesabı Kapalı (0.00 TL)")

        st.divider()
        
        # Detaylar
        c1, c2 = st.columns(2)
        c1.metric("Toplam Satış", f"{toplam_satis} TL")
        c2.metric("Toplam Tahsilat", f"{toplam_tahsilat} TL")

        st.subheader("📑 Hesap Ekstresi")
        st.dataframe(kisi_df[['tarih', 'tip', 'miktar', 'aciklama']], use_container_width=True)
    else:
        st.info("Lütfen detaylarını görmek istediğiniz müşteriyi seçin.")
        st.dataframe(df, use_container_width=True)
else:
    st.warning("Henüz kayıt yok.")
            
