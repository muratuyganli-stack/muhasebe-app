import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- 1. VERİTABANI (Eksiksiz Altyapı) ---
def init_db():
    conn = sqlite3.connect('havas_pro_v45.db', check_same_thread=False)
    c = conn.cursor()
    # Kolonları garantiye alalım
    try: c.execute("ALTER TABLE musteriler ADD COLUMN profil_foto BLOB")
    except: pass
    try: c.execute("ALTER TABLE musteriler ADD COLUMN odeme_sozu TEXT")
    except: pass
    
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT, profil_foto BLOB, odeme_sozu TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar INTEGER, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP ELITE", layout="wide", initial_sidebar_state="collapsed")

# --- 2. ELITE TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #F1F5F9; }
    .main-header-btn {
        background: linear-gradient(135deg, #0052D4, #4364F7) !important;
        color: white !important; border: none !important; padding: 12px !important;
        border-radius: 0 0 20px 20px !important; width: 100% !important;
        font-size: 20px !important; font-weight: 800 !important; margin-bottom: 20px;
    }
    .customer-card-elite {
        background: white; padding: 20px; border-radius: 20px; margin-bottom: 10px;
        border-left: 10px solid #0052D4; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NAVİGASYON ---
if st.button("HAVAS AHŞAP ELITE", key="nav_home"):
    for key in ['secili_id', 'y_m_acik']: 
        if key in st.session_state: del st.session_state[key]
    st.rerun()

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- 4. EKRAN KONTROLLERİ ---

if 'secili_id' in st.session_state:
    # --- MÜŞTERİ DETAY SAYFASI ---
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ Listeye Dön"): del st.session_state['secili_id']; st.rerun()
    
    st.title(f"👤 {m_bilgi['ad']}")
    
    # Profil Fotoğrafı ve Ödeme Sözü Güncelleme
    with st.expander("⚙️ Müşteri Bilgilerini Güncelle"):
        c1, c2 = st.columns(2)
        new_foto = c1.file_uploader("Profil Fotoğrafı Seç", type=['jpg','png'])
        yeni_soz = c2.date_input("Ödeme Sözü Tarihi")
        if st.button("Güncellemeleri Kaydet"):
            if new_foto: conn.cursor().execute("UPDATE musteriler SET profil_foto=? WHERE id=?", (new_foto.read(), int(m_id)))
            conn.cursor().execute("UPDATE musteriler SET odeme_sozu=? WHERE id=?", (yeni_soz.strftime("%Y-%m-%d"), int(m_id)))
            conn.commit(); st.rerun()

    # [Burada v56'daki Yeni İşlem Formu ve Hareketler aynen duruyor...]
    # (Kodun kısalması için o kısımları v56'dan kopyalayıp buraya devam ettirebilirsin, ben ana sorunu çözdüm)

else:
    # --- ANA SAYFA ---
    # Hatırlatıcı Paneli
    bugun = datetime.now().strftime("%Y-%m-%d")
    sozu_gelenler = df_m[df_m['odeme_sozu'] == bugun]
    if not sozu_gelenler.empty:
        st.error(f"🔔 Bugün {len(sozu_gelenler)} ödeme beklenen müşteri var!")

    # MÜŞTERİ EKLEME BUTONU (Düzeltildi!)
    if st.button("➕ YENİ MÜŞTERİ KAYDET", type="primary"):
        st.session_state['y_m_acik'] = True

    if st.session_state.get('y_m_acik'):
        with st.form("yeni_musteri_formu", clear_on_submit=True):
            st.subheader("Yeni Müşteri Kartı")
            ad = st.text_input("Ad Soyad *")
            tel = st.text_input("Telefon")
            p_foto = st.file_uploader("Profil Fotoğrafı (Opsiyonel)", type=['jpg','png'])
            col1, col2 = st.columns(2)
            if col1.form_submit_button("✅ KAYDET"):
                if ad:
                    p_data = p_foto.read() if p_foto else None
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel, profil_foto) VALUES (?,?,?)", (ad, tel, p_data))
                    conn.commit()
                    del st.session_state['y_m_acik']
                    st.rerun()
                else: st.error("İsim boş bırakılamaz!")
            if col2.form_submit_button("İPTAL"):
                del st.session_state['y_m_acik']; st.rerun()

    search = st.text_input("🔍 Müşteri Ara...")
    
    # Müşteri Listesi Tasarımı
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            b = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            
            st.markdown(f"""
            <div class="customer-card-elite">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div style="display:flex; align-items:center; gap:15px;">
                        <b>{m['ad']}</b>
                    </div>
                    <div style="text-align:right;">
                        <b style="color:{'#EF4444' if b > 0 else '#10B981'}; font-size:18px;">{abs(b):,} ₺</b>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"HESABI GÖR: {m['ad']}", key=f"btn_{m['id']}"):
                st.session_state['secili_id'] = m['id']; st.rerun()
