import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- 1. VERİTABANI (Gelişmiş Rehber ve Hafıza) ---
def init_db():
    conn = sqlite3.connect('havas_pro_v45.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, eposta TEXT, adres TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide", initial_sidebar_state="collapsed")

# --- 2. GÖRSEL TASARIM (Mavi & Beyaz Elite) ---
st.markdown("""
    <style>
    .main-header { background: #0052D4; padding: 20px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin-bottom: 20px; }
    .action-btn { background: #F0F7FF; border: 1px solid #0052D4; border-radius: 10px; padding: 10px; text-align: center; color: #0052D4; font-weight: bold; text-decoration: none; display: inline-block; width: 100%; }
    .customer-card { background: white; padding: 15px; border-radius: 18px; margin-bottom: 10px; border-left: 8px solid #0052D4; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. RAPORLAMA MOTORU (PDF) ---
def generate_pro_report(df, m_ad):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16); c.drawString(50, 800, f"HAVAS AHSAP - {m_ad} RAPORU")
    c.setFont("Helvetica", 10); y = 760
    c.drawString(50, y, "Tarih | Islem | Tutar | Aciklama"); y -= 20
    for _, r in df.iterrows():
        c.drawString(50, y, f"{r['tarih']} | {r['tip']} | {r['miktar']:,} TL | {r['aciklama']}"); y -= 20
    c.save(); return buf.getvalue()

st.markdown('<div class="main-header"><h1>HAVAS AHŞAP</h1></div>', unsafe_allow_html=True)

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

if 'secili_id' in st.session_state:
    # --- MÜŞTERİ DETAY VE İLETİŞİM PANELİ ---
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ LISTEYE DON"): del st.session_state['secili_id']; st.rerun()
    
    st.title(f"👤 {m_bilgi['ad']}")
    
    # WHATSAPP, TEL VE E-POSTA BUTONLARI
    c1, c2, c3 = st.columns(3)
    if m_bilgi['tel']:
        # WhatsApp Linki
        wa_url = f"https://wa.me/90{m_bilgi['tel'].replace(' ', '')}"
        c1.markdown(f'<a href="{wa_url}" target="_blank" class="action-btn">💬 WhatsApp</a>', unsafe_allow_html=True)
        c2.markdown(f'<a href="tel:{m_bilgi["tel"]}" class="action-btn">📞 Ara</a>', unsafe_allow_html=True)
    if m_bilgi['eposta']:
        c3.markdown(f'<a href="mailto:{m_bilgi["eposta"]}" class="action-btn">📧 E-posta</a>', unsafe_allow_html=True)

    # RAPORLAMA (PDF)
    st.divider()
    m_i_df = df_i[df_i['musteri_id'] == m_id]
    if not m_i_df.empty:
        pdf = generate_pro_report(m_i_df, m_bilgi['ad'])
        st.download_button("📥 PROFESYONEL PDF RAPOR AL (WhatsApp/Mail Paylaş)", pdf, f"{m_bilgi['ad']}_Rapor.pdf")

    # ÇOKLU FOTOĞRAF VE İŞLEM EKLEME (UNUTULMAYAN KISIM)
    with st.container(border=True):
        st.markdown("### 📸 YENI ISLEM & COKLU FOTOGRAF")
        with st.form("pro_form", clear_on_submit=True):
            tip = st.selectbox("İşlem", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (TL)", min_value=0, step=1)
            not_ = st.text_input("Açıklama")
            fotos = st.file_uploader("📷 Fotoğrafları Seç / Çek (Çoklu)", accept_multiple_files=True)
            if st.form_submit_button("✅ KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # GEÇMİŞ VE FOTOLAR
    for _, row in m_i_df.sort_values(by='id', ascending=False).iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} TL"):
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)

else:
    # --- ANA LİSTE ---
    if st.button("➕ YENI MUSTERI EKLE"): st.session_state['y_m'] = True
    if st.session_state.get('y_m'):
        with st.form("y_m_f"):
            ad = st.text_input("Ad Soyad *")
            tel = st.text_input("Telefon (Örn: 5321234455)")
            mail = st.text_input("E-posta")
            if st.form_submit_button("KAYDET"):
                conn.cursor().execute("INSERT INTO musteriler (ad, tel, eposta) VALUES (?,?,?)", (ad, tel, mail))
                conn.commit(); st.session_state['y_m'] = False; st.rerun()

    search = st.text_input("🔍 Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""<div class="customer-card"><b>{m['ad']}</b><br><b style="color:{'red' if bakiye > 0 else 'green'}; font-size:20px;">{abs(bakiye):,} TL</b></div>""", unsafe_allow_html=True)
            if st.button(f"DETAY: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()

# --- TÜM VERİLERİ YEDEKLEME (EXCEL) ---
with st.sidebar:
    st.header("⚙️ YEDEKLEME")
    if not df_i.empty:
        output = io.BytesIO()
        df_i.to_excel(output, index=False, engine='openpyxl')
        st.download_button("📥 TUM VERILERI EXCEL YEDEKLE", output.getvalue(), "Havas_Ahsap_Yedek.xlsx")
    
