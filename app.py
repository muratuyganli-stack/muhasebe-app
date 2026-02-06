import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

# Veritabanı v7 (Temiz Kurulum)
def init_db():
    conn = sqlite3.connect('muhasebe_v7.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (tarih TEXT, tip TEXT, kisi TEXT, miktar REAL, aciklama TEXT)''')
    conn.commit()
    return conn

# PDF Oluşturma Fonksiyonu
def generate_pdf(kisi, df_kisi, bakiye):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, f"HESAP EKSTRESI: {kisi}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Tarih: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    p.line(100, 770, 500, 770)
    
    y = 740
    p.drawString(100, y, "Tarih")
    p.drawString(250, y, "Islem Tipi")
    p.drawString(400, y, "Miktar")
    y -= 20
    
    p.setFont("Helvetica", 10)
    for index, row in df_kisi.iterrows():
        p.drawString(100, y, str(row['tarih']))
        p.drawString(250, y, str(row['tip']))
        p.drawString(400, y, f"{row['miktar']:,.2f} TL")
        y -= 20
        if y < 100:
            p.showPage()
            y = 800
            
    p.line(100, y+10, 500, y+10)
    y -= 30
    p.setFont("Helvetica-Bold", 14)
    durum_metni = "TOPLAM BORC" if bakiye > 0 else "TOPLAM ALACAK"
    p.drawString(100, y, f"{durum_metni}: {abs(bakiye):,.2f} TL")
    p.save()
    buffer.seek(0)
    return buffer

conn = init_db()
st.set_page_config(page_title="Cari Takip v7", layout="wide")

# Veri Çekme
df = pd.read_sql_query("SELECT * FROM islemler", conn)

with st.sidebar:
    st.header("➕ Yeni Islem")
    with st.form("yeni_islem", clear_on_submit=True):
        tip = st.selectbox("Islem", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
        kisi = st.text_input("Musteri Adi").strip().title()
        miktar = st.number_input("Tutar", min_value=0.0)
        aciklama = st.text_input("Not")
        if st.form_submit_button("Kaydet"):
            if kisi and miktar > 0:
                c = conn.cursor()
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                c.execute("INSERT INTO islemler VALUES (?,?,?,?,?)", (tarih, tip, kisi, miktar, aciklama))
                conn.commit()
                st.rerun()

st.title("💼 Cari Yönetim & PDF Sistemi")

if not df.empty:
    musteriler = sorted(df['kisi'].unique())
    secilen = st.selectbox("🔍 Musteri Secin", ["Genel Durum"] + musteriler)
    
    if secilen != "Genel Durum":
        k_df = df[df['kisi'] == secilen].sort_values(by='tarih', ascending=False)
        
        # Bakiye Hesaplama
        satislar = k_df[k_df['tip'] == "Satis (Alacak Yaz)"]['miktar'].sum()
        tahsilatlar = k_df[k_df['tip'] == "Tahsilat (Borctan Dus)"]['miktar'].sum()
        bakiye = satislar - tahsilatlar
        
        # Renkli Bakiye
        if bakiye > 0:
            st.error(f"### 🔴 {secilen} Borcu: {bakiye:,.2f} TL")
        else:
            st.success(f"### 🟢 {secilen} Alacagi: {abs(bakiye):,.2f} TL")
            
        # PDF BUTONU
        pdf_file = generate_pdf(secilen, k_df, bakiye)
        st.download_button("📥 PDF Olarak Indir", pdf_file, f"{secilen}_ekstre.pdf", "application/pdf")
        
        st.dataframe(k_df[['tarih', 'tip', 'miktar', 'aciklama']], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
else:
    st.info("Henüz kayit yok. Yan menuden ekleyin.")
        
