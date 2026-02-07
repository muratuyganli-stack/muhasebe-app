import customtkinter as ctk

class VeresiyeUygulamasi(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Dijital Veresiye Defteri")
        self.geometry("400x500")
        ctk.set_appearance_mode("dark") 

        # Başlık
        self.label = ctk.CTkLabel(self, text="Müşteri Borç Kaydı", font=("Arial", 20, "bold"))
        self.label.pack(pady=20)

        # Giriş Alanları
        self.musteri_entry = ctk.CTkEntry(self, placeholder_text="Müşteri Adı", width=250)
        self.musteri_entry.pack(pady=10)

        self.miktar_entry = ctk.CTkEntry(self, placeholder_text="Miktar (TL)", width=250)
        self.miktar_entry.pack(pady=10)

        # Butonlar
        self.ekle_button = ctk.CTkButton(self, text="Borç Ekle", fg_color="red", hover_color="#8B0000", command=self.borc_ekle)
        self.ekle_button.pack(pady=10)

        self.odeme_button = ctk.CTkButton(self, text="Ödeme Al", fg_color="green", hover_color="#006400", command=self.odeme_al)
        self.odeme_button.pack(pady=10)

        # Bilgi Ekranı
        self.sonuc_box = ctk.CTkTextbox(self, width=300, height=150)
        self.sonuc_box.pack(pady=20)

    def borc_ekle(self):
        isim = self.musteri_entry.get()
        miktar = self.miktar_entry.get()
        self.sonuc_box.insert("end", f"BORÇ: {isim} -> {miktar} TL eklendi.\n")

    def odeme_al(self):
        isim = self.musteri_entry.get()
        miktar = self.miktar_entry.get()
        self.sonuc_box.insert("end", f"ÖDEME: {isim} -> {miktar} TL alındı.\n")

if __name__ == "__main__":
    app = VeresiyeUygulamasi()
    app.mainloop()
        
