import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- 1. VERİTABANI GÜNCELLEME (Yeni kolonlar ekleniyor) ---
def init_db():
    conn = sqlite3.connect('havas_pro_v45.db', check_same_thread=False)
    c = conn.cursor()
    # Mevcut tablolara yeni alanlar ekleme (Hata vermemesi için IF NOT EXISTS mantığı)
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

# --- 2. ELITE TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #F1F5F9; }
    
    /* Elite Müşteri Kartları */
    .elite-card {
        background: white; padding: 25px; border-radius: 24px; margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        display: flex; align-items: center; gap: 20px;
        border: 1px solid rgba(255,255,255,0.7);
    }
    .profile-img {
        width: 70px; height: 70px; border-radius: 50%; object-fit: cover;
        border: 3px solid #0052D4; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .status-badge {
        padding: 5px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVİGASYON ---
if st.button("HAVAS AHŞAP ELITE", key="header_home"):
    for key in ['secili_id', 'y_m']: 
        if key in st.session_state: del st.session_state[key]
    st.rerun()

df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ Listeye Dön"): del st.session_state['secili_id']; st.rerun()
    
    col_p, col_t = st.columns([1, 4])
    with col_p:
        if m_bilgi['profil_foto']: st.image(m_bilgi['profil_foto'], width=120)
        else: st.warning("Foto Yok")
        new_p = st.file_uploader("Değiştir", type=['jpg','png'], key="p_up")
        if new_p:
            conn.cursor().execute("UPDATE musteriler SET profil_foto=? WHERE id=?", (new_p.read(), int(m_id)))
            conn.commit(); st.rerun()
            
    with col_t:
        st.title(f"👤 {m_bilgi['ad']}")
        o_tarih = st.date_input("Tahsilat Sözü Tarihi", value=datetime.now())
        if st.button("Sözü Kaydet"):
            conn.cursor().execute("UPDATE musteriler SET odeme_sozu=? WHERE id=?", (o_tarih.strftime("%Y-%m-%d"), int(m_id)))
            conn.commit(); st.success("Tarih kaydedildi!")

    # İşlem ekleme ve listeleme kısımları (v56 ile aynı, bozulmadı)
    # ... [Burada v56'daki işlem kodları aynen devam eder] ...
    
else:
    # --- ANA SAYFA: HATIRLATICI VE LİSTE ---
    bugun = datetime.now().strftime("%Y-%m-%d")
    sozu_gelenler = df_m[df_m['odeme_sozu'] == bugun]
    
    if not sozu_gelenler.empty:
        st.error(f"🔔 Bugün {len(sozu_gelenler)} Kişiden Ödeme Bekleniyor!")
        for _, r in sozu_gelenler.iterrows():
            st.info(f"💰 {r['ad']} - Söz Verilen Tarih: Bugün")

    search = st.text_input("🔍 Müşteri veya İşlem Ara...")
    
    if st.button("➕ YENİ MÜŞTERİ EKLE"): st.session_state['y_m'] = True
    
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            m_i = df_i[df_i['musteri_id'] == m['id']]
            bakiye = int(m_i[m_i['tip'].str.contains("Satis")]['miktar'].sum() - m_i[m_i['tip'].str.contains("Tahsilat")]['miktar'].sum())
            
            # ELITE KART GÖRÜNÜMÜ
            with st.container():
                c1, c2, c3 = st.columns([1, 3, 2])
                with c1:
                    if m['profil_foto']: st.image(m['profil_foto'], width=80)
                    else: st.image("https://via.placeholder.com/150", width=80) # Varsayılan ikon
                with c2:
                    st.markdown(f"### {m['ad']}")
                    st.caption(f"📞 {m['tel']}")
                    if m['odeme_sozu']: st.markdown(f"📅 Söz: {m['odeme_sozu']}")
                with c3:
                    st.markdown(f"## {bakiye:,} ₺")
                    if st.button("DETAY", key=f"det_{m['id']}"):
                        st.session_state['secili_id'] = m['id']; st.rerun()
                st.divider()

