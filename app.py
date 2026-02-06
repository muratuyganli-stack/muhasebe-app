import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import plotly.express as px # Grafik için yeni ekledik

# --- 1. VERİTABANI (Mevcut veriler korunuyor) ---
def init_db():
    conn = sqlite3.connect('havas_pro_v45.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide", initial_sidebar_state="collapsed")

# --- 2. GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .main-header { background: #0052D4; padding: 10px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .customer-card { background: white; padding: 15px; border-radius: 18px; margin-bottom: 12px; border-left: 10px solid #0052D4; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .action-btn { background: #F0F7FF; border: 1px solid #0052D4; border-radius: 10px; padding: 8px; text-align: center; color: #0052D4; font-weight: bold; text-decoration: none; display: block; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h2>HAVAS AHŞAP</h2></div>', unsafe_allow_html=True)

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- 3. ÜÇÜNCÜ SEÇENEK: ANALİZ VE GRAFİKLER ---
if 'secili_id' not in st.session_state and not df_i.empty:
    with st.expander("📊 Dükkan Analiz Raporu (Görsel)", expanded=False):
        # Aylık Ciro Grafiği Hazırlığı
        df_i['tarih_dt'] = pd.to_datetime(df_i['tarih'], format="%d-%m-%Y %H:%M", errors='coerce')
        df_i['Ay'] = df_i['tarih_dt'].dt.strftime('%B %Y')
        
        aylik_ozet = df_i.groupby(['Ay', 'tip'])['miktar'].sum().reset_index()
        
        fig = px.bar(aylik_ozet, x='Ay', y='miktar', color='tip', 
                     title="Aylık Satış ve Tahsilat Durumu",
                     labels={'miktar':'Toplam Tutar (₺)', 'tip':'İşlem Türü'},
                     color_discrete_map={'Satis (Verdim)': '#EF4444', 'Tahsilat (Aldim)': '#10B981'},
                     barmode='group')
        st.plotly_chart(fig, use_container_width=True)

# --- 4. ANA AKIŞ (v49 ile birebir aynı, bozulmadı) ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ LİSTEYE DÖN"): del st.session_state['secili_id']; st.rerun()
    
    st.title(f"👤 {m_bilgi['ad']}")
    
    # Yeni İşlem Formu
    with st.container(border=True):
        st.markdown("### ➕ YENİ İŞLEM")
        with st.form("islem_f_v50", clear_on_submit=True):
            tip = st.selectbox("İşlem", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (₺)", min_value=0, step=1)
            not_ = st.text_input("Açıklama")
            fotos = st.file_uploader("📷 Fotoğraflar", accept_multiple_files=True)
            if st.form_submit_button("SİSTEME İŞLE"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # Geçmiş Hareketler
    m_i_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in m_i_df.iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)

else:
    # Ana Liste Ekranı
    toplam_aldigim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
    toplam_verdigim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum())
    
    st.markdown(f"""
    <div style="background:white; padding:15px; border-radius:15px; display:flex; justify-content:space-around; margin-bottom:20px; border:1px solid #E2E8F0;">
        <div style="text-align:center;"><small>Tahsilat</small><br><b style="color:green; font-size:18px;">{toplam_aldigim:,} ₺</b></div>
        <div style="text-align:center;"><small>Alacak</small><br><b style="color:red; font-size:18px;">{toplam_verdigim - toplam_aldigim:,} ₺</b></div>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input("🔍 Müşteri Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""<div class="customer-card"><b>{m['ad']}</b><br><b style="color:{'#EF4444' if bakiye > 0 else '#10B981'}; font-size:18px;">{abs(bakiye):,} TL</b></div>""", unsafe_allow_html=True)
            if st.button(f"HESABI GÖR: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
