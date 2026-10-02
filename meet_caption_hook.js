/**
 * ⚡ Alpha Meet Copilot Connector - Universal Line-Based Extractor
 */

(function () {
  console.log("⚡ [Alpha Meet Copilot] Active & Listening...");

  if (window._alphaMeetObserver) {
    try { window._alphaMeetObserver.disconnect(); } catch(e){}
  }

  let lastSentText = "";
  let debounceTimer = null;
  const COPILOT_ENDPOINT = "http://localhost:8765/api/caption";

  function sendToCopilot(text) {
    if (!text || text.length < 3 || text === lastSentText) return;
    lastSentText = text;
    console.log("🚀 [Alpha Meet Copilot] Spoken Sentence Sent:", text);

    fetch(COPILOT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    }).catch(err => {
      // Teleprompter offline warning
    });
  }

  function extractCleanSpeech() {
    // 1. Cari elemen teks ucapan langsung di Google Meet
    const captionNodes = document.querySelectorAll('div[jsname="YSxPC"], span[jsname="YSxPC"]');
    if (captionNodes.length > 0) {
      const lastNode = captionNodes[captionNodes.length - 1];
      if (lastNode && lastNode.innerText && lastNode.innerText.trim().length > 2) {
        return isolateLatestSentence(lastNode.innerText.trim());
      }
    }

    // 2. Ekstraktor Universal: Ambil baris teks tepat di atas toolbar Google Meet
    const allText = document.body.innerText || "";
    if (allText.includes("keyboard_arrow_up") || allText.includes("Setelan audio")) {
      const parts = allText.split(/keyboard_arrow_up|Setelan audio/)[0].trim();
      const lines = parts.split("\n").map(l => l.trim()).filter(l => l.length > 0);
      
      const blacklist = ["buka setelan teks", "warna font", "ukuran font", "settings", "circle", "format_size", "language", "inggris", "anda", "info", "detail rapat"];
      
      for (let i = lines.length - 1; i >= 0; i--) {
        const line = lines[i];
        if (!blacklist.includes(line.toLowerCase()) && !line.startsWith("Muhammad") && line.length > 2) {
          return isolateLatestSentence(line);
        }
      }
    }

    return null;
  }

  function isolateLatestSentence(raw) {
    const sentences = raw.split(/[.?!]\s*/).map(s => s.trim()).filter(s => s.length > 0);
    if (sentences.length > 0) {
      let latest = sentences[sentences.length - 1];
      if (latest.split(" ").length <= 2 && sentences.length >= 2) {
        latest = sentences[sentences.length - 2] + " " + latest;
      }
      return latest;
    }
    const words = raw.split(/\s+/);
    if (words.length > 10) {
      return words.slice(-10).join(" ");
    }
    return raw;
  }

  window._alphaMeetObserver = new MutationObserver(() => {
    const cleanSpeech = extractCleanSpeech();
    if (cleanSpeech && cleanSpeech !== lastSentText) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        sendToCopilot(cleanSpeech);
      }, 450);
    }
  });

  window._alphaMeetObserver.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true
  });

  let oldBadge = document.getElementById("alpha-copilot-badge");
  if (oldBadge) oldBadge.remove();

  const badge = document.createElement("div");
  badge.id = "alpha-copilot-badge";
  badge.textContent = "⚡ Alpha Copilot: ACTIVE";
  badge.style.cssText = `
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    background: #0284C7;
    color: white;
    padding: 5px 14px;
    border-radius: 16px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 11px;
    font-weight: bold;
    z-index: 999999;
    box-shadow: 0 4px 10px rgba(0,0,0,0.25);
    pointer-events: none;
    transition: opacity 0.5s ease;
  `;
  document.body.appendChild(badge);
  setTimeout(() => { badge.style.opacity = "0.5"; }, 3000);
})();
