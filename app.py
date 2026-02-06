import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# Veritabanı v27
def init_db():
    conn = sqlite3.connect('muhasebe_v27.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- GELİŞMİŞ GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    
    /* Başlık */
    .shop-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 12px; border-radius: 10px; color: white; text-align: center; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .shop-title { font-family: 'Arial Black', sans-serif; font-size: 22px; margin: 0; }
    
    /* ÖZEL YENİ MÜŞTERİ BUTONU TASARIMI */
    .add-customer-container {
        background: white;
        padding: 2px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 2px dashed #3b82f6;
        transition: 0.3s;
    }
    
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
        color: white;
        border: none;
        padding: 15px 20px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 12px;
        width: 100%;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
        transition: all 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
    }

    /* Cari Kartlar */
    .cari-kart {
        background: white; padding: 15px; border-radius: 12px; margin-bottom: 10px;
        border-left: 6px solid #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
st.markdown('<div class="shop-header"><p class="shop-title">🔨 HAVAS AHŞAP | Cari Takip</p></div>', unsafe_allow_html=True)

# Verileri Çek
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- ANA SAYFA AKIŞI ---
if 'secili_id' not in st.session_state:
    
    # ŞIK YENİ MÜŞTERİ BUTONU
    if st.button("➕ YENİ MÜŞTERİ / CARİ KART OLUŞTUR"):
        st.session_state['yeni_m_ekran'] = True

    # Yeni Müşteri Formu (Butona basınca açılır)
    if st.session_state.get('yeni_m_ekran'):
        with st.container(border=True):
            st.markdown("### 👤 Yeni Müşteri Bilgileri")
            with st.form("yeni_m_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                n_ad = col1.text_input("Ad Soyad", placeholder="Örn: Mehmet Yılmaz")
                n_tel = col2.text_input("Telefon", placeholder="05XX XXX XX XX")
                c_ekle, c_vazgec = st.columns(2)
                if c_ekle.form_submit_button("✅ SİSTEME KAYDET"):
                    if n_ad:
                        conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (n_ad, n_tel))
                        conn.commit()
                        st.session_state['yeni_m_ekran'] = False
                        st.success("Müşteri başarıyla eklendi!")
                        st.rerun()
                if c_vazgec.form_submit_button("❌ İPTAL"):
                    st.session_state['yeni_m_ekran'] = False
                    st.rerun()

    st.divider()

    # Müşteri Arama ve Listeleme
    if not df_m.empty:
        search = st.text_input("🔍 Listede Ara...", placeholder="Müşteri ismini buraya yazın")
        for _, m in df_m.iterrows():
            if search.lower() in m['ad'].lower():
                m_islemler = df_i[df_i['musteri_id'] == m['id']]
                bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - \
                         m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
                
                st.markdown(f"""
                    <div class="cari-kart">
                        <table style="width:100%;">
                            <tr>
                                <td style="width:70%;">
                                    <b style="font-size:18px;">{m['ad']}</b><br>
                                    <small style="color:gray;">📞 {m['tel'] if m['tel'] else 'Telefon yok'}</small>
                                </td>
                                <td style="text-align:right;">
                                    <span style="font-size:18px; font-weight:bold; color:{'#d9534f' if bakiye > 0 else '#28a745'};">
                                        {abs(bakiye):,.2f} TL
                                    </span>
                                </td>
                            </tr>
                        </table>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"🔎 Detay ve İşlemler: {m['ad']}", key=f"go_{m['id']}"):
                    st.session_state['secili_id'] = m['id']
                    st.rerun()

# --- DETAY EKRANI (Müşteri Seçilince) ---
else:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ ANA LİSTEYE DÖN"):
        del st.session_state['secili_id']; st.rerun()
    
    st.markdown(f"## 📋 {m_bilgi['ad']}")
    
    # İşlem ekleme formu ve geçmişi burada devam ediyor...
    # (Önceki kararlı sürümdeki fotoğraf ekleme ve işlem görme kodları aktiftir)
    with st.expander("➕ YENİ İŞLEM / FOTOĞRAF EKLE", expanded=True):
        with st.form("islem_detay", clear_on_submit=True):
            t = st.selectbox("İşlem", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
            mik = st.number_input("Tutar", min_value=0.0)
            fotos = st.file_uploader("Fotoğraflar", accept_multiple_files=True)
            if st.form_submit_button("KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, mik, t, ""))
                is_id = c.lastrowid
                for f in fotos: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit(); st.rerun()
                
