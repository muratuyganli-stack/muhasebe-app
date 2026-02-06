import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- 1. VERİTABANI (Tertemiz Yeni Başlangıç) ---
def init_db():
    conn = sqlite3.connect('havas_mavi_v41.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide", initial_sidebar_state="collapsed")

# --- 2. BEYAZ & MAVİ GÖRSEL TASARIM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FFFFFF; }
    
    /* Üst Bar - Canlı Mavi */
    .main-header {
        background: linear-gradient(135deg, #0052D4 0%, #4364F7 50%, #6FB1FC 100%);
        padding: 25px; border-radius: 0 0 35px 35px; color: white;
        text-align: center; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(67, 100, 247, 0.2);
    }
    
    /* Özet Kartı */
    .summary-card {
        background: #F0F7FF; padding: 20px; border-radius: 20px;
        display: flex; justify-content: space-around; align-items: center;
        margin-bottom: 25px; border: 1px solid #D1E3FF;
    }

    /* Müşteri Kartları */
    .customer-card {
        background: white; padding: 18px; border-radius: 18px;
        margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;
        border: 1px solid #E2E8F0; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* Mavi Avatar */
    .avatar-circle {
        width: 50px; height: 50px; background: #0052D4; border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: #FFFFFF; font-size: 22px; margin-right: 15px;
    }

    /* Mavi Butonlar */
    div.stButton > button {
        background: #0052D4; color: white; border-radius: 12px;
        height: 3.2em; font-weight: 700; border: none; width: 100%;
        box-shadow: 0 4px 10px rgba(0, 82, 212, 0.2);
    }
    div.stButton > button:hover { background: #0041A8; }
    </style>
    """, unsafe_allow_html=True)

# --- PDF MOTORU ---
def generate_pdf(df, m_ad):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16); c.drawString(50, 800, f"HAVAS AHSAP - {m_ad}")
    c.setFont("Helvetica", 11); y = 760
    for _, r in df.iterrows():
        c.drawString(50, y, f"{r['tarih']} | {r['tip']} | {r['miktar']:,} TL | {r['aciklama']}")
        y -= 20
        if y < 50: c.showPage(); y = 800
    c.save(); return buf.getvalue()

st.markdown('<div class="main-header"><h1 style="margin:0; font-size:26px; font-weight:900; letter-spacing:1px;">HAVAS AHŞAP</h1></div>', unsafe_allow_html=True)

df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)

# --- AKIŞ ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    col1, col2 = st.columns([3, 1])
    if col1.button("⬅️ GERİ"): del st.session_state['secili_id']; st.rerun()
    
    m_i_df = df_i[df_i['musteri_id'] == m_id]
    if not m_i_df.empty:
        col2.download_button("📩 PDF", generate_pdf(m_i_df, m_bilgi['ad']), f"{m_bilgi['ad']}.pdf")

    st.subheader(f"👤 {m_bilgi['ad']}")

    with st.container(border=True):
        st.markdown("### 📸 İŞLEM EKLE")
        with st.form("mavi_form", clear_on_submit=True):
            t = st.selectbox("İşlem", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            m = st.number_input("Tutar (₺)", min_value=0, step=1)
            n = st.text_input("Açıklama")
            fotos = st.file_uploader("📷 Fotoğraf Makinesi / Galeri", accept_multiple_files=True)
            if st.form_submit_button("✅ KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(m), t, n))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # Geçmiş ve Fotolar
    for _, row in m_i_df.sort_values(by='id', ascending=False).iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)
            if st.button("Sil", key=f"d_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

else:
    # ANA SAYFA ÖZET
    aldim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
    verdim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum())
    st.markdown(f"""
    <div class="summary-card">
        <div style="text-align:center;"><small>ALDIĞIM</small><br><b style="color:#2F855A;font-size:22px;">{aldim:,} ₺</b></div>
        <div style="text-align:center;"><small>VERDİĞİM</small><br><b style="color:#C53030;font-size:22px;">{verdim:,} ₺</b></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ YENİ MÜŞTERİ EKLE"): st.session_state['y_m'] = True
    if st.session_state.get('y_m'):
        with st.form("y_m_f"):
            ad = st.text_input("Ad Soyad")
            if st.form_submit_button("REHBERE EKLE"):
                conn.cursor().execute("INSERT INTO musteriler (ad) VALUES (?)", (ad,))
                conn.commit(); st.session_state['y_m'] = False; st.rerun()

    st.divider()
    search = st.text_input("🔍 Müşteri Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""
            <div class="customer-card">
                <div style="display:flex; align-items:center;">
                    <div class="avatar-circle">{m['ad'][0].upper()}</div>
                    <div style="font-weight:700; font-size:17px; color:#1A365D;">{m['ad']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:800; font-size:18px; color:{'#C53030' if bakiye > 0 else '#2F855A'};">{abs(bakiye):,} ₺</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"DETAY: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()

with st.sidebar:
    if not df_i.empty:
        output = io.BytesIO()
        df_i.to_excel(output, index=False)
        st.download_button("📥 YEDEKLE (EXCEL)", output.getvalue(), "Havas_Mavi_Yedek.xlsx")
        
