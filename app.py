import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Veritabanı v25
def init_db():
    conn = sqlite3.connect('muhasebe_v25.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS musteriler (id INTEGER PRIMARY KEY AUTOINCREMENT, ad TEXT, tel TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS islemler (id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER, tarih TEXT, tip TEXT, miktar REAL, aciklama TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS fotograflar (islem_id INTEGER, foto BLOB)''')
    conn.commit()
    return conn

conn = init_db()
st.set_page_config(page_title="HAVAS AHŞAP", layout="wide")

# --- GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    .shop-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }
    .cari-kart {
        background: white; padding: 15px; border-radius: 12px; margin-bottom: 10px;
        border-left: 8px solid #3b82f6; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stButton>button { border-radius: 10px; font-weight: bold; }
    .bakiye-pozitif { color: #d9534f; font-weight: bold; font-size: 20px; }
    .bakiye-negatif { color: #28a745; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- BAŞLIK ---
st.markdown('<div class="shop-header"><h1 style="margin:0;">🔨 HAVAS AHŞAP</h1><p style="margin:0;">Hızlı Cari ve İşlem Takibi</p></div>', unsafe_allow_html=True)

# Verileri Çek
df_m = pd.read_sql_query("SELECT * FROM musteriler", conn)
df_i = pd.read_sql_query("SELECT * FROM islemler", conn)

# --- EKRAN YÖNETİMİ ---
# Eğer bir müşteri seçildiyse doğrudan işlem sayfasını göster
if 'secili_id' in st.session_state:
    m_id = st.session_state['secili_id']
    m_bilgi = df_m[df_m['id'] == m_id].iloc[0]
    
    if st.button("⬅️ LİSTEYE GERİ DÖN"):
        del st.session_state['secili_id']
        st.rerun()
    
    st.markdown(f"## 👤 {m_bilgi['ad']}")
    
    # Yeni İşlem ve Fotoğraf Ekleme Alanı
    with st.container(border=True):
        st.subheader("➕ Yeni İşlem / Fotoğraf Ekle")
        with st.form("islem_formu", clear_on_submit=True):
            col_t, col_m = st.columns(2)
            tip = col_t.selectbox("İşlem Tipi", ["Satis (Alacak Yaz)", "Tahsilat (Borctan Dus)"])
            mik = col_m.number_input("Tutar (TL)", min_value=0.0)
            not_ = st.text_input("Açıklama / Not")
            fotos = st.file_uploader("Fotoğraf Ekle (Çoklu)", accept_multiple_files=True)
            if st.form_submit_button("KAYDI TAMAMLA"):
                c = conn.cursor()
                tarih = datetime.now().strftime("%d-%m-%Y %H:%M")
                c.execute("INSERT INTO islemler (musteri_id, tarih, miktar, tip, aciklama) VALUES (?,?,?,?,?)", (int(m_id), tarih, mik, tip, not_))
                is_id = c.lastrowid
                for f in fotos:
                    c.execute("INSERT INTO fotograflar VALUES (?,?)", (is_id, f.read()))
                conn.commit()
                st.success("İşlem başarıyla eklendi!")
                st.rerun()

    # Geçmiş Hareketler
    st.markdown("### 📜 Geçmiş Hareketler")
    k_df = df_i[df_i['musteri_id'] == m_id].sort_values(by='id', ascending=False)
    for _, row in k_df.iterrows():
        with st.expander(f"📌 {row['tarih']} - {row['tip']} - {row['miktar']} TL"):
            st.write(f"**Not:** {row['aciklama']}")
            f_df = pd.read_sql_query(f"SELECT foto FROM fotograflar WHERE islem_id = {row['id']}", conn)
            if not f_df.empty:
                cols = st.columns(len(f_df))
                for i, fr in f_df.iterrows():
                    cols[i].image(fr['foto'], use_container_width=True)
            if st.button("🗑️ İşlemi Sil", key=f"del_{row['id']}"):
                conn.cursor().execute("DELETE FROM islemler WHERE id=?", (row['id'],))
                conn.commit(); st.rerun()

# --- ANA SAYFA (LİSTE) ---
else:
    with st.expander("👤 YENİ MÜŞTERİ EKLE"):
        with st.form("yeni_m"):
            ad = st.text_input("Müşteri Ad Soyad")
            tel = st.text_input("Telefon")
            if st.form_submit_button("KAYDET"):
                if ad:
                    conn.cursor().execute("INSERT INTO musteriler (ad, tel) VALUES (?,?)", (ad, tel))
                    conn.commit(); st.rerun()

    st.divider()
    
    if not df_m.empty:
        search = st.text_input("🔍 Müşteri Ara...", placeholder="İsim yazın...")
        for _, m in df_m.iterrows():
            if search.lower() in m['ad'].lower():
                m_islemler = df_i[df_i['musteri_id'] == m['id']]
                bakiye = m_islemler[m_islemler['tip'].str.contains("Satis")]['miktar'].sum() - \
                         m_islemler[m_islemler['tip'].str.contains("Tahsilat")]['miktar'].sum()
                
                # Kart Tasarımı
                st.markdown(f"""
                    <div class="cari-kart">
                        <table style="width:100%;">
                            <tr>
                                <td><b>{m['ad']}</b><br><small>{m['tel']}</small></td>
                                <td style="text-align:right;">
                                    <span class="{'bakiye-pozitif' if bakiye > 0 else 'bakiye-negatif'}">{abs(bakiye):,.2f} TL</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                """, unsafe_allow_html=True)
                
                # Kartın altına tıklama butonu (Hemen geçiş yapar)
                if st.button(f"İŞLEMLERİ GÖR: {m['ad']}", key=f"go_{m['id']}"):
                    st.session_state['secili_id'] = m['id']
                    st.rerun()
                
