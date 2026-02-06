import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- 1. VERİTABANI (Fotoğraf & Cari Veri Hafızası) ---
def init_db():
    conn = sqlite3.connect('havas_ahsap_v39.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, adres TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    # Fotoğraflar asla silinmez, burada saklanır
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide", initial_sidebar_state="collapsed")

# --- 2. GÖRSEL TASARIM (Elite & Modern) ---
st.markdown("""
    <style>
    .avatar-circle {
        width: 50px; height: 50px; background: #1A1A1A; border-radius: 15px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: #FFFFFF; font-size: 20px; margin-right: 15px;
    }
    .main-header {
        background: linear-gradient(135deg, #1A365D 0%, #2B6CB0 100%);
        padding: 20px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin-bottom: 20px;
    }
    .customer-card {
        background: white; padding: 15px; border-radius: 18px; margin-bottom: 12px;
        display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF OLUŞTURMA (WhatsApp Paylaşımı İçin) ---
def generate_whatsapp_pdf(df, m_ad):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 800, f"HAVAS AHSAP - {m_ad} EKSTRESI")
    c.setFont("Helvetica", 10)
    y = 770
    c.drawString(50, y, "Tarih | Islem | Tutar | Not"); y -= 20
    for _, r in df.iterrows():
        c.drawString(50, y, f"{r['tarih']} | {r['tip']} | {r['miktar']} TL | {r['aciklama']}"); y -= 20
    c.save()
    return buf.getvalue()

st.markdown('<div class="main-header"><h1 style="margin:0;">HAVAS AHŞAP</h1></div>', unsafe_allow_html=True)

# --- EKRAN KONTROLÜ ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = pd.read_sql_query(f"SELECT * FROM musteriler WHERE id={m_id}", conn).iloc[0]
    
    col_back, col_pdf = st.columns([2, 1])
    if col_back.button("⬅️ LİSTEYE DÖN"):
        del st.session_state['secili_id']; st.rerun()
    
    # WHATSAPP PDF BUTONU
    m_islemler = pd.read_sql_query(f"SELECT * FROM islemler WHERE musteri_id={m_id}", conn)
    if not m_islemler.empty:
        pdf_data = generate_whatsapp_pdf(m_islemler, m_bilgi['ad'])
        col_pdf.download_button("📩 WhatsApp PDF", pdf_data, f"{m_bilgi['ad']}.pdf")

    st.subheader(f"👤 {m_bilgi['ad']}")
    
    # İŞLEM VE FOTOĞRAF (ASLA UNUTULMAYACAK KISIM)
    with st.container(border=True):
        st.markdown("### 📸 İŞLEM VE FOTOĞRAF EKLE")
        with st.form("islem_f", clear_on_submit=True):
            tip = st.selectbox("İşlem", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (TL)", min_value=0, step=1)
            not_ = st.text_input("Açıklama")
            fotos = st.file_uploader("📷 Fotoğraf Çek / Seç", accept_multiple_files=True)
            if st.form_submit_button("✅ KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # GEÇMİŞ VE FOTOLAR
    st.divider()
    for _, row in m_islemler.sort_values(by="id", ascending=False).iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)

else:
    # ANA LİSTE (Siyah İkonlar)
    df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
    df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
    
    if st.button("➕ YENİ MÜŞTERİ"): st.session_state['yeni_m'] = True
    if st.session_state.get('yeni_m'):
        with st.form("y_m"):
            ad = st.text_input("Müşteri Adı")
            if st.form_submit_button("KAYDET"):
                conn.cursor().execute("INSERT INTO musteriler (ad) VALUES (?)", (ad,))
                conn.commit(); st.session_state['yeni_m'] = False; st.rerun()

    search = st.text_input("🔍 Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""
            <div class="customer-card">
                <div style="display:flex; align-items:center;">
                    <div class="avatar-circle">{m['ad'][0]}</div>
                    <div style="font-weight:700;">{m['ad']}</div>
                </div>
                <div style="font-weight:800; color:{'#C53030' if bakiye > 0 else '#2F855A'};">{abs(bakiye):,} ₺</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Gör: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
                
