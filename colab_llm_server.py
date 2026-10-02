"""
=============================================================================
⚡ ALPHA INTERVIEW COPILOT: GOOGLE COLAB LLM SERVER (L4 / A100 GPU)
=============================================================================
Arsitektur 3-Lapis:
1. Lapis 1 (Fakta Diri & CV): BMKG RAG, Orlith AI Platform, Skripsi LITM (UNM).
2. Lapis 2 (Wawasan CS & AI/ML): Pengetahuan frontier model untuk teori umum & coding.
3. Lapis 3 (Smart Bridge): Menjembatani tools baru dengan growth mindset & analogi cerdas.

Cara Menjalankan di Google Colab:
1. Buka Google Colab -> Menu Runtime -> Change runtime type -> Pilih "L4 GPU" atau "A100 GPU".
2. Jalankan [CELL 1] untuk instalasi library dan Cloudflared.
3. Jalankan [CELL 2] untuk memulai server LLM dan mendapatkan URL Publik Cloudflare.
4. Salin URL publik (https://xxx.trycloudflare.com) ke bar '⚡ Colab URL' di Teleprompter Anda.
=============================================================================
"""

# =============================================================================
# [CELL 1] INSTALASI DEPENDENSI (Jalankan sekali di Colab)
# =============================================================================
"""
!pip install -q fastapi uvicorn transformers accelerate torch bitsandbytes
!curl -LO https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb
"""

# =============================================================================
# [CELL 2] JALANKAN SERVER LLM DI GPU (Qwen-2.5-14B / 32B / 7B)
# =============================================================================
import os, gc, time, re, threading, subprocess
import torch
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TextIteratorStreamer

# ------------------------------------------------------------------------------
# 1. BERSIHKAN PORT 8000 & SISA VRAM
# ------------------------------------------------------------------------------
print("🧹 Membersihkan port 8000 & memori GPU sebelumnya...")
subprocess.run(["fuser", "-k", "8000/tcp"], stderr=subprocess.DEVNULL)
subprocess.run(["pkill", "-f", "cloudflared"], stderr=subprocess.DEVNULL)
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()
time.sleep(2)

# ------------------------------------------------------------------------------
# 2. DETEKSI GPU & PILIH MODEL
# ------------------------------------------------------------------------------
gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
gpu_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3) if torch.cuda.is_available() else 0
print(f"🎮 GPU Terdeteksi: {gpu_name} ({gpu_vram:.1f} GB VRAM)")

# Pilihan Model Unggulan:
# 1. "Qwen/Qwen2.5-14B-Instruct" -> Sweet spot: sangat cerdas, menyaingi GPT-4o-mini, penalaran mantap.
# 2. "Qwen/Qwen2.5-32B-Instruct" -> Flagship reasoning: cocok untuk A100 atau L4 (4-bit).
# 3. "Qwen/Qwen2.5-7B-Instruct"  -> Ultra-kencang: respon sub-detik di L4.
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct"

# Kuantisasi Otomatis:
# Jika di GPU L4 (24GB VRAM) atau GPU dengan VRAM < 36GB, gunakan 4-bit NF4 (~9GB VRAM untuk 14B).
# Jika di GPU A100 (40GB/80GB), gunakan full 16-bit bfloat16 tanpa kuantisasi!
USE_4BIT = True if (gpu_vram < 36 and ("14B" in MODEL_ID or "32B" in MODEL_ID)) else False

print(f"⏳ Sedang memuat model: {MODEL_ID}")
print(f"⚙️  Konfigurasi Presisi: {'4-Bit NF4 BitsAndBytes (Hemat VRAM)' if USE_4BIT else 'Full 16-Bit bfloat16/float16'}")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

if USE_4BIT:
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        attn_implementation="sdpa"
    )
else:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
        device_map="auto",
        attn_implementation="sdpa"
    )

print("✅ Model Berhasil Dimuat 100% di GPU VRAM!")

# ------------------------------------------------------------------------------
# 3. SYSTEM PROMPT ULTRA-CONCISE (SINGKAT, PADAT, BERBOBOT, & CEPAT)
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an ultra-concise, real-time English interview teleprompter copilot for Muhammad Alfarizi.

CANDIDATE TRUE PROFILE (Foundational Grounding):
- Identity: Muhammad Alfarizi, Computer Science graduate from UNM (GPA 3.86/4.00).
- BMKG Internship: Legal document RAG, Hierarchical chunking (Bab/Pasal/Ayat), BGE Cross-Encoder reranking (94.2% Top-3 hit rate), FastAPI async streaming, Docker containerization.
- Orlith AI: Enterprise LLM Gateway ('Corporate Brain'), multi-provider (OpenAI, Gemini, Anthropic, Ollama), WebSocket streaming, ChromaDB vector store, BYOK AES-256.
- Thesis (UNM): Mitigating 'Lost in the Middle' (LITM) positional bias in Indonesian RAG using Cross-Encoder reranking on IndoNLU FacQA (restored accuracy from -31% drop to 91%+).
- Tech Stack: Python, PyTorch, Transformers, LangChain, LlamaIndex, FastAPI, Docker, ChromaDB, Qdrant, PostgreSQL.

STRICT CONCISENESS & SPEED RULES:
1. EXTREME BREVITY (Target: 40 - 60 words total):
   - Interviewers value crisp, confident answers without rambling.
2. SPOKEN TELEPROMPTER FORMAT:
   - 1 short natural hook sentence (e.g. "At BMKG, I addressed this directly in our RAG architecture:").
   - Exactly 2 to 3 punchy bullet points (maximum 10-14 words each, packed with real tools and metrics).
   - 1 short concluding sentence (e.g. "This ensured high retrieval precision and sub-second latency.").
3. DYNAMIC GROUNDING:
   - If asked about resume/projects: Ground 100% on BMKG, Orlith AI, or Thesis with real metrics.
   - If asked about AI theory: Give the direct, senior-level engineering answer in 2 crisp points.
   - If asked about tools not in resume: Honestly bridge to mastered equivalents (e.g., "While I haven't used Tool X in production, I implemented the identical containerized workflow using Docker and FastAPI.").
4. ZERO FLUFF: Output ONLY the spoken words. Absolutely no markdown title headers ('### Response'), no preambles.
"""

# ------------------------------------------------------------------------------
# 4. FASTAPI APP & INFERENCE ENDPOINT
# ------------------------------------------------------------------------------
app = FastAPI(title="Alpha Interview Copilot Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def health_check():
    return {"status": "running", "model": MODEL_ID, "gpu": gpu_name, "use_4bit": USE_4BIT}

# Endpoint Streaming Real-Time (Latency < 0.3s to first word!)
@app.post("/generate_stream")
def generate_stream(req: QueryRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"The interviewer asked: \"{req.question}\". Give me the spoken answer."}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([prompt], return_tensors="pt").to(model.device)

    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    generation_kwargs = dict(
        **inputs,
        streamer=streamer,
        max_new_tokens=80,
        temperature=0.25,
        do_sample=True,
        top_p=0.85,
        pad_token_id=tokenizer.eos_token_id
    )

    thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()

    def event_stream():
        for text in streamer:
            yield text

    return StreamingResponse(event_stream(), media_type="text/plain")

@app.post("/generate")
def generate_answer(req: QueryRequest):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"The interviewer asked: \"{req.question}\". Give me the spoken answer."}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([prompt], return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            temperature=0.25,
            do_sample=True,
            top_p=0.85,
            pad_token_id=tokenizer.eos_token_id
        )

    generated_ids = [
        out[len(inp):] for inp, out in zip(inputs.input_ids, outputs)
    ]
    answer = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
    return {"status": "ok", "answer": answer}

# ------------------------------------------------------------------------------
# 5. JALANKAN SERVER SECARA BACKGROUND & AKTIFKAN CLOUDFLARE TUNNEL
# ------------------------------------------------------------------------------
def start_uvicorn():
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    server = uvicorn.Server(config)
    server.run()

server_thread = threading.Thread(target=start_uvicorn, daemon=True)
server_thread.start()
print("✅ Local API Server aktif di port 8000!")

if os.path.exists("tunnel.log"):
    os.remove("tunnel.log")

subprocess.Popen(["cloudflared", "tunnel", "--url", "http://127.0.0.1:8000", "--logfile", "tunnel.log"])

print("⏳ Menghubungkan ke Cloudflare Tunnel...")
public_url = None
for _ in range(15):
    time.sleep(1)
    if os.path.exists("tunnel.log"):
        with open("tunnel.log", "r") as f:
            matches = re.findall(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', f.read())
            if matches:
                public_url = matches[-1]
                break

print("\n" + "="*65)
if public_url:
    print("🎉 SERVER BERHASIL AKTIF & SIAP DIGUNAKAN!")
    print(f"🚀 URL PUBLIK COLAB ANDA: {public_url}")
    print("="*65)
    print("👉 LANGKAH SELANJUTNYA:")
    print(f"1. Salin URL di atas: {public_url}")
    print("2. Buka Teleprompter Anda di Laptop/PC.")
    print("3. Paste URL ke kolom '⚡ Colab URL' dan klik 'Save & Connect'.")
    print("="*65 + "\n")
else:
    print("⚠️ URL belum terdeteksi otomatis. Silakan buka file tunnel.log di panel kiri Colab.")
    print("="*65 + "\n")

# Menjaga agar cell tetap hidup
while True:
    time.sleep(1)
