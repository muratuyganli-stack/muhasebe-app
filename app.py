import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

# Veritabanı v6
def init_db():
    conn = sqlite3.connect('muhasebe_v6.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS islemler 
                 (tarih TEXT, tip TEXT, kisi TEXT, miktar REAL, aciklama TEXT, foto BLOB)''')
    conn.commit()
    return conn

def generate_pdf(kisi, df_kisi, bakiye):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, f"HESAP EKSTRESI: {kisi}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 780, f"Tarih: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    p.line(100, 770, 500, 770)
    
    y = 750
    p.drawString(100, y, "Tarih")
    p.drawString(200, y, "Islem")
    p.drawString(350, y, "Miktar")
    y -= 20
    
    p.setFont("Helvetica", 10)
    for index, row in df_kisi.iterrows():
        p.drawString(100, y, str(row['tarih']))
        p.drawString(200, y, str(row['tip']))
        p.drawString(350, y, f"{row['miktar']:.2f} TL")
        y -= 20
        if y < 100:
            p.showPage()
            y = 800
            
    p.line(100, y, 500, y)
    y -= 30
    p.setFont("Helvetica-Bold", 14)
    durum = "TOPLAM BORC" if bakiye > 0 else "TOPLAM ALACAK"
    p.drawString(100, y, f"{durum}: {abs(bakiye):,.2f} TL")
    
    p.save()
    buffer.seek(0)
    return buffer

conn = init_db()
st.set_page_config(page_title="Cari Takip PDF", layout="wide")
df = pd.read_sql_query("SELECT * FROM islemler", conn)

with st.sidebar:
    st.title("⚙️ Islem Ekle")
    with st.form("kayit", clear_on_submit=True):
        tip = st.selectbox("Tip", ["Satış (Alacak Yaz)", "Tahsilat (Borçtan Düş)"])
        kisi = st.text_input("Müşteri Adı").strip().title()
        miktar = st.number_input("Tutar", min_value=0.0)
        aciklama = st.text_area("Not")
        if st.form_submit_button("Kaydet"):
            c = conn.cursor(); tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
            c.execute("INSERT INTO islemler VALUES (?,?,?,?,?,?)", (tarih, tip, kisi, miktar, aciklama, None))
            conn.commit(); st.rerun()

st.title("💼 Cari Takip ve PDF")
if not df.empty:
    kisiler = sorted(df['kisi'].unique())
    secilen = st.selectbox("Müşteri Seç", ["Genel"] + kisiler)
    
    if secilen != "Genel":
        k_df = df[df['kisi'] == secilen].sort_values(by='tarih', ascending=False)
        bakiye = k_df[k_df['tip'].contains("Satış")]['miktar'].sum() - k_df[k_df['tip'].contains("Tahsilat")]['miktar'].sum()
        
        # PDF BUTONU
        pdf_data = generate_pdf(secilen, k_df, bakiye)
        st.download_button(label="📥 PDF Ekstresi İndir", data=pdf_data, file_name=f"{secilen}_ekstre.pdf", mime="application/pdf")
        
        if bakiye > 0: st.error(f"Borç: {bakiye} TL")
        else: st.success(f"Alacak: {abs(bakiye)} TL")
        st.dataframe(k_df)
