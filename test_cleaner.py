import re

raw = """14.04
ojd-mykf-smz
ojd-mykf-smz
info
Detail rapat
1
Tekan Panah Bawah untuk membuka baki tempat Anda mengarahkan kursor dan Escape untuk menutupnya.
Buat catatan dengan Gemini
pen_spark
Tekan Panah Bawah untuk membuka baki tempat Anda mengarahkan kursor dan Escape untuk menutupnya.
Muhammad alfarizi
Muhammad alfarizi
language
Inggris
format_size
Ukuran font
circle
Warna font
settings
Buka setelan teks
Anda
Hello! What's your name? Hello! What's your name? What do you mean? Hello! Hello! What's your name? Tell me about yourself.
keyboard_arrow_up
Setelan audio
mic
Nonaktifkan mikrofon (ctrl + d)
keyboard_arrow_up
Setelan Video
videocam_off
Aktifkan kamera (ctrl + e)
computer_arrow_up
Bagikan layar
mood
Kirim reaksi
closed_caption
Nonaktifkan teks (c atau shift + c)
back_hand
Angkat tangan (ctrl + alt + h)
more_vert
Opsi lainnya
call_end
Tutup panggilan
chat
Chat dengan semua orang
apps
Alat rapat
lock_person
Kontrol penyelenggara"""

def clean_meet_text(text):
    # Pola: cari teks setelah nama pembicara (misal "Anda\n" atau nama orang) dan sebelum "keyboard_arrow_up"
    # Atau potong baris-baris menu
    if "keyboard_arrow_up" in text:
        parts = text.split("keyboard_arrow_up")[0]
        # Cari baris setelah 'Buka setelan teks' atau 'Anda'
        lines = [l.strip() for l in parts.split("\n") if l.strip()]
        # Ambil baris terakhir sebelum keyboard_arrow_up yang bukan nama pembicara
        spoken_lines = []
        capture = False
        for l in lines:
            if l in ["Buka setelan teks", "Warna font", "Ukuran font", "settings", "circle", "format_size", "language", "Inggris"]:
                capture = True
                continue
            if capture and l != "Anda" and not l.startswith("Muhammad"):
                spoken_lines.append(l)
        if spoken_lines:
            return " ".join(spoken_lines)
    return text

print("RESULT:", clean_meet_text(raw))
