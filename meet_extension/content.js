/**
 * ⚡ Alpha Global Meeting Copilot Connector (Multi-Platform)
 * Mendukung otomatisasi subtitle dari:
 * 1. Google Meet (meet.google.com)
 * 2. Zoom Web Client (*.zoom.us)
 * 3. Microsoft Teams (teams.microsoft.com & teams.live.com)
 * 4. Cisco Webex (*.webex.com)
 */

(function () {
  const currentHost = window.location.hostname;
  let platformName = "Meeting";

  if (currentHost.includes("meet.google.com")) platformName = "Google Meet";
  else if (currentHost.includes("zoom.us")) platformName = "Zoom Web";
  else if (currentHost.includes("teams.microsoft") || currentHost.includes("teams.live")) platformName = "MS Teams";
  else if (currentHost.includes("webex.com")) platformName = "Webex";

  console.log(`⚡ [Alpha Global Copilot] Active on ${platformName} (${currentHost})`);

  if (window._alphaMeetObserver) {
    try { window._alphaMeetObserver.disconnect(); } catch(e){}
  }

  let lastSentText = "";
  let debounceTimer = null;
  const COPILOT_ENDPOINT = "http://localhost:8765/api/caption";

  function sendToCopilot(text) {
    if (!text || text.length < 3 || text === lastSentText) return;
    lastSentText = text;
    console.log(`🚀 [Alpha Copilot - ${platformName}] Terkirim:`, text);

    fetch(COPILOT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text })
    }).catch(err => {
      // Teleprompter offline warning
    });
  }

  function extractCleanSpeech() {
    // ==========================================
    // 1. ZOOM WEB CLIENT
    // ==========================================
    if (currentHost.includes("zoom.us")) {
      const zoomNodes = document.querySelectorAll(
        '.closed-caption-window, [class*="closed-caption"], [class*="caption-text"], [aria-label*="caption" i]'
      );
      if (zoomNodes.length > 0) {
        for (let i = zoomNodes.length - 1; i >= 0; i--) {
          const txt = (zoomNodes[i].innerText || "").trim();
          if (txt.length > 2 && txt.length < 400) {
            return isolateLatestSentence(txt);
          }
        }
      }
    }

    // ==========================================
    // 2. MICROSOFT TEAMS
    // ==========================================
    if (currentHost.includes("teams.microsoft") || currentHost.includes("teams.live")) {
      const teamsNodes = document.querySelectorAll(
        '[data-tid*="closed-captions"], [class*="closed-caption"], [aria-label*="closed caption" i], .ui-chat__item__message'
      );
      if (teamsNodes.length > 0) {
        for (let i = teamsNodes.length - 1; i >= 0; i--) {
          const txt = (teamsNodes[i].innerText || "").trim();
          if (txt.length > 2 && txt.length < 400) {
            return isolateLatestSentence(txt);
          }
        }
      }
    }

    // ==========================================
    // 3. GOOGLE MEET
    // ==========================================
    const meetNodes = document.querySelectorAll('div[jsname="YSxPC"], span[jsname="YSxPC"]');
    if (meetNodes.length > 0) {
      const lastNode = meetNodes[meetNodes.length - 1];
      if (lastNode && lastNode.innerText && lastNode.innerText.trim().length > 2) {
        return isolateLatestSentence(lastNode.innerText.trim());
      }
    }

    // Google Meet Toolbar Fallback
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

    // ==========================================
    // 4. GENERIC WEB ACCESSIBILITY / ARIA FALLBACK
    // ==========================================
    const genericNodes = document.querySelectorAll('[aria-live="polite"], [role="region"][aria-label*="caption" i]');
    if (genericNodes.length > 0) {
      for (let i = genericNodes.length - 1; i >= 0; i--) {
        const txt = (genericNodes[i].innerText || "").trim();
        if (txt.length > 3 && txt.length < 300) {
          return isolateLatestSentence(txt);
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

  // Tampilkan badge koneksi multi-platform
  let oldBadge = document.getElementById("alpha-copilot-badge");
  if (oldBadge) oldBadge.remove();

  const badge = document.createElement("div");
  badge.id = "alpha-copilot-badge";
  badge.textContent = `⚡ Alpha Copilot: ${platformName.toUpperCase()} CONNECTED`;
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
  setTimeout(() => { badge.style.opacity = "0.5"; }, 4000);
})();
