import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- 1. VERİTABANI ALTYAPISI (Hatasız ve Tam) ---
def init_db():
    conn = sqlite3.connect('havas_pro_v45.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, profil_foto BLOB, odeme_sozu TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP DEFTER", layout="wide", initial_sidebar_state="collapsed")

# --- 2. GÖRSEL TASARIM (Defter Konsepti) ---
st.markdown("""
    <style>
    .stApp { background-color: #F4F7F9; }
    .main-header { 
        background: #1E3A8A; padding: 10px; border-radius: 0 0 15px 15px; 
        color: white; text-align: center; margin-bottom: 20px;
    }
    .customer-card { 
        background: white; padding: 15px; border-radius: 15px; margin-bottom: 10px; 
        border-left: 8px solid #1E3A8A; box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
    }
    .excel-table { font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NAVİGASYON ---
if st.button("HAVAS AHŞAP BORÇ-ALACAK DEFTERİ", key="nav_home"):
    for k in ['secili_id', 'y_m_acik']:
        if k in st.session_state: del st.session_state[k]
    st.rerun()

# Verileri Çek
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- 4. ANA EKRAN KONTROLÜ ---
tab1, tab2 = st.tabs(["🗂 Cari Kartlar", "📊 Genel Defter (Excel)"])

with tab1:
    if 'secili_id' in st.session_state:
        # --- MÜŞTERİ DETAY SAYFASI ---
        m_id = st.session_state['secili_id']
        m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
        
        col_back, col_del = st.columns([4, 1])
        if col_back.button("⬅️ Listeye Dön"): del st.session_state['secili_id']; st.rerun()
        
        st.subheader(f"👤 {m_bilgi['ad']} - Hesap Dökümü")

        # Yeni İşlem Formu
        with st.expander("➕ YENİ İŞLEM EKLE", expanded=False):
            with st.form("islem_f"):
                tip = st.selectbox("İşlem Türü", ["Satis (Borç Yaz)", "Tahsilat (Ödeme Al)"])
                mik = st.number_input("Tutar (₺)", min_value=0)
                not_ = st.text_input("Açıklama")
                fots = st.file_uploader("📷 Fotoğraflar", accept_multiple_files=True)
                if st.form_submit_button("DEFTERE İŞLE"):
                    c = conn.cursor()
                    tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                    c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(mik), tip, not_))
                    is_id = c.lastrowid
                    for f in fots: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                    conn.commit(); st.rerun()

        # Müşteriye Özel Excel Tablosu
        m_i_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
        if not m_i_df.empty:
            st.markdown("### 📒 Kişisel Defter")
            st.dataframe(m_i_df[['tarih', 'tip', 'miktar', 'aciklama']], use_container_width=True)
            
            # Eski Kayıtlar ve Fotoğraflar
            for _, row in m_i_df.iterrows():
                with st.expander(f"🔍 {row['tarih']} - {row['tip']} - {row['miktar']:,} ₺"):
                    st.write(f"Not: {row['aciklama']}")
                    if st.button("Sil", key=f"d_{row['id']}"):
                        conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()
                    f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
                    if not f_df.empty:
                        cols = st.columns(3)
                        for i, fr in f_df.iterrows(): cols[i % 3].image(fr['foto'], use_container_width=True)

    else:
        # --- ANA LİSTE (KARTLAR) ---
        if st.button("➕ YENİ MÜŞTERİ EKLE"): st.session_state['y_m_acik'] = True
        if st.session_state.get('y_m_acik'):
            with st.form("y_m"):
                ad = st.text_input("Ad Soyad")
                tel = st.text_input("Telefon")
                if st.form_submit_button("KAYDET"):
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (ad, tel))
                    conn.commit(); del st.session_state['y_m_acik']; st.rerun()

        search = st.text_input("🔍 Cari Ara...")
        for _, m in df_m.iterrows():
            if search.lower() in m['ad'].lower():
                m_i = df_i[df_i['musteri_id'] == m['id']]
                b = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
                
                st.markdown(f"""
                <div class="customer-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <b>{m['ad']}</b>
                        <b style="color:{'#EF4444' if b > 0 else '#10B981'};">{abs(b):,} ₺</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"HESABI GÖR: {m['ad']}", key=f"btn_{m['id']}"):
                    st.session_state['secili_id'] = m['id']; st.rerun()

with tab2:
    # --- GENEL DEFTER (EXCEL TABLOSU GİBİ) ---
    st.subheader("📊 Tüm Hareketler (Excel Görünümü)")
    
    if not df_i.empty:
        # İsimleri birleştirelim
        genel_df = pd.merge(df_i, df_m[['id', 'ad']], left_on='musteri_id', right_on='id')
        genel_df = genel_df[['tarih', 'ad', 'tip', 'miktar', 'aciklama']]
        genel_df.columns = ['Tarih', 'Müşteri Adı', 'İşlem Türü', 'Tutar (₺)', 'Not']
        
        # Excel gibi filtreleme ve arama yapılabilen tablo
        st.dataframe(genel_df.sort_values(by='Tarih', ascending=False), use_container_width=True, height=500)
        
        # Excel İndirme Butonu
        output = io.BytesIO()
        genel_df.to_excel(output, index=False, engine='openpyxl')
        st.download_button("📥 TÜM DEFTERİ EXCEL OLARAK İNDİR", output.getvalue(), "Havas_Genel_Defter.xlsx")
    else:
        st.info("Henüz defterde kayıtlı işlem yok.")
            
