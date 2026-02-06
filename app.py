import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- 1. VERİTABANI (En Kararlı Yapı) ---
def init_db():
    conn = sqlite3.connect('havas_premium_v36.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, adres TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide", initial_sidebar_state="collapsed")

# --- 2. ELİTE GÖRSEL TASARIM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F0F2F5; }
    
    /* Üst Bar */
    .main-header {
        background: linear-gradient(135deg, #1A365D 0%, #2B6CB0 100%);
        padding: 25px; border-radius: 0 0 30px 30px; color: white;
        text-align: center; margin-bottom: 25px; box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* Özet Kartı */
    .summary-card {
        background: white; padding: 20px; border-radius: 25px;
        display: flex; justify-content: space-around; align-items: center;
        margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .stat-box { text-align: center; }
    .stat-label { font-size: 13px; color: #718096; font-weight: 600; text-transform: uppercase; }
    .stat-val-up { color: #2F855A; font-size: 24px; font-weight: 800; }
    .stat-val-down { color: #C53030; font-size: 24px; font-weight: 800; }

    /* Müşteri Kartları */
    .customer-card {
        background: white; padding: 18px; border-radius: 20px;
        margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;
        border: 1px solid #EDF2F7; transition: 0.3s;
    }
    .customer-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.06); }
    
    .avatar-circle {
        width: 50px; height: 50px; background: #EBF8FF; border-radius: 15px;
        display: flex; align-items: center; justify-content: center;
        font-weight: 800; color: #2B6CB0; font-size: 20px; margin-right: 15px;
    }

    /* Müşteri Ekle Butonu */
    div.stButton > button:first-child {
        background: #3182CE; color: white; border-radius: 15px;
        height: 3.5em; font-weight: 700; border: none; width: 100%;
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.3);
    }
    
    /* Fotoğraf Alanı */
    .photo-area { border: 2px dashed #CBD5E0; border-radius: 15px; padding: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ÜST BAŞLIK ---
st.markdown('<div class="main-header"><h1 style="margin:0; font-size:28px; letter-spacing:-1px;">🔨 HAVAS AHŞAP</h1><p style="opacity:0.8; font-size:14px; margin:0;">Mobilya Tasarım & Cari Yönetim</p></div>', unsafe_allow_html=True)

# Verileri Çek
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)

# --- 4. EKRAN YÖNETİMİ ---
if 'secili_id' in st.session_state:
    # --- DETAY SAYFASI ---
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ ANA LİSTEYE DÖN"):
        del st.session_state['secili_id']; st.rerun()
    
    st.markdown(f"## 👤 {m_bilgi['ad']}")
    st.caption(f"📞 {m_bilgi['tel']} | 📍 {m_bilgi['adres']}")

    # HIZLI İŞLEM FORMU
    with st.container(border=True):
        st.markdown("### 📷 İŞLEM VE FOTOĞRAF EKLE")
        with st.form("premium_islem", clear_on_submit=True):
            col1, col2 = st.columns(2)
            t = col1.selectbox("İşlem Tipi", ["Satis (Verdim)", "Tahsilat (Aldim)"])
            m = col2.number_input("Tutar (₺)", min_value=0, step=1)
            n = st.text_input("Not / Açıklama")
            # FOTOĞRAF MAKİNESİ / GALERİ
            st.markdown('<p style="font-size:13px; color:#718096; margin-bottom:0;">📷 Belge veya İş Fotoğrafları</p>', unsafe_allow_html=True)
            fotos = st.file_uploader("", accept_multiple_files=True, label_visibility="collapsed")
            
            if st.form_submit_button("✅ KAYDI TAMAMLA"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, int(m), t, n))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.success("İşlem başarıyla eklendi!"); st.rerun()

    # GEÇMİŞ HAREKETLER
    st.markdown("### 📜 GEÇMİŞ")
    k_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} | {row['tip']} | {row['miktar']:,} ₺"):
            st.write(f"📝 {row['aciklama']}")
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows(): cols[i].image(fr['foto'], use_container_width=True)
            if st.button("SİL", key=f"del_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],)); conn.commit(); st.rerun()

else:
    # --- ANA LİSTE SAYFASI ---
    # Özet Kartı
    aldim = int(df_i[df_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
    verdim = int(df_i[df_i['tip'].str.contains("Satis")]['miktar'].sum())
    st.markdown(f"""
    <div class="summary-card">
        <div class="stat-box"><div class="stat-label">ALDĞIM</div><div class="stat-val-up">{aldim:,} ₺</div></div>
        <div style="width:1px; height:40px; background:#E2E8F0;"></div>
        <div class="stat-box"><div class="stat-label">VERDİĞİM</div><div class="stat-val-down">{verdim:,} ₺</div></div>
    </div>
    """, unsafe_allow_html=True)

    # Yeni Müşteri Butonu
    if st.button("➕ YENİ MÜŞTERİ OLUŞTUR"):
        st.session_state['yeni_m'] = True
    
    if st.session_state.get('yeni_m'):
        with st.form("premium_m"):
            ad = st.text_input("Ad Soyad *")
            tel = st.text_input("Telefon")
            adr = st.text_area("Adres")
            c1, c2 = st.columns(2)
            if c1.form_submit_button("✅ KAYDET"):
                if ad:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel, adres) VALUES (?,?,?)", (ad, tel, adr))
                    conn.commit(); st.session_state['yeni_m'] = False; st.rerun()
            if c2.form_submit_button("İPTAL"): st.session_state['yeni_m'] = False; st.rerun()

    st.divider()
    search = st.text_input("🔍 Listede Ara...", placeholder="İsim yazmaya başlayın...")
    
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            
            st.markdown(f"""
            <div class="customer-card">
                <div style="display:flex; align-items:center;">
                    <div class="avatar-circle">{m['ad'][0]}</div>
                    <div>
                        <div style="font-weight:700; color:#2D3748; font-size:16px;">{m['ad']}</div>
                        <div style="font-size:12px; color:#A0AEC0;">📞 {m['tel'] if m['tel'] else 'No Yok'}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-weight:800; font-size:18px; color:{'#C53030' if bakiye > 0 else '#2F855A'};">
                        {abs(bakiye):,} ₺
                    </div>
                    <div style="font-size:11px; font-weight:700; color:#A0AEC0; text-transform:uppercase;">
                        {'BORÇLU' if bakiye > 0 else 'ALACAKLI'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"DETAY / İŞLEM: {m['ad']}", key=f"v_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()

# --- YAN MENÜ: EXCEL YEDEK ---
with st.sidebar:
    st.markdown("### ⚙️ AYARLAR")
    if not df_i.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            yedek = pd.merge(df_i, df_m, left_on='musteri_id', right_on='id')
            yedek = yedek[['tarih', 'ad', 'tip', 'miktar', 'aciklama']]
            yedek.to_excel(writer, index=False, sheet_name='Havas_Yedek')
        st.download_button("📥 TÜM VERİLERİ YEDEKLE", output.getvalue(), "Havas_Ahsap_Yedek.xlsx")
        
