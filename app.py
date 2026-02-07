import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import plotly.express as px

# --- 1. VERİTABANI BAĞLANTISI (Sadık Kalıyoruz) ---
def init_db():
    conn = sqlite3.connect('havas_pro_v45.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP PRO", layout="wide", initial_sidebar_state="collapsed")

# --- 2. PREMIUM GÖRSEL TASARIM (CSS GÜNCELLEMESİ) ---
st.markdown("""
    <style>
    /* Genel Arka Plan */
    .stApp { background-color: #F8FAFC; }
    
    /* Premium Üst Başlık */
    .stButton > button.home-btn-premium {
        background: linear-gradient(135deg, #0052D4, #4364F7, #6FB1FC) !important;
        color: white !important; border: none !important; padding: 12px !important;
        border-radius: 0 0 20px 20px !important; width: 100% !important;
        font-size: 20px !important; font-weight: 800 !important;
        box-shadow: 0 10px 20px rgba(0,82,212,0.2) !important;
        transition: all 0.3s ease;
    }
    
    /* Müşteri Kartları */
    .customer-card-pro { 
        background: white; padding: 20px; border-radius: 20px; margin-bottom: 15px; 
        border-left: 12px solid #0052D4; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        transition: transform 0.2s;
    }
    .customer-card-pro:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.06); }
    
    /* Özet Paneli */
    .stats-box {
        background: white; padding: 20px; border-radius: 25px; 
        display: flex; justify-content: space-around; align-items: center;
        border: 1px solid #E2E8F0; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
    }
    
    /* Butonlar */
    .stButton > button { border-radius: 12px !important; transition: all 0.2s; }
    .stButton > button:hover { opacity: 0.9; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PREMIUM NAVİGASYON ---
if st.button("HAVAS AHŞAP", key="header_home_pro", help="Ana Sayfa"):
    for key in ['secili_id', 'y_m', 'edit_islem_id']:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- 4. EKRAN KONTROLLERİ ---

if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    # Başlık ve Silme Butonu
    c_header, c_del = st.columns([4, 1.2])
    with c_header: 
        if st.button("⬅️ Geri Dön"): del st.session_state['secili_id']; st.rerun()
    with c_del:
        if st.button("🗑️ Kaydı Sil", type="secondary", use_container_width=True):
            conn.cursor().execute("DELETE FROM musteriler WHERE id=?", (int(m_id),)); conn.commit(); del st.session_state['secili_id']; st.rerun()
    
    st.markdown(f"<h2 style='color:#1E293B; margin-top:10px;'>👤 {m_bilgi['ad']}</h2>", unsafe_allow_html=True)
    
    # İşlem Düzenleme (Varsa)
    if 'edit_islem_id' in st.session_state:
        with st.container(border=True):
            st.warning("İşlemi Güncelle")
            e_row = df_i[df_i['id'] == st.session_state['edit_islem_id']].iloc[0]
            y_mik = st.number_input("Tutar", value=int(e_row['miktar']))
            y_not = st.text_input("Not", value=str(e_row['aciklama']))
            if st.button("✅ Güncellemeyi Kaydet"):
                conn.cursor().execute("UPDATE islemler SET miktar=?, aciklama=? WHERE id=?", (y_mik, y_not, st.session_state['edit_islem_id']))
                conn.commit(); del st.session_state['edit_islem_id']; st.rerun()

    # Yeni İşlem Formu
    with st.expander("✨ YENİ İŞLEM EKLE", expanded=False):
        with st.form("islem_pro", clear_on_submit=True):
            tip = st.selectbox("İşlem Türü", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (₺)", min_value=0)
            not_ = st.text_input("Açıklama / Not")
            fotos = st.file_uploader("📷 Fotoğraflar", accept_multiple_files=True)
            if st.form_submit_button("SİSTEME İŞLE"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # Hesap Dökümü
    st.markdown("### 📜 Hesap Hareketleri")
    m_i_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in m_i_df.iterrows():
        renk = "#10B981" if "Tahsilat" in row['tip'] else "#EF4444"
        with st.expander(f"📍 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            st.markdown(f"<p style='color:#64748B;'>Not: {row['aciklama']}</p>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            if c1.button("✏️ Düzenle", key=f"e_{row['id']}"): st.session_state['edit_islem_id'] = row['id']; st.rerun()
            if c2.button("🗑️ Sil", key=f"d_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()
            
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(3)
                for i, fr in f_df.iterrows(): cols[i % 3].image(fr['foto'], use_container_width=True)

else:
    # --- ANA SAYFA PREMIUM GÖRÜNÜM ---
    top_ald = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum() if not df_i.empty else 0)
    top_ver = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum() if not df_i.empty else 0)
    
    st.markdown(f"""
    <div class="stats-box">
        <div style="text-align:center;"><small style="color:#64748B;">Tahsil Edilen</small><br><b style="color:#10B981; font-size:22px;">{top_ald:,} ₺</b></div>
        <div style="width:1px; height:40px; background:#E2E8F0;"></div>
        <div style="text-align:center;"><small style="color:#64748B;">Toplam Alacak</small><br><b style="color:#EF4444; font-size:22px;">{top_ver - top_ald:,} ₺</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
    
    if st.button("➕ YENİ MÜŞTERİ KAYDET", type="primary"): st.session_state['y_m'] = True
    if st.session_state.get('y_m'):
        with st.form("y_m_pro"):
            ad = st.text_input("Ad Soyad")
            tel = st.text_input("Telefon No")
            if st.form_submit_button("✅ SİSTEME EKLE"):
                conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (ad, tel))
                conn.commit(); del st.session_state['y_m']; st.rerun()

    search = st.text_input("🔍 Müşteri Listesinde Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            b = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            
            st.markdown(f"""
            <div class="customer-card-pro">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div><b style="font-size:20px; color:#1E293B;">{m['ad']}</b></div>
                    <div style="text-align:right;">
                        <b style="color:{'#EF4444' if b > 0 else '#10B981'}; font-size:22px;">{abs(b):,} ₺</b><br>
                        <small style="color:#64748B;">{'Bakiyesi Var' if b > 0 else 'Borcu Yok'}</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"HESABI GÖR: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()

with st.sidebar:
    st.markdown("### 💎 PREMIUM PANEL")
    if not df_i.empty:
        output = io.BytesIO()
        df_i.to_excel(output, index=False, engine='openpyxl')
        st.download_button("📥 Excel Yedek Al", output.getvalue(), "Havas_V56_Yedek.xlsx", use_container_width=True)
