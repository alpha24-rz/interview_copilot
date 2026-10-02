# ⚡ Alpha Interview Teleprompter & Copilot

Sistem asisten wawancara *real-time* berbasis *floating HUD* (selalu di atas layar Zoom/Google Meet) yang dirancang khusus untuk memandu wawancara teknis dan HRD berbahasa Inggris secara instan tanpa latensi (0 ms).

---

## 🚀 Cara Menjalankan

Cukup **klik 2 kali** file:
👉 `run_copilot.bat` (di folder utama)

Atau lewat terminal/PowerShell:
```bash
cd "c:\Users\USER\OneDrive\Dokumen\folder kk alfa\interview_copilot"
python teleprompter_gui.py
```

---

## 🎮 Tombol Cepat Keyboard (Hotkeys)

Saat HRD bertanya, tekan salah satu tombol fungsi ini tanpa perlu mengetik:

| Tombol | Topik Pertanyaan HRD | Deskripsi Jawaban |
| :---: | :--- | :--- |
| **F1** | *Tell me about yourself / Background* | Perkenalan profil, pendidikan di UNM, proyek BMKG, dan Orlith AI. |
| **F2** | *BMKG Experience / RAG Project* | Detail arsitektur RAG, Cross-Encoder reranking, regulasi ASN, FastAPI & Docker. |
| **F3** | *Thesis / Lost in the Middle (LITM)* | Penjelasan bias posisi LITM, IndoNLU FacQA benchmark, dan mitigasi BGE. |
| **F4** | *Function Calling / Agent Tools* | JSON schema, tool use, deteksi intent, penanganan error multi-turn. |
| **F5** | *Orlith AI Platform* | Platform enterprise Multi-Provider LLMs, ChromaDB, token streaming WebSocket. |
| **F6** | *Evaluation Metrics & Benchmarks* | Penjelasan metrik akurasi (EM, F1, MRR, Recall) dan latency trade-off. |
| **Esc** | *Clear Search Bar* | Membersihkan kotak pencarian dan kembali ke F1. |

---

## 🔍 Pencarian Otomatis Kata Kunci (*Search-as-you-type*)

Jika pertanyaan HRD di luar 6 tombol di atas, cukup ketik **2–4 huruf saja** di kotak pencarian:
* Ketik `weak` atau `streng` $\rightarrow$ Muncul jawaban Kelebihan & Kekurangan (*Strengths & Weaknesses*).
* Ketik `remot` atau `why` $\rightarrow$ Muncul alasan memilih kerja remote & motivasi di perusahaan tersebut.
* Ketik `stack` atau `pyt` $\rightarrow$ Muncul rincian teknologi (Python, PyTorch, LangChain, FastAPI).
* Ketik `ask` atau `any` $\rightarrow$ Muncul daftar pertanyaan balik berkualitas tinggi untuk diajukan ke HRD di akhir sesi.

---

## 💡 Fitur Unggulan

1. **Always-on-Top:** Jendela mengambang di atas Zoom / Google Meet dan tidak akan tertutup jendela lain.
2. **Posisi Kamera Alami:** Jendela otomatis muncul di tengah atas layar tepat di bawah lensa webcam, sehingga mata Anda tetap terlihat menatap pewawancara.
3. **Format "Say This First" (Opening Hook):** Setiap topik memiliki kalimat pembuka natural yang siap Anda ucapkan terlebih dahulu untuk mengulur waktu 3–5 detik sambil mata Anda melirik poin-poin teknis di bawahnya.
4. **Ukuran Huruf & Transparansi:** Dilengkapi tombol **A- / A+** dan *slider opacity* agar teks nyaman dibaca sekilas.
5. **Auto-Clipboard Sync:** Centang `📋 Auto-Clipboard`. Jika Anda menyalakan *Live Caption [CC]* di Google Meet dan meng-copy teks subtitle, jawaban akan langsung berganti otomatis!
