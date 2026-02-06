import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# Veritabanı v5
def init_db():
    conn = sqlite3.connect('muhasebe_v5.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (tarih TEXT, tip TEXT, kisi TEXT, miktar REAL, aciklama TEXT, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="Cari Takip Ultra", page_icon="📈", layout="wide")

# Verileri Çek
df = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- YAN MENÜ ---
with st.sidebar:
    st.title("⚙️ İşlem Merkezi")
    with st.form("kayit_formu", clear_on_submit=True):
        tip = st.selectbox("İşlem Tipi", ["Satış (Alacak Yaz)", "Tahsilat (Borçtan Düş)"])
        kisi = st.text_input("Müşteri Adı").strip().title()
        miktar = st.number_input("Tutar (TL)", min_value=0.0, format="%.2f")
        aciklama = st.text_area("İşlem Notu")
        foto = st.file_uploader("Belge/Fiş Fotoğrafı", type=['jpg', 'png', 'jpeg'])
        
        if st.form_submit_button("Sisteme İşle"):
            if kisi and miktar > 0:
                foto_bytes = foto.read() if foto else None
                c = conn.cursor()
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO islemler VALUES (?,?,?,?,?,?)", 
                          (tarih, tip, kisi, miktar, aciklama, foto_bytes))
                conn.commit()
                st.success(f"Kayıt Tamam: {kisi}")
                st.rerun()

# --- ANA EKRAN ---
st.title("💼 Profesyonel Cari Yönetimi")

if not df.empty:
    kisiler = sorted(df['kisi'].unique())
    secilen_kisi = st.selectbox("👤 Müşteri Seçimi", ["Genel Özet"] + kisiler)

    if secilen_kisi != "Genel Özet":
        kisi_df = df[df['kisi'] == secilen_kisi].sort_values(by='tarih', ascending=False)
        
        # Bakiye Hesabı
        satis = kisi_df[kisi_df['tip'] == "Satış (Alacak Yaz)"]['miktar'].sum()
        tahsilat = kisi_df[kisi_df['tip'] == "Tahsilat (Borçtan Düş)"]['miktar'].sum()
        bakiye = satis - tahsilat
        
        # Renkli Durum Çubuğu
        if bakiye > 0:
            st.error(f"### 🔴 {secilen_kisi} Toplam Borcu: {bakiye:,.2f} TL")
        elif bakiye < 0:
            st.success(f"### 🟢 {secilen_kisi} Alacak Bakiyesi: {abs(bakiye):,.2f} TL")
        else:
            st.info(f"### 🔵 {secilen_kisi} Hesabı Kapalı")

        # Excel/CSV Dökümü Al (PDF alternatifi olarak en kolayı)
        csv = kisi_df[['tarih', 'tip', 'miktar', 'aciklama']].to_csv(index=False).encode('utf-8-sig')
        st.download_button(f"📄 {secilen_kisi} Hesap Ekstresini İndir", csv, f"{secilen_kisi}_ekstre.csv", "text/csv")

        st.divider()
        
        # Hareket Listesi
        for index, row in kisi_df.iterrows():
            with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if row['foto']:
                        st.image(row['foto'], use_container_width=True)
                with col2:
                    st.write(f"**Detay:** {row['aciklama']}")
    else:
        # Genel Finansal Durum
        toplam_alacak = df[df['tip'] == "Satış (Alacak Yaz)"]['miktar'].sum() - df[df['tip'] == "Tahsilat (Borçtan Düş)"]['miktar'].sum()
        st.metric("Piyasadaki Toplam Alacağınız", f"{toplam_alacak:,.2f} TL")
        st.dataframe(df, use_container_width=True)
else:
    st.warning("Başlamak için sol menüden ilk müşterinizi ekleyin.")
