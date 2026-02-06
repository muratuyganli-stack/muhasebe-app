import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Veritabanı v32 - Küsuratsız (Tam Sayı) Tutar Yapısı
def init_db():
    conn = sqlite3.connect('muhasebe_v32.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, eposta TEXT, adres TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- CSS VE BAŞLIK (Önceki Şık Tasarım Korundu) ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .shop-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 10px; border-radius: 10px; color: white; text-align: center; margin-bottom: 15px; }
    .summary-box { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.03); margin-bottom: 20px; }
    .customer-card { background: white; padding: 15px; border-radius: 15px; margin-bottom: 10px; border-left: 6px solid #3b82f6; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="shop-header"><p style="margin:0; font-weight:bold; font-size:20px;">🔨 HAVAS AHŞAP | Cari Yönetim</p></div>', unsafe_allow_html=True)

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ Listeye Dön"):
        del st.session_state['secili_id']; st.rerun()
    
    st.markdown(f"### 👤 {m_bilgi['ad']}")

    # YENİ İŞLEM FORMU (Tam Sayı Ayarlı)
    with st.container(border=True):
        st.subheader("📷 Yeni İşlem & Fotoğraflar")
        with st.form("islem_form", clear_on_submit=True):
            tip = st.selectbox("İşlem Tipi", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            # KURUŞLARI KALDIRDIK: step=1 ile sadece tam sayı
            mik = st.number_input("Tutar (TL)", min_value=0, step=1)
            not_ = st.text_input("Not / Açıklama")
            fotos = st.file_uploader("Fotoğrafları Seç (Çoklu)", accept_multiple_files=True)
            
            if st.form_submit_button("SİSTEME KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fotos:
                    c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.success("Kaydedildi!"); st.rerun()

    # GEÇMİŞ VE FOTOLAR (Tam Sayı Görünümü)
    st.markdown("### 📜 Geçmiş Hareketler")
    k_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {int(row['miktar']):,} TL"):
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)
            if st.button("🗑️ Sil", key=f"del_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

else:
    # ANA SAYFA ÖZETİ (Tam Sayı)
    aldim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
    verdim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum())
    st.markdown(f"""<div class="summary-box"><div style="display:flex;justify-content:space-between;">
        <div><small>Aldım</small><br><b style="color:#2F855A; font-size:24px;">{aldim:,} ₺</b></div>
        <div style="text-align:right;"><small>Verdim</small><br><b style="color:#C53030; font-size:24px;">{verdim:,} ₺</b></div>
    </div></div>""", unsafe_allow_html=True)

    if st.button("➕ Müşteri ekle"): st.session_state['yeni_m'] = True
    if st.session_state.get('yeni_m'):
        with st.form("yeni_m_f"):
            n_ad = st.text_input("Ad Soyad")
            if st.form_submit_button("Kaydet"):
                conn.cursor().execute("INSERT INTO musteriler (ad) VALUES (?)", (n_ad,))
                conn.commit(); st.session_state['yeni_m'] = False; st.rerun()

    # LİSTE (Tam Sayı Bakiye)
    search = st.text_input("🔍 Müşteri Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_islemler = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""<div class="customer-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><b>{m['ad']}</b></div>
                    <div style="text-align:right;">
                        <b style="color:{'#C53030' if bakiye > 0 else '#2F855A'};">{abs(bakiye):,} ₺</b><br>
                        <small>{'Verdim' if bakiye > 0 else 'Aldım'}</small>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Gör: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
            
