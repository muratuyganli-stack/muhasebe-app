import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Veritabanı v31 - Fotoğraf + Rehber + PDF
def init_db():
    conn = sqlite3.connect('muhasebe_v31.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, eposta TEXT, adres TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- PDF OLUŞTURMA FONKSİYONU ---
def generate_pdf(df, m_ad):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, f"HAVAS AHSAP - {m_ad} EKSTRESI")
    c.setFont("Helvetica", 10)
    c.drawString(50, 785, f"Rapor Tarihi: {datetime.now().strftime('%d/%m/%Y')}")
    c.line(50, 780, 550, 780)
    
    y = 750
    c.drawString(50, y, "Tarih")
    c.drawString(150, y, "Islem")
    c.drawString(300, y, "Tutar")
    c.drawString(400, y, "Not")
    y -= 20
    
    for _, r in df.iterrows():
        c.drawString(50, y, str(r['tarih']))
        c.drawString(150, y, str(r['tip']))
        c.drawString(300, y, f"{r['miktar']:,} TL")
        c.drawString(400, y, str(r['aciklama'])[:30])
        y -= 20
        if y < 50: c.showPage(); y = 800
    
    c.save()
    return buf.getvalue()

# --- CSS VE BAŞLIK ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .shop-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 10px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px; }
    .customer-card { background: white; padding: 15px; border-radius: 15px; margin-bottom: 10px; border-left: 6px solid #3b82f6; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="shop-header"><h3 style="margin:0;">🔨 HAVAS AHŞAP | Cari Yönetim</h3></div>', unsafe_allow_html=True)

# Verileri Çek
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- ANA SAYFA VEYA DETAY ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ Listeye Dön"):
        del st.session_state['secili_id']; st.rerun()
    
    st.markdown(f"### 👤 {m_bilgi['ad']}")
    st.caption(f"📞 {m_bilgi['tel']} | ✉️ {m_bilgi['eposta']} | 📍 {m_bilgi['adres']}")

    # PDF RAPORLAMA
    with st.expander("📄 WhatsApp İçin PDF Dökümü Al"):
        if st.button("Hemen PDF Hazırla"):
            m_islemler = df_i[df_i['musteri_id'] == m_id]
            pdf = generate_pdf(m_islemler, m_bilgi['ad'])
            st.download_button("📥 PDF İndir ve Paylaş", pdf, f"{m_bilgi['ad']}_Ekstre.pdf")

    # FOTOĞRAF EKLEME FORMU (BURADA!)
    with st.container(border=True):
        st.subheader("📷 Yeni İşlem & Fotoğraflar")
        with st.form("islem_form", clear_on_submit=True):
            tip = st.selectbox("İşlem Tipi", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (TL)", min_value=0.0)
            not_ = st.text_input("Not / Açıklama")
            # ÇOKLU FOTOĞRAF SEÇİMİ
            fotos = st.file_uploader("Fotoğrafları/Belgeleri Seç (Birden Fazla)", accept_multiple_files=True)
            
            if st.form_submit_button("SİSTEME KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, mik, tip, not_))
                is_id = c.lastrowid
                for f in fotos:
                    c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.success("Fotoğraflarla birlikte kaydedildi!"); st.rerun()

    # GEÇMİŞ VE FOTOĞRAF GÖRÜNTÜLEME
    st.markdown("### 📜 Geçmiş Hareketler")
    k_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
            st.write(f"**Not:** {row['aciklama']}")
            # FOTOĞRAFLARI GETİR
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                st.write("**Ekli Fotoğraflar:**")
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows():
                    cols[i].image(fr['foto'], use_container_width=True)
            if st.button("🗑️ Sil", key=f"del_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

else:
    # MÜŞTERİ EKLEME (GENİŞ REHBERLİ)
    with st.expander("➕ YENİ MÜŞTERİ / CARİ KART EKLE"):
        with st.form("yeni_m"):
            ad = st.text_input("Ad Soyad *")
            tel = st.text_input("Telefon")
            mail = st.text_input("E-posta")
            adr = st.text_area("Adres")
            if st.form_submit_button("REHBERE KAYDET"):
                if ad:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel, eposta, adres) VALUES (?,?,?,?)", (ad, tel, mail, adr))
                    conn.commit(); st.rerun()

    st.divider()
    
    # LİSTELEME (ÖNCEKİ ŞIK TASARIM)
    if not df_m.empty:
        search = st.text_input("🔍 Müşteri Ara...")
        for _, m in df_m.iterrows():
            if search.lower() in m['ad'].lower():
                m_islemler = df_i[df_i['musteri_id'] == m['id']]
                bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
                
                st.markdown(f"""<div class="customer-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div><b>{m['ad']}</b><br><small>{m['tel']}</small></div>
                        <div style="text-align:right;">
                            <b style="color:{'#C53030' if bakiye > 0 else '#2F855A'};">{abs(bakiye):,.2f} TL</b><br>
                            <small>{'Verdim' if bakiye > 0 else 'Aldım'}</small>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"🔎 İŞLEMLER VE FOTOLAR: {m['ad']}", key=f"view_{m['id']}"):
                    st.session_state['secili_id'] = m['id']; st.rerun()
                    
