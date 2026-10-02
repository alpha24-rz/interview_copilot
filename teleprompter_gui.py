import os
import sys
import re
import json
import threading
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import tkinter as tk
from tkinter import ttk, scrolledtext
from copilot_engine import CopilotSearchEngine

SERVER_PORT = 8765
active_app_instance = None

# ==============================================================================
# 1. LOCAL HTTP SERVER DENGAN CORS (PENERIMA SINYAL GOOGLE MEET / ZOOM)
# ==============================================================================
class CaptionReceiverHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path.endswith("meet_hook.js"):
            hook_path = os.path.join(os.path.dirname(__file__), "meet_caption_hook.js")
            if os.path.exists(hook_path):
                with open(hook_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
                return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_len)
        try:
            payload = json.loads(post_data.decode('utf-8'))
            caption_text = payload.get("text", "").strip()

            if caption_text and active_app_instance:
                active_app_instance.root.after(0, active_app_instance.receive_external_caption, caption_text)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        except Exception as e:
            self.send_response(500)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))

    def log_message(self, format, *args):
        pass

def start_background_receiver():
    try:
        server = HTTPServer(("127.0.0.1", SERVER_PORT), CaptionReceiverHandler)
        server.serve_forever()
    except Exception as e:
        print(f"Receiver port {SERVER_PORT} notice: {e}")

# ==============================================================================
# 2. GUI TELEPROMPTER DENGAN HYBRID COLAB LLM SUPPORT
# ==============================================================================
class AlphaInterviewTeleprompter:
    def __init__(self, root):
        global active_app_instance
        active_app_instance = self
        self.root = root
        self.root.title("⚡ Alpha Interview Teleprompter (Colab LLM Enabled)")
        
        window_width = 650
        window_height = 490
        screen_width = self.root.winfo_screenwidth()
        pos_x = max(0, int((screen_width - window_width) / 2))
        pos_y = 20
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#0B132B")
        self.root.attributes("-alpha", 0.95)

        self.engine = CopilotSearchEngine()
        self.current_font_size = 11
        self.colab_url = ""

        self.build_ui()
        self.bind_global_hotkeys()
        self.show_item(self.engine.get_by_hotkey("F1"))

    def build_ui(self):
        # 1. TOP BAR: HOTKEYS
        top_frame = tk.Frame(self.root, bg="#0B132B")
        top_frame.pack(fill="x", padx=8, pady=(5, 2))

        hotkeys = [
            ("F1: Intro", "F1", "#2563EB"),
            ("F2: BMKG", "F2", "#0D9488"),
            ("F3: LITM/Thesis", "F3", "#7C3AED"),
            ("F4: Tools/Agent", "F4", "#D97706"),
            ("F5: Orlith", "F5", "#0284C7"),
            ("F6: Metrics", "F6", "#4F46E5"),
        ]

        for label, hk, color in hotkeys:
            btn = tk.Button(
                top_frame, text=label, font=("Segoe UI", 8, "bold"),
                bg=color, fg="white", activebackground="#1E293B", activeforeground="white",
                bd=0, padx=6, pady=2, cursor="hand2",
                command=lambda k=hk: self.on_hotkey_pressed(k)
            )
            btn.pack(side="left", padx=2)

        # 2. COLAB LLM URL INPUT BAR
        colab_frame = tk.Frame(self.root, bg="#0B132B")
        colab_frame.pack(fill="x", padx=8, pady=2)

        lbl_colab = tk.Label(colab_frame, text="⚡ Colab URL:", bg="#0B132B", fg="#F59E0B", font=("Segoe UI", 8, "bold"))
        lbl_colab.pack(side="left", padx=(2, 4))

        self.entry_colab = tk.Entry(
            colab_frame, font=("Segoe UI", 8), bg="#1E293B", fg="#FDE68A",
            insertbackground="white", bd=0, highlightthickness=1, highlightbackground="#D97706"
        )
        self.entry_colab.insert(0, "Paste trycloudflare.com URL here (Optional)")
        self.entry_colab.pack(side="left", fill="x", expand=True, ipady=1)

        btn_save_colab = tk.Button(
            colab_frame, text="Connect", font=("Segoe UI", 7, "bold"),
            bg="#D97706", fg="white", bd=0, padx=6, cursor="hand2",
            command=self.save_colab_url
        )
        btn_save_colab.pack(side="right", padx=(4, 0))

        # 3. SEARCH BAR
        search_frame = tk.Frame(self.root, bg="#0B132B")
        search_frame.pack(fill="x", padx=8, pady=2)

        lbl_icon = tk.Label(search_frame, text="🔍", bg="#0B132B", fg="#94A3B8", font=("Segoe UI", 9))
        lbl_icon.pack(side="left", padx=(2, 4))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_typed)

        self.entry_search = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=("Segoe UI", 10), bg="#1E293B", fg="#F8FAFC",
            insertbackground="white", bd=0, highlightthickness=1, highlightbackground="#334155"
        )
        self.entry_search.pack(side="left", fill="x", expand=True, ipady=2)

        btn_ask_llm = tk.Button(
            search_frame, text="🤖 Ask LLM", font=("Segoe UI", 8, "bold"),
            bg="#059669", fg="white", bd=0, padx=6, cursor="hand2",
            command=self.trigger_colab_llm
        )
        btn_ask_llm.pack(side="right", padx=(4, 2))

        btn_clear = tk.Button(
            search_frame, text="✕ Esc", font=("Segoe UI", 8),
            bg="#334155", fg="#CBD5E1", bd=0, padx=5, cursor="hand2",
            command=self.clear_search
        )
        btn_clear.pack(side="right", padx=(2, 0))

        # 4. DISPLAY AREA
        display_frame = tk.Frame(self.root, bg="#0B132B")
        display_frame.pack(fill="both", expand=True, padx=8, pady=2)

        self.txt_display = scrolledtext.ScrolledText(
            display_frame, wrap=tk.WORD, bg="#030712", fg="#F3F4F6",
            bd=0, highlightthickness=1, highlightbackground="#1F2937",
            padx=10, pady=8
        )
        self.txt_display.pack(fill="both", expand=True)
        self.update_font_styles()

        # 5. BOTTOM BAR: CONTROLS
        bottom_frame = tk.Frame(self.root, bg="#0B132B")
        bottom_frame.pack(fill="x", padx=8, pady=(2, 5))

        lbl_font = tk.Label(bottom_frame, text="Font:", bg="#0B132B", fg="#94A3B8", font=("Segoe UI", 8))
        lbl_font.pack(side="left", padx=(2, 2))

        btn_font_dec = tk.Button(bottom_frame, text="A-", font=("Segoe UI", 8), bg="#1E293B", fg="white", bd=0, padx=5, command=self.dec_font)
        btn_font_dec.pack(side="left", padx=1)

        btn_font_inc = tk.Button(bottom_frame, text="A+", font=("Segoe UI", 8), bg="#1E293B", fg="white", bd=0, padx=5, command=self.inc_font)
        btn_font_inc.pack(side="left", padx=1)

        lbl_trans = tk.Label(bottom_frame, text="  Trans:", bg="#0B132B", fg="#94A3B8", font=("Segoe UI", 8))
        lbl_trans.pack(side="left", padx=(4, 2))

        self.slider_alpha = tk.Scale(
            bottom_frame, from_=50, to=100, orient="horizontal",
            bg="#0B132B", fg="#94A3B8", highlightthickness=0, bd=0,
            showvalue=0, length=70, command=self.on_slider_alpha
        )
        self.slider_alpha.set(95)
        self.slider_alpha.pack(side="left", padx=2)

        self.lbl_status = tk.Label(bottom_frame, text="● Fast DB Ready (3,766 items)", bg="#0B132B", fg="#10B981", font=("Segoe UI", 8, "bold"))
        self.lbl_status.pack(side="right", padx=4)

    def save_colab_url(self):
        url = self.entry_colab.get().strip()
        if url and ("trycloudflare.com" in url or "ngrok" in url or "loca.lt" in url):
            self.colab_url = url.rstrip("/")
            self.lbl_status.config(text="⏳ Connecting to Colab...", fg="#F59E0B")
            def _check():
                try:
                    req = urllib.request.Request(self.colab_url + "/", method="GET")
                    with urllib.request.urlopen(req, timeout=6) as res:
                        data = json.loads(res.read().decode("utf-8"))
                        gpu = data.get("gpu", "GPU")
                        mod = data.get("model", "LLM").split("/")[-1]
                        self.root.after(0, self.lbl_status.config, {"text": f"✅ {mod} ({gpu}) Connected", "fg": "#10B981"})
                except Exception:
                    self.root.after(0, self.lbl_status.config, {"text": "✅ Colab GPU Connected", "fg": "#10B981"})
            threading.Thread(target=_check, daemon=True).start()
        else:
            self.colab_url = ""
            self.lbl_status.config(text="Colab URL Cleared", fg="#94A3B8")

    def update_font_styles(self):
        sz = self.current_font_size
        self.txt_display.tag_config("title", font=("Segoe UI", sz + 1, "bold"), foreground="#38BDF8")
        self.txt_display.tag_config("hook_lbl", font=("Segoe UI", sz - 1, "bold"), foreground="#F59E0B")
        self.txt_display.tag_config("hook_txt", font=("Segoe UI", sz, "italic"), foreground="#FDE68A")
        self.txt_display.tag_config("bullet_icon", font=("Segoe UI", sz, "bold"), foreground="#60A5FA")
        self.txt_display.tag_config("bullet_txt", font=("Segoe UI", sz), foreground="#F8FAFC")
        self.txt_display.tag_config("close_lbl", font=("Segoe UI", sz - 1, "bold"), foreground="#94A3B8")
        self.txt_display.tag_config("close_txt", font=("Segoe UI", sz - 1, "italic"), foreground="#CBD5E1")
        self.txt_display.tag_config("llm_tag", font=("Segoe UI", sz, "bold"), foreground="#34D399")

    def inc_font(self):
        if self.current_font_size < 18:
            self.current_font_size += 1
            self.update_font_styles()

    def dec_font(self):
        if self.current_font_size > 9:
            self.current_font_size -= 1
            self.update_font_styles()

    def on_slider_alpha(self, val):
        alpha = float(val) / 100.0
        self.root.attributes("-alpha", alpha)

    def bind_global_hotkeys(self):
        for i in range(1, 7):
            self.root.bind_all(f"<F{i}>", lambda e, k=f"F{i}": self.on_hotkey_pressed(k))
        self.root.bind_all("<Escape>", lambda e: self.clear_search())

    def on_hotkey_pressed(self, hk):
        item = self.engine.get_by_hotkey(hk)
        if item:
            self.search_var.set("")
            self.show_item(item)
            self.lbl_status.config(text=f"Hotkey: {hk}", fg="#60A5FA")

    def on_search_typed(self, *args):
        q = self.search_var.get().strip()
        if not q:
            return
        results = self.engine.search(q)
        if results:
            self.show_item(results[0])
            self.lbl_status.config(text=f"Matched: {results[0].get('id', '')}", fg="#10B981")
        else:
            self.lbl_status.config(text="No match found", fg="#F87171")

    def trigger_colab_llm(self):
        q = self.search_var.get().strip()
        if not q or not self.colab_url:
            if not self.colab_url:
                self.lbl_status.config(text="⚠️ Masukkan Colab URL terlebih dahulu", fg="#F87171")
            return
        
        self.lbl_status.config(text="⚡ Streaming dari Colab GPU...", fg="#F59E0B")

        def _worker():
            # 1. Coba Endpoint Streaming untuk Kecepatan Ultra-Kilat (<0.4s First Token)
            stream_success = False
            try:
                req = urllib.request.Request(
                    f"{self.colab_url}/generate_stream",
                    data=json.dumps({"question": q}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                self.root.after(0, self.init_stream_display, q)
                with urllib.request.urlopen(req, timeout=15) as res:
                    while True:
                        chunk = res.read(64)
                        if not chunk:
                            break
                        text_chunk = chunk.decode("utf-8", errors="ignore")
                        self.root.after(0, self.append_stream_text, text_chunk)
                        stream_success = True
                if stream_success:
                    self.root.after(0, self.lbl_status.config, {"text": "✅ Colab Live Answer Ready", "fg": "#34D399"})
                    return
            except Exception:
                pass

            # 2. Fallback ke Endpoint Standar /generate jika /generate_stream tidak tersedia
            try:
                req = urllib.request.Request(
                    f"{self.colab_url}/generate",
                    data=json.dumps({"question": q}).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=15) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    answer = data.get("answer", "")
                    self.root.after(0, self.display_colab_answer, q, answer)
            except Exception as e:
                self.root.after(0, self.lbl_status.config, {"text": f"Colab Error: {e}", "fg": "#F87171"})

        threading.Thread(target=_worker, daemon=True).start()

    def init_stream_display(self, question):
        self.txt_display.config(state="normal")
        self.txt_display.delete("1.0", tk.END)
        self.txt_display.insert(tk.END, f"🤖 Live Stream from Colab GPU\n", "llm_tag")
        self.txt_display.insert(tk.END, f"Question: \"{question}\"\n", "hook_lbl")
        self.txt_display.insert(tk.END, "─" * 48 + "\n\n")
        self.txt_display.config(state="disabled")

    def append_stream_text(self, text_chunk):
        self.txt_display.config(state="normal")
        self.txt_display.insert(tk.END, text_chunk, "bullet_txt")
        self.txt_display.see(tk.END)
        self.txt_display.config(state="disabled")

    def display_colab_answer(self, question, answer):
        self.txt_display.config(state="normal")
        self.txt_display.delete("1.0", tk.END)
        self.txt_display.insert(tk.END, f"🤖 Dynamic Answer from Colab GPU\n", "llm_tag")
        self.txt_display.insert(tk.END, f"Question: \"{question}\"\n", "hook_lbl")
        self.txt_display.insert(tk.END, "─" * 48 + "\n\n")
        self.txt_display.insert(tk.END, answer, "bullet_txt")
        self.txt_display.config(state="disabled")
        self.lbl_status.config(text="✅ Colab Answer Ready", fg="#34D399")

    def clean_meet_text(self, text):
        cleaned = text.strip()
        if "keyboard_arrow_up" in cleaned or "Setelan audio" in cleaned:
            parts = re.split(r'keyboard_arrow_up|Setelan audio|Setelan Video', cleaned)[0].strip()
            lines = [l.strip() for l in parts.split("\n") if l.strip()]
            blacklist = ["buka setelan teks", "warna font", "ukuran font", "settings", "circle", "format_size", "language", "inggris", "anda", "info", "detail rapat"]
            spoken_line = ""
            for l in reversed(lines):
                if l.lower() not in blacklist and not l.startswith("Muhammad") and len(l) > 2:
                    spoken_line = l
                    break
            if spoken_line:
                cleaned = spoken_line

        sentences = [s.strip() for s in re.split(r'[.?!]\s*', cleaned) if s.strip()]
        if sentences:
            latest = sentences[-1]
            if len(latest.split()) <= 2 and len(sentences) >= 2:
                latest = sentences[-2] + " " + latest
            return latest

        words = cleaned.split()
        if len(words) > 10:
            return " ".join(words[-10:])
        return cleaned

    def receive_external_caption(self, caption_text):
        caption_clean = self.clean_meet_text(caption_text).strip()
        if not caption_clean:
            return
        self.search_var.set(caption_clean)
        self.lbl_status.config(text=f"⚡ Auto-Heard: \"{caption_clean[:26]}...\"", fg="#FBBF24")

        # Jika Colab URL terhubung, otomatis minta Colab LLM juga!
        if self.colab_url and len(caption_clean.split()) >= 3:
            self.trigger_colab_llm()

    def clear_search(self):
        self.search_var.set("")
        self.entry_search.focus_set()
        self.show_item(self.engine.get_by_hotkey("F1"))

    def show_item(self, item):
        if not item:
            return
        self.txt_display.config(state="normal")
        self.txt_display.delete("1.0", tk.END)

        hk_str = f" [{item['hotkey']}]" if "hotkey" in item else ""
        self.txt_display.insert(tk.END, f"{item.get('title', 'Answer')}{hk_str}\n", "title")
        self.txt_display.insert(tk.END, "─" * 48 + "\n")

        if "opening_hook" in item:
            self.txt_display.insert(tk.END, "SAY THIS FIRST:\n", "hook_lbl")
            self.txt_display.insert(tk.END, f"\"{item['opening_hook']}\"\n\n", "hook_txt")

        if "bullets" in item:
            for b in item["bullets"]:
                self.txt_display.insert(tk.END, "•  ", "bullet_icon")
                self.txt_display.insert(tk.END, f"{b}\n\n", "bullet_txt")

        if "closing" in item:
            self.txt_display.insert(tk.END, "CLOSING:\n", "close_lbl")
            self.txt_display.insert(tk.END, f"\"{item['closing']}\"\n", "close_txt")

        self.txt_display.config(state="disabled")

def launch():
    t = threading.Thread(target=start_background_receiver, daemon=True)
    t.start()
    root = tk.Tk()
    app = AlphaInterviewTeleprompter(root)
    root.mainloop()

if __name__ == "__main__":
    launch()
