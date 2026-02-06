import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

# Veritabanı v8 (Çoklu Fotoğraf Desteği İçin Yeni Tablo Yapısı)
def init_db():
    conn = sqlite3.connect('muhasebe_v8.db', check_same_thread=False)
    c = conn.cursor()
    # Ana işlemler tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, tip TEXT, kisi TEXT, miktar REAL, aciklama TEXT)''')
    # Fotoğraflar için ayrı tablo (Bir işleme birden fazla foto bağlamak için)
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar 
                 (islem_id INTEGER, foto BLOB)''')
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
        if y < 100: p.showPage(); y = 800
    p.line(100, y+10, 500, y+10)
    y -= 30
    p.setFont("Helvetica-Bold", 14)
    durum_metni = "TOPLAM BORC" if bakiye > 0 else "TOPLAM ALACAK"
    p.drawString(100, y, f"{durum_metni}: {abs(bakiye):,.2f} TL")
    p.save()
    buffer.seek(0)
    return buffer

conn = init_db()
st.set_page_config(page_title="Cari Takip Ultra v8", layout="wide")

# --- YAN MENÜ ---
with st.sidebar:
    st.header("➕ Yeni İşlem & Çoklu Foto")
    with st.form("yeni_islem", clear_on_submit=True):
        tip = st.selectbox("İşlem", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
        kisi = st.text_input("Müşteri Adı").strip().title()
        miktar = st.number_input("Tutar", min_value=0.0)
        aciklama = st.text_input("Not")
        # ÇOKLU FOTOĞRAF SEÇİMİ
        yuklenen_fotolar = st.file_uploader("Belge/Fiş Fotoğrafları (Birden fazla seçilebilir)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        
        if st.form_submit_button("Sisteme Kaydet"):
            if kisi and miktar > 0:
                c = conn.cursor()
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                # İşlemi kaydet
                c.execute("INSERT INTO islemler (tarih, tip, kisi, miktar, aciklama) VALUES (?,?,?,?,?)", (tarih, tip, kisi, miktar, aciklama))
                islem_id = c.lastrowid
                # Fotoğrafları kaydet
                for f in yuklenen_fotolar:
                    c.execute("INSERT INTO fotograflar (islem_id, foto) VALUES (?,?)", (islem_id, f.read()))
                conn.commit()
                st.success(f"{kisi} için {len(yuklenen_fotolar)} fotoğraflı kayıt eklendi!")
                st.rerun()

# --- ANA EKRAN ---
st.title("💼 Çoklu Görsel Destekli Cari Yönetim")
df = pd.read_sql_query("SELECT * FROM islemler", conn)

if not df.empty:
    musteriler = sorted(df['kisi'].unique())
    secilen = st.selectbox("🔍 Müşteri Seçin", ["Genel Durum"] + musteriler)
    
    if secilen != "Genel Durum":
        k_df = df[df['kisi'] == secilen].sort_values(by='tarih', ascending=False)
        satislar = k_df[k_df['tip'] == "Satis (Alacak Yaz)"]['miktar'].sum()
        tahsilatlar = k_df[k_df['tip'] == "Tahsilat (Borctan Dus)"]['miktar'].sum()
        bakiye = satislar - tahsilatlar
        
        # Durum Göstergesi
        if bakiye > 0: st.error(f"### 🔴 {secilen} Borcu: {bakiye:,.2f} TL")
        else: st.success(f"### 🟢 {secilen} Alacağı: {abs(bakiye):,.2f} TL")
            
        # PDF Butonu
        pdf_file = generate_pdf(secilen, k_df, bakiye)
        st.download_button("📥 PDF Ekstresini İndir", pdf_file, f"{secilen}_ekstre.pdf", "application/pdf")
        
        st.divider()
        # Hareketler ve Fotoğraflar
        for _, row in k_df.iterrows():
            with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
                st.write(f"**Not:** {row['aciklama']}")
                # Bu işleme ait tüm fotoları çek
                islem_fotolari = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
                if not islem_fotolari.empty:
                    cols = st.columns(len(islem_fotolari))
                    for idx, f_row in islem_fotolari.iterrows():
                        cols[idx].image(f_row['foto'], use_container_width=True)
                else:
                    st.info("Bu işleme ait fotoğraf yok.")
    else:
        st.dataframe(df, use_container_width=True)
else:
    st.info("Henüz kayıt yok. Sol menüden başlayın.")
        
