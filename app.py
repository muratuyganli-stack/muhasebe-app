import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- 1. VERİTABANI (Mevcut yapı korunuyor) ---
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

# --- 2. GÖRSEL TASARIM (Dashboard Eklenmiş Hali) ---
st.markdown("""
    <style>
    .main-header { background: #0052D4; padding: 20px; border-radius: 0 0 25px 25px; color: white; text-align: center; margin-bottom: 20px; }
    .dashboard-card { 
        background: #FFFFFF; padding: 15px; border-radius: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px;
        display: flex; justify-content: space-around; align-items: center; border: 1px solid #E0E7FF;
    }
    .dash-item { text-align: center; }
    .dash-label { font-size: 12px; color: #64748B; font-weight: bold; text-transform: uppercase; }
    .dash-val { font-size: 22px; font-weight: 800; color: #1E3A8A; }
    .action-btn { background: #F0F7FF; border: 1px solid #0052D4; border-radius: 10px; padding: 10px; text-align: center; color: #0052D4; font-weight: bold; text-decoration: none; display: inline-block; width: 100%; }
    .customer-card { background: white; padding: 15px; border-radius: 18px; margin-bottom: 10px; border-left: 8px solid #0052D4; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PDF MOTORU ---
def generate_pro_report(df, m_ad):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16); c.drawString(50, 800, f"HAVAS AHSAP - {m_ad} RAPORU")
    c.setFont("Helvetica", 10); y = 760
    for _, r in df.iterrows():
        c.drawString(50, y, f"{r['tarih']} | {r['tip']} | {r['miktar']:,} TL | {r['aciklama']}"); y -= 20
    c.save(); return buf.getvalue()

st.markdown('<div class="main-header"><h1>HAVAS AHŞAP</h1></div>', unsafe_allow_html=True)

# Verileri Çek
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- 4. YENİ: OTOMATİK BAKİYE ÖZETİ (DASHBOARD) ---
if 'secili_id' not in st.session_state:
    toplam_aldigim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
    toplam_verdigim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum())
    disaridaki_para = toplam_verdigim - toplam_aldigim
    musteri_sayisi = len(df_m)

    st.markdown(f"""
    <div class="dashboard-card">
        <div class="dash-item"><div class="dash-label">Müşteri Sayısı</div><div class="dash-val">{musteri_sayisi}</div></div>
        <div style="width:1px; height:40px; background:#E2E8F0;"></div>
        <div class="dash-item"><div class="dash-label">Toplam Tahsilat</div><div class="dash-val" style="color:#10B981;">{toplam_aldigim:,} ₺</div></div>
        <div style="width:1px; height:40px; background:#E2E8F0;"></div>
        <div class="dash-item"><div class="dash-label">Dışarıdaki Alacak</div><div class="dash-val" style="color:#EF4444;">{disaridaki_para:,} ₺</div></div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. EKRAN KONTROLÜ (v45'teki her şey aynen korunuyor) ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ LİSTEYE DÖN"): del st.session_state['secili_id']; st.rerun()
    
    st.title(f"👤 {m_bilgi['ad']}")
    
    # İletişim Butonları
    c1, c2, c3 = st.columns(3)
    if m_bilgi['tel']:
        wa_url = f"https://wa.me/90{m_bilgi['tel'].replace(' ', '')}"
        c1.markdown(f'<a href="{wa_url}" target="_blank" class="action-btn">💬 WhatsApp</a>', unsafe_allow_html=True)
        c2.markdown(f'<a href="tel:{m_bilgi["tel"]}" class="action-btn">📞 Ara</a>', unsafe_allow_html=True)
    if m_bilgi['eposta']:
        c3.markdown(f'<a href="mailto:{m_bilgi["eposta"]}" class="action-btn">📧 E-posta</a>', unsafe_allow_html=True)

    # PDF Rapor
    m_i_df = df_i[df_i['musteri_id'] == m_id]
    if not m_i_df.empty:
        pdf = generate_pro_report(m_i_df, m_bilgi['ad'])
        st.download_button("📥 PDF RAPOR AL", pdf, f"{m_bilgi['ad']}_Rapor.pdf")

    # Çoklu Fotoğraf ve İşlem
    with st.container(border=True):
        st.markdown("### 📸 YENİ İŞLEM & FOTOĞRAFLAR")
        with st.form("islem_form_v46", clear_on_submit=True):
            tip = st.selectbox("İşlem", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (TL)", min_value=0, step=1)
            not_ = st.text_input("Not")
            fotos = st.file_uploader("📷 Fotoğraflar (Çoklu)", accept_multiple_files=True)
            if st.form_submit_button("✅ KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # Geçmiş ve Fotolar (Görsel Hafıza)
    for _, row in m_i_df.sort_values(by='id', ascending=False).iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} TL"):
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)

else:
    # Ana Liste Ekranı
    if st.button("➕ YENİ MÜŞTERİ EKLE"): st.session_state['y_m'] = True
    if st.session_state.get('y_m'):
        with st.form("yeni_m_form"):
            ad = st.text_input("Ad Soyad *")
            tel = st.text_input("Telefon")
            mail = st.text_input("E-posta")
            if st.form_submit_button("KAYDET"):
                conn.cursor().execute("INSERT INTO musteriler (ad, tel, eposta) VALUES (?,?,?)", (ad, tel, mail))
                conn.commit(); st.session_state['y_m'] = False; st.rerun()

    search = st.text_input("🔍 Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""<div class="customer-card"><b>{m['ad']}</b><br><b style="color:{'#EF4444' if bakiye > 0 else '#10B981'}; font-size:20px;">{abs(bakiye):,} TL</b></div>""", unsafe_allow_html=True)
            if st.button(f"DETAY: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()

# Yedekleme (Sidebar)
with st.sidebar:
    st.header("⚙️ YEDEKLEME")
    if not df_i.empty:
        output = io.BytesIO()
        df_i.to_excel(output, index=False, engine='openpyxl')
        st.download_button("📥 EXCEL YEDEK AL", output.getvalue(), "Havas_Ahsap_Yedek.xlsx")
        
