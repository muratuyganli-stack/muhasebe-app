import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# Veritabanı v29
def init_db():
    conn = sqlite3.connect('muhasebe_v29.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- CSS: FOTOĞRAFLARDAKİ GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FB; }
    .header-bar { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; margin-bottom: 10px; }
    .brand { font-weight: bold; font-size: 20px; color: #2D3748; }
    
    .summary-box {
        background: white; padding: 20px; border-radius: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03); margin-bottom: 20px;
    }
    .amount-val-aldim { color: #2F855A; font-size: 24px; font-weight: bold; }
    .amount-val-verdim { color: #C53030; font-size: 24px; font-weight: bold; }

    .customer-card {
        background: white; padding: 15px; border-radius: 18px;
        margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .avatar {
        width: 45px; height: 45px; background: #E2E8F0; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-weight: bold; color: #4A5568; margin-right: 12px;
    }
    
    /* Müşteri Ekle Butonu */
    div.stButton > button:first-child {
        background-color: #3182CE !important; color: white !important;
        border-radius: 25px !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ÜST BAR ---
st.markdown('<div class="header-bar"><div class="brand">📖 HAVAS AHŞAP</div><div>⚙️</div></div>', unsafe_allow_html=True)

# Verileri Çek
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)

# --- DETAY EKRANI (AÇIKSA) ---
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ Geri Dön"):
        del st.session_state['secili_id']; st.rerun()
    
    st.header(f"👤 {m_bilgi['ad']}")
    
    # FOTOĞRAF EKLEME FORMU
    with st.container(border=True):
        st.subheader("📷 Yeni İşlem & Çoklu Fotoğraf")
        with st.form("islem_f", clear_on_submit=True):
            tip = st.selectbox("İşlem", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar", min_value=0.0)
            not_ = st.text_input("Not")
            # ÇOKLU FOTOĞRAF SEÇİMİ
            yuklenen_fotolar = st.file_uploader("Belge/Ürün Fotoğrafları (Birden Fazla)", accept_multiple_files=True)
            
            if st.form_submit_button("KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, mik, tip, not_))
                is_id = c.lastrowid
                for f in yuklenen_fotolar:
                    c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.success("Fotoğraflarla kaydedildi!"); st.rerun()

    # GEÇMİŞ VE FOTOĞRAF GÖRÜNTÜLEME
    st.divider()
    k_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} ₺"):
            st.write(f"**Not:** {row['aciklama']}")
            # FOTOĞRAFLARI GETİR
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows():
                    cols[i].image(fr['foto'], use_container_width=True)
            if st.button("🗑️ Sil", key=f"del_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

# --- ANA LİSTE EKRANI ---
else:
    # Özet Tabela
    aldim = df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum()
    verdim = df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum()
    st.markdown(f"""<div class="summary-box"><div style="display:flex;justify-content:space-between;">
        <div><small>Aldım</small><br><div class="amount-val-aldim">{aldim:,.1f} ₺</div></div>
        <div style="text-align:right;"><small>Verdim</small><br><div class="amount-val-verdim">{verdim:,.1f} ₺</div></div>
    </div></div>""", unsafe_allow_html=True)

    # Müşteri Ekle ve Ara
    if st.button("➕ Müşteri ekle"): st.session_state['yeni_m'] = True
    if st.session_state.get('yeni_m'):
        with st.form("yeni_m_f"):
            n_ad = st.text_input("Ad Soyad")
            if st.form_submit_button("Kaydet"):
                conn.cursor().execute("INSERT INTO musteriler (ad) VALUES (?)", (n_ad,))
                conn.commit(); st.session_state['yeni_m'] = False; st.rerun()

    search = st.text_input("🔍 Arama", placeholder="Müşteri ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_islemler = df_i[df_i['musteri_id'] == m['id']]
            bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
            
            st.markdown(f"""<div class="customer-card">
                <div style="display:flex;align-items:center;">
                    <div class="avatar">{m['ad'][0]}</div>
                    <div><b>{m['ad']}</b><br><small style="color:gray;">Bugün</small></div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:bold;color:{'#C53030' if bakiye > 0 else '#2F855A'};">{abs(bakiye):,.1f} ₺</div>
                    <small style="color:gray;">{'Verdim' if bakiye > 0 else 'Aldım'}</small>
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"Gör: {m['ad']}", key=f"view_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
                
