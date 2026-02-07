import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import plotly.express as px

# --- 1. VERİTABANI ALTYAPISI (Veriler Korunuyor) ---
def init_db():
    conn = sqlite3.connect('havas_pro_v45.db', check_same_thread=False)
    c = conn.cursor()
    # Gerekli tüm tablolar ve kolonlar
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, profil_foto BLOB, odeme_sozu TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP ELITE", layout="wide", initial_sidebar_state="collapsed")

# --- 2. ELİTE TASARIM AYARLARI ---
st.markdown("""
    <style>
    .stApp { background-color: #F1F5F9; }
    .main-header { background: #0052D4; padding: 10px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .customer-card { background: white; padding: 15px; border-radius: 20px; margin-bottom: 10px; border-left: 10px solid #0052D4; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NAVİGASYON ---
if st.button("HAVAS AHŞAP", key="nav_home"):
    for k in ['secili_id', 'y_m_acik', 'edit_islem_id']:
        if k in st.session_state: del st.session_state[k]
    st.rerun()

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- 4. EKRAN KONTROLLERİ ---

if 'secili_id' in st.session_state:
    # --- MÜŞTERİ DETAY SAYFASI ---
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    col_geri, col_sil = st.columns([4, 1])
    if col_geri.button("⬅️ Listeye Dön"): del st.session_state['secili_id']; st.rerun()
    if col_sil.button("🗑️ Müşteriyi Sil"):
        conn.cursor().execute("DELETE FROM musteriler WHERE id=?", (int(m_id),))
        conn.commit(); del st.session_state['secili_id']; st.rerun()

    st.title(f"👤 {m_bilgi['ad']}")

    # Güncelleme Paneli (Profil Foto ve Ödeme Sözü)
    with st.expander("⚙️ Bilgileri Güncelle"):
        c1, c2 = st.columns(2)
        nf = c1.file_uploader("Profil Fotoğrafı", type=['jpg','png'])
        ns = c2.date_input("Ödeme Sözü")
        if st.button("Kaydet"):
            if nf: conn.cursor().execute("UPDATE musteriler SET profil_foto=? WHERE id=?", (nf.read(), int(m_id)))
            conn.cursor().execute("UPDATE musteriler SET odeme_sozu=? WHERE id=?", (ns.strftime("%Y-%m-%d"), int(m_id)))
            conn.commit(); st.rerun()

    # Yeni İşlem Formu
    with st.container(border=True):
        st.markdown("### ➕ YENİ İŞLEM")
        with st.form("islem_formu", clear_on_submit=True):
            tip = st.selectbox("Tür", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            mik = st.number_input("Tutar (₺)", min_value=0)
            not_ = st.text_input("Not")
            fots = st.file_uploader("📷 Fotoğraflar", accept_multiple_files=True)
            if st.form_submit_button("SİSTEME İŞLE"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                is_id = c.lastrowid
                for f in fots: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()

    # İşlem Geçmişi (Düzenle ve Sil Butonlu)
    st.markdown("### 📜 Geçmiş")
    m_i_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in m_i_df.iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            c1, c2 = st.columns(2)
            if c1.button("🗑️ İşlemi Sil", key=f"d_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()
            st.write(f"Not: {row['aciklama']}")
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(3)
                for i, fr in f_df.iterrows(): cols[i % 3].image(fr['foto'], use_container_width=True)

else:
    # --- ANA SAYFA ---
    # Ödeme Hatırlatıcı
    bugun = datetime.now().strftime("%Y-%m-%d")
    soz_list = df_m[df_m['odeme_sozu'] == bugun]
    if not soz_list.empty:
        st.error(f"🔔 Bugün {len(soz_list)} kişiden ödeme bekleniyor!")

    # Müşteri Ekleme (Çalışan Hali)
    if st.button("➕ YENİ MÜŞTERİ KAYDET", type="primary"):
        st.session_state['y_m_acik'] = True

    if st.session_state.get('y_m_acik'):
        with st.form("yeni_m_form"):
            ad = st.text_input("Ad Soyad")
            tel = st.text_input("Telefon")
            if st.form_submit_button("✅ REHBERE EKLE"):
                if ad:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (ad, tel))
                    conn.commit(); del st.session_state['y_m_acik']; st.rerun()

    # Arama ve Liste
    search = st.text_input("🔍 Ara...")
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            b = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            
            st.markdown(f"""<div class="customer-card"><b>{m['ad']}</b><br><b style="color:{'#EF4444' if b > 0 else '#10B981'}; font-size:18px;">{abs(b):,} ₺</b></div>""", unsafe_allow_html=True)
            if st.button(f"HESABI GÖR: {m['ad']}", key=f"btn_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
    
