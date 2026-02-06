import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- VERİTABANI AYARLARI ---
def init_db():
    conn = sqlite3.connect('havas_elite_v44.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, eposta TEXT, adres TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide", initial_sidebar_state="collapsed")

# --- VİDEODAKİ GİBİ MODERN TASARIM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F7F9FC; }
    
    .main-header {
        background: #FFFFFF; padding: 15px; border-radius: 0 0 20px 20px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .brand-title { color: #1E3A8A; font-weight: 800; font-size: 20px; }

    .summary-card {
        background: white; padding: 20px; border-radius: 20px;
        margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .stat-val-aldim { color: #22C55E; font-size: 24px; font-weight: 800; }
    .stat-val-verdim { color: #EF4444; font-size: 24px; font-weight: 800; }

    .customer-list-card {
        background: white; padding: 15px; border-radius: 18px;
        margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;
        border: 1px solid #E2E8F0;
    }
    .avatar-box {
        width: 48px; height: 48px; background: #EBF8FF; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: #3182CE; font-size: 20px; margin-right: 15px;
    }

    /* Müşteri Ekle Butonu */
    .stButton>button {
        background: #3182CE; color: white; border-radius: 15px;
        height: 3.5em; font-weight: 700; border: none; width: 100%;
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# --- PDF VE RAPORLAMA FONKSİYONU ---
def generate_pdf(df, m_ad):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, f"HAVAS AHSAP - {m_ad} EKSTRESI")
    c.setFont("Helvetica", 10)
    y = 760
    for _, r in df.iterrows():
        c.drawString(50, y, f"{r['tarih']} | {r['tip']} | {r['miktar']:,} TL | {r['aciklama']}")
        y -= 20
        if y < 50: c.showPage(); y = 800
    c.save()
    return buf.getvalue()

# --- ÜST PANEL ---
st.markdown('<div class="main-header"><div class="brand-title">📖 HAVAS AHŞAP</div><div>🌐 ⚙️</div></div>', unsafe_allow_html=True)

df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)

if 'secili_id' in st.session_state:
    # --- MÜŞTERİ DETAY SAYFASI ---
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    col_back, col_pdf = st.columns([3, 1])
    if col_back.button("⬅️ GERİ DÖN"):
        del st.session_state['secili_id']; st.rerun()
    
    # PDF Raporlama & WhatsApp Hazırlığı
    m_i_df = df_i[df_i['musteri_id'] == m_id]
    if not m_i_df.empty:
        pdf_data = generate_pdf(m_i_df, m_bilgi['ad'])
        col_pdf.download_button("📩 PDF AL", pdf_data, f"{m_bilgi['ad']}.pdf")

    st.markdown(f"## 👤 {m_bilgi['ad']}")
    st.info(f"📞 {m_bilgi['tel'] if m_bilgi['tel'] else 'Tel Yok'} | 📧 {m_bilgi['eposta'] if m_bilgi['eposta'] else 'E-posta Yok'}")

    # YENİ İŞLEM EKLEME (VİDEODAKİ GİBİ)
    with st.container(border=True):
        st.markdown("### ➕ YENİ İŞLEM")
        with st.form("hizli_islem", clear_on_submit=True):
            col_t, col_m = st.columns(2)
            t = col_t.selectbox("İşlem Tipi", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            m = col_m.number_input("Tutar (₺)", min_value=0, step=1)
            tarih_sec = st.date_input("İşlem Tarihi", datetime.now())
            n = st.text_area("Açıklama / Not")
            fotos = st.file_uploader("📷 FOTOĞRAF ÇEK / EKLE (ÇOKLU)", accept_multiple_files=True)
            if st.form_submit_button("SİSTEME KAYDET"):
                c = conn.cursor()
                t_str = tarih_sec.strftime("%d-%m-%Y")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), t_str, int(m), t, n))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.success("İşlem Başarıyla Kaydedildi!"); st.rerun()

    # GEÇMİŞ İŞLEMLER VE FOTOĞRAF GALERİSİ
    st.divider()
    for _, row in m_i_df.sort_values(by='id', ascending=False).iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            st.write(f"📝 {row['aciklama']}")
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)
            if st.button("🗑️ SİL", key=f"d_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

else:
    # --- ANA LİSTE SAYFASI ---
    aldim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
    verdim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum())
    st.markdown(f"""
    <div class="summary-card">
        <div style="text-align:center;"><small style="color:#666;">ALDĞIM</small><br><b class="stat-val-aldim">{aldim:,} ₺</b></div>
        <div style="width:1px; height:40px; background:#E2E8F0;"></div>
        <div style="text-align:center;"><small style="color:#666;">VERDİĞİM</small><br><b class="stat-val-verdim">{verdim:,} ₺</b></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ MÜŞTERİ EKLE"): st.session_state['y_m'] = True
    if st.session_state.get('y_m'):
        with st.form("y_m_f"):
            ad = st.text_input("Ad Soyad *")
            tel = st.text_input("Telefon")
            ep = st.text_input("E-posta")
            if st.form_submit_button("REHBERE KAYDET"):
                if ad:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel, eposta) VALUES (?,?,?)", (ad, tel, ep))
                    conn.commit(); st.session_state['y_m'] = False; st.rerun()

    st.divider()
    search = st.text_input("🔍 ARA...", placeholder="Müşteri ismini yazın...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""
            <div class="customer-list-card">
                <div style="display:flex; align-items:center;">
                    <div class="avatar-box">{m['ad'][0].upper()}</div>
                    <div style="font-weight:700; color:#2D3748;">{m['ad']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:800; color:{'#EF4444' if bakiye > 0 else '#22C55E'};">{abs(bakiye):,} ₺</div>
                    <div style="font-size:10px; font-weight:700; color:#A0AEC0;">{'VERDİM' if bakiye > 0 else 'ALDIM'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"DETAY: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()

with st.sidebar:
    st.markdown("### ⚙️ YÖNETİM")
    if not df_i.empty:
        output = io.BytesIO()
        df_i.to_excel(output, index=False, engine='openpyxl')
        st.download_button("📥 EXCEL YEDEĞİ AL", output.getvalue(), "Havas_Ahsap_Yedek.xlsx")
    
