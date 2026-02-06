import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Veritabanı v24
def init_db():
    conn = sqlite3.connect('muhasebe_v24.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide", initial_sidebar_state="collapsed")

# --- GÜÇLÜ GÖRSEL TASARIM (CSS) ---
st.markdown("""
    <style>
    /* Arka Plan ve Genel Font */
    .stApp { background-color: #f4f7f6; }
    
    /* Başlık Tasarımı */
    .shop-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .shop-title { font-family: 'Arial Black', sans-serif; font-size: clamp(28px, 10vw, 45px); margin: 0; }
    
    /* Kart Tasarımları */
    .cari-kart {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        border-left: 8px solid #3b82f6;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Butonları Güzelleştirme */
    .stButton>button {
        border-radius: 10px;
        height: 3.2em;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Sayısal Göstergeler */
    .bakiye-pozitif { color: #d9534f; font-size: 24px; font-weight: bold; }
    .bakiye-negatif { color: #28a745; font-size: 24px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
st.markdown('<div class="shop-header"><p class="shop-title">🔨 HAVAS AHŞAP</p><p>Mobilya & Mimarlık Cari Takip</p></div>', unsafe_allow_html=True)

# --- ÜST MENÜ: YENİ KAYIT ---
col_ekle, col_bos = st.columns([2, 2])
with col_ekle:
    with st.expander("👤 YENİ MÜŞTERİ TANIMLA", expanded=False):
        with st.form("yeni_m"):
            ad = st.text_input("Müşteri Ad Soyad")
            tel = st.text_input("Telefon No")
            if st.form_submit_button("REHBERE KAYDET"):
                if ad:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (ad, tel))
                    conn.commit(); st.rerun()

st.divider()

# Verileri Çek
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- MÜŞTERİ LİSTESİ ---
if not df_m.empty:
    search = st.text_input("🔍 Müşteri Ara...", placeholder="İsim veya telefon yazın...")
    
    for _, m in df_m.iterrows():
        if search.lower() in m['ad'].lower():
            # Bakiye Hesabı
            m_islemler = df_i[df_i['musteri_id'] == m['id']]
            bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - \
                     m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
            
            # GÖRSEL KART
            st.markdown(f"""
                <div class="cari-kart">
                    <table style="width:100%; border:none;">
                        <tr>
                            <td style="width:60%;">
                                <b style="font-size:20px; color:#1e3a8a;">{m['ad']}</b><br>
                                <span style="color:grey;">📞 {m['tel'] if m['tel'] else 'Kayıt Yok'}</span>
                            </td>
                            <td style="text-align:right;">
                                <span class="{'bakiye-pozitif' if bakiye > 0 else 'bakiye-negatif'}">
                                    {abs(bakiye):,.2f} TL
                                </span><br>
                                <small style="color:grey;">{'BORÇLU' if bakiye > 0 else 'ALACAKLI'}</small>
                            </td>
                        </tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)
            
            # İşlem Butonu (Kartın hemen altına)
            if st.button(f"⚙️ İŞLEM VE FOTOĞRAF: {m['ad']}", key=f"is_{m['id']}"):
                st.session_state['aktif_m'] = m['id']; st.rerun()

# --- İŞLEM PANELİ ---
if 'aktif_m' in st.session_state:
    m_id = st.session_state['aktif_m']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    with st.sidebar:
        st.header(f"📑 {m_bilgi['ad']}")
        if st.button("⬅️ ANA SAYFAYA DÖN"):
            del st.session_state['aktif_m']; st.rerun()
        
        st.divider()
        with st.form("islem_f", clear_on_submit=True):
            tip = st.selectbox("İşlem Tipi", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
            mik = st.number_input("Tutar", min_value=0.0)
            foto = st.file_uploader("Fotoğrafları Yükle (Çoklu)", accept_multiple_files=True)
            if st.form_submit_button("KAYDET"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, mik, tip, ""))
                is_id = c.lastrowid
                for r in foto: c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, r.read()))
                conn.commit(); st.rerun()
        
        if st.button("🗑️ BU CARİYİ TAMAMEN SİL"):
            conn.cursor().execute("DELETE FROM musteriler WHERE id=?", (m_id,))
            conn.commit(); del st.session_state['aktif_m']; st.rerun()
            
