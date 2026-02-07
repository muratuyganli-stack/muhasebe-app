import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import plotly.express as px

# --- VERİTABANI ---
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

# --- GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stButton > button.home-btn-style {
        background-color: #0052D4 !important; color: white !important;
        border: none !important; padding: 10px !important;
        border-radius: 0 0 15px 15px !important; width: 100% !important;
        font-size: 18px !important; font-weight: 700 !important;
    }
    .customer-card { background: white; padding: 15px; border-radius: 18px; margin-bottom: 12px; border-left: 10px solid #0052D4; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- MAVİ BANTLI BAŞLIK (Navigasyon) ---
if st.button("HAVAS AHŞAP", key="home_nav_v53"):
    if 'secili_id' in st.session_state:
        del st.session_state['secili_id']
    st.rerun()

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- ANALİZ PANELİ ---
if 'secili_id' not in st.session_state and not df_i.empty:
    with st.expander("📊 Dükkan Analiz Raporu", expanded=False):
        try:
            df_i['tarih_dt'] = pd.to_datetime(df_i['tarih'], format="%d-%m-%Y %H:%M", errors='coerce')
            df_i['Ay'] = df_i['tarih_dt'].dt.strftime('%B %Y')
            aylik_ozet = df_i.groupby(['Ay', 'tip'])['miktar'].sum().reset_index()
            fig = px.bar(aylik_ozet, x='Ay', y='miktar', color='tip', 
                         color_discrete_map={'Satis (Verdim)': '#EF4444', 'Tahsilat (Aldim)': '#10B981'},
                         barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        except: st.info("Analiz için yeterli veri henüz yok.")

# --- ANA AKIŞ ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    if st.button("⬅️ LİSTEYE DÖN"): del st.session_state['secili_id']; st.rerun()
    st.markdown(f"#### 👤 {m_bilgi['ad']}")
    
    with st.container(border=True):
        st.markdown("### ➕ YENİ İŞLEM")
        with st.form("islem_form", clear_on_submit=True):
            tip = st.selectbox("İşlem", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (₺)", min_value=0, step=1)
            fotos = st.file_uploader("📷 Fotoğraflar", accept_multiple_files=True)
            if st.form_submit_button("SİSTEME İŞLE"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip) VALUES (?,?,?,?)", (int(m_id), tarih, int(mik), tip))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    m_i_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in m_i_df.iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)
else:
    # Ana Sayfa Özeti
    toplam_aldigim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
    toplam_verdigim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum())
    st.markdown(f"""<div style="background:white; padding:10px; border-radius:15px; display:flex; justify-content:space-around; border:1px solid #E2E8F0;">
        <div style="text-align:center;"><small>Tahsilat</small><br><b style="color:green;">{toplam_aldigim:,} ₺</b></div>
        <div style="text-align:center;"><small>Alacak</small><br><b style="color:red;">{toplam_verdigim - toplam_aldigim:,} ₺</b></div>
    </div>""", unsafe_allow_html=True)

    search = st.text_input("🔍 Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            b = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""<div class="customer-card"><b>{m['ad']}</b><br><b style="color:{'#EF4444' if b > 0 else '#10B981'}; font-size:18px;">{abs(b):,} TL</b></div>""", unsafe_allow_html=True)
            if st.button(f"GÖR: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
