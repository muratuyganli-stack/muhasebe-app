import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import plotly.express as px

# --- 1. VERİTABANI BAĞLANTISI ---
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
    .main-header-btn { background-color: #0052D4 !important; color: white !important; border-radius: 0 0 15px 15px !important; width: 100% !important; font-size: 18px !important; font-weight: 700 !important; margin-bottom: 15px; border: none !important; padding: 10px !important; }
    .customer-card { background: white; padding: 15px; border-radius: 18px; margin-bottom: 12px; border-left: 10px solid #0052D4; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .delete-btn { color: #FF4B4B !important; border: 1px solid #FF4B4B !important; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NAVİGASYON ---
if st.button("HAVAS AHŞAP", key="header_home"):
    for key in ['secili_id', 'y_m', 'edit_islem_id']:
        if key in st.session_state: del st.session_state[key]
    st.rerun()

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- 4. EKRAN KONTROLLERİ ---

if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    col_back, col_del_m = st.columns([3, 1])
    with col_back:
        if st.button("⬅️ LİSTEYE DÖN"): del st.session_state['secili_id']; st.rerun()
    with col_del_m:
        if st.button("🗑️ MÜŞTERİYİ SİL", use_container_width=True):
            c = conn.cursor()
            c.execute("DELETE FROM musteriler WHERE id=?", (int(m_id),))
            c.execute("DELETE FROM islemler WHERE musteri_id=?", (int(m_id),))
            conn.commit(); del st.session_state['secili_id']; st.rerun()
    
    st.markdown(f"#### 👤 {m_bilgi['ad']}")
    
    # İŞLEM DÜZENLEME FORMU (Eğer bir işlem seçildiyse)
    if 'edit_islem_id' in st.session_state:
        e_id = st.session_state['edit_islem_id']
        e_row = df_i[df_i['id'] == e_id].iloc[0]
        with st.form("edit_form"):
            st.warning(f"Düzenlenen İşlem: {e_row['tarih']}")
            yeni_mik = st.number_input("Yeni Tutar", value=int(e_row['miktar']))
            yeni_not = st.text_input("Yeni Not", value=str(e_row['aciklama']))
            col_e1, col_e2 = st.columns(2)
            if col_e1.form_submit_button("GÜNCELLE"):
                conn.cursor().execute("UPDATE islemler SET miktar=?, aciklama=? WHERE id=?", (yeni_mik, yeni_not, e_id))
                conn.commit(); del st.session_state['edit_islem_id']; st.rerun()
            if col_e2.form_submit_button("İPTAL"):
                del st.session_state['edit_islem_id']; st.rerun()

    # YENİ İŞLEM EKLEME (Koda Sadık)
    with st.expander("➕ YENİ İŞLEM EKLE", expanded=False):
        with st.form("islem_v55", clear_on_submit=True):
            tip = st.selectbox("Tür", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar", min_value=0, step=1)
            not_ = st.text_input("Not")
            fotos = st.file_uploader("📷 Fotoğraflar", accept_multiple_files=True)
            if st.form_submit_button("KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # HAREKETLER LİSTESİ (Düzenle ve Sil Butonlu)
    st.markdown("### 📜 İşlem Geçmişi")
    m_i_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in m_i_df.iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            st.write(f"Not: {row['aciklama']}")
            col1, col2 = st.columns(2)
            if col1.button(f"✏️ Düzenle", key=f"e_{row['id']}"):
                st.session_state['edit_islem_id'] = row['id']; st.rerun()
            if col2.button(f"🗑️ Sil", key=f"d_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],))
                conn.cursor().execute("DELETE FROM fotograflar WHERE islem_id=?", (row['id'],))
                conn.commit(); st.rerun()
            
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(3)
                for i, fr in f_df.iterrows(): cols[i % 3].image(fr['foto'], use_container_width=True)

else:
    # ANA LİSTE (Koda Sadık)
    toplam_aldigim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum() if not df_i.empty else 0)
    toplam_verdigim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum() if not df_i.empty else 0)
    st.markdown(f"""<div style="background:white; padding:10px; border-radius:15px; display:flex; justify-content:space-around; margin-bottom:15px; border:1px solid #E2E8F0;">
        <div style="text-align:center;"><small>Tahsilat</small><br><b style="color:green;">{toplam_aldigim:,} ₺</b></div>
        <div style="text-align:center;"><small>Alacak</small><br><b style="color:red;">{toplam_verdigim - toplam_aldigim:,} ₺</b></div>
    </div>""", unsafe_allow_html=True)

    if st.button("➕ YENİ MÜŞTERİ KAYDET"): st.session_state['y_m'] = True
    if st.session_state.get('y_m'):
        with st.form("yeni_m"):
            ad = st.text_input("Ad Soyad")
            tel = st.text_input("Telefon")
            if st.form_submit_button("REHBERE EKLE"):
                conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (ad, tel))
                conn.commit(); del st.session_state['y_m']; st.rerun()

    search = st.text_input("🔍 Müşteri Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            b = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            st.markdown(f"""<div class="customer-card"><b>{m['ad']}</b><br><b style="color:{'#EF4444' if b > 0 else '#10B981'}; font-size:20px;">{abs(b):,} TL</b></div>""", unsafe_allow_html=True)
            if st.button(f"HESABI GÖR: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
        
