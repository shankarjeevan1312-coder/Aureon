document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const backendBadge = document.getElementById("backend-badge");
  const cpuStat = document.getElementById("cpu-stat");
  const ramStat = document.getElementById("ram-stat");
  const netStat = document.getElementById("net-stat");
  const orbModeBadge = document.getElementById("orb-mode-badge");
  const audioToggleBtn = document.getElementById("audio-toggle-btn");
  const messagesContainer = document.getElementById("messages-container");
  const chatForm = document.getElementById("chat-form");
  const textInput = document.getElementById("text-input");
  const micBtn = document.getElementById("mic-btn");
  const voiceStatus = document.getElementById("voice-status");
  const memoryBtn = document.getElementById("memory-btn");
  const memoryModal = document.getElementById("memory-modal");
  const closeMemoryBtn = document.getElementById("close-memory-btn");
  const memoryProfile = document.getElementById("memory-profile");
  const memoryLedger = document.getElementById("memory-ledger");

  // Destructive Confirmation Modal
  const confirmModal = document.getElementById("confirm-modal");
  const confirmText = document.getElementById("confirm-text");
  const confirmDetails = document.getElementById("confirm-details");
  const confirmActionBtn = document.getElementById("confirm-action-btn");
  const denyActionBtn = document.getElementById("deny-action-btn");

  let pendingAction = null;
  let isListening = false;
  let isSpeaking = false;
  let isProcessing = false;
  let recognition = null;
  let socket = null;
  let audioPlayer = new Audio();

  // Register Service Worker for PWA
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch((err) => {
      console.log("ServiceWorker registration skipped: ", err);
    });
  }

  // Audio FX Toggle
  let audioFxEnabled = true;
  audioToggleBtn.addEventListener("click", () => {
    audioFxEnabled = !audioFxEnabled;
    window.aureonSounds.enabled = audioFxEnabled;
    audioToggleBtn.textContent = audioFxEnabled ? "🔊 FX: ON" : "🔇 FX: OFF";
    if (audioFxEnabled) window.aureonSounds.playClick();
  });

  // Quick Action Buttons
  document.querySelectorAll(".quick-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      if (query) {
        if (window.aureonSounds) window.aureonSounds.playClick();
        handleUserSubmit(query);
      }
    });
  });

  // Visualizer Setup with 4 States: IDLE, LISTENING, PROCESSING, SPEAKING
  const canvas = document.getElementById("visualizer");
  const ctx = canvas.getContext("2d");
  let pulsePhase = 0;

  function updateOrbBadge() {
    if (isListening) {
      orbModeBadge.textContent = "LISTENING";
      orbModeBadge.style.color = "var(--red-glow)";
      orbModeBadge.style.borderColor = "var(--red-glow)";
    } else if (isProcessing) {
      orbModeBadge.textContent = "PROCESSING";
      orbModeBadge.style.color = "var(--amber-glow)";
      orbModeBadge.style.borderColor = "var(--amber-glow)";
    } else if (isSpeaking) {
      orbModeBadge.textContent = "SPEAKING";
      orbModeBadge.style.color = "var(--cyan-glow)";
      orbModeBadge.style.borderColor = "var(--cyan-glow)";
    } else {
      orbModeBadge.textContent = "SYSTEM READY";
      orbModeBadge.style.color = "var(--cyan-dim)";
      orbModeBadge.style.borderColor = "var(--border-glow)";
    }
  }

  function drawOrb() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const baseRadius = 78;

    let speed = 0.03;
    let amplitude = 6;
    let primaryColor = "rgba(0, 240, 255, ";

    if (isListening) {
      speed = 0.09;
      amplitude = 18;
      primaryColor = "rgba(255, 51, 68, ";
    } else if (isProcessing) {
      speed = 0.12;
      amplitude = 12;
      primaryColor = "rgba(255, 184, 0, ";
    } else if (isSpeaking) {
      speed = 0.07;
      amplitude = 14;
      primaryColor = "rgba(0, 240, 255, ";
    }

    pulsePhase += speed;
    const dynamicRadius = baseRadius + Math.sin(pulsePhase) * amplitude;

    // Glowing outer rings
    for (let i = 3; i > 0; i--) {
      ctx.beginPath();
      ctx.arc(centerX, centerY, dynamicRadius + i * 22, 0, Math.PI * 2);
      ctx.strokeStyle = `${primaryColor}${0.12 * i})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }

    // Inner glowing core
    const gradient = ctx.createRadialGradient(centerX, centerY, 8, centerX, centerY, dynamicRadius);
    gradient.addColorStop(0, `${primaryColor}0.9)`);
    gradient.addColorStop(0.6, `${primaryColor}0.25)`);
    gradient.addColorStop(1, `${primaryColor}0)`);

    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(centerX, centerY, dynamicRadius, 0, Math.PI * 2);
    ctx.fill();

    updateOrbBadge();
    requestAnimationFrame(drawOrb);
  }
  drawOrb();

  // Initialize Speech Recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add("listening");
      voiceStatus.textContent = "LISTENING...";
      if (window.aureonSounds) window.aureonSounds.playWake();
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      voiceStatus.textContent = "TRANSCRIBED: " + transcript;
      handleUserSubmit(transcript);
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      stopListening();
    };

    recognition.onend = () => {
      stopListening();
    };
  } else {
    voiceStatus.textContent = "SPEECH API NOT SUPPORTED IN THIS BROWSER (USE TEXT)";
  }

  function toggleListening() {
    if (!recognition) return;
    if (isListening) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (e) {
        console.warn(e);
      }
    }
  }

  function stopListening() {
    isListening = false;
    micBtn.classList.remove("listening");
    voiceStatus.textContent = "CLICK MIC TO SPEAK";
  }

  micBtn.addEventListener("click", toggleListening);

  // WebSocket Connection
  function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      backendBadge.textContent = "CONNECTED";
      backendBadge.style.color = "var(--cyan-glow)";
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "telemetry") {
        cpuStat.textContent = `${data.data.cpu}%`;
        ramStat.textContent = `${data.data.ram}%`;
      } else if (data.type === "response") {
        renderResponse(data.payload);
      }
    };

    socket.onclose = () => {
      backendBadge.textContent = "OFFLINE";
      backendBadge.style.color = "var(--red-glow)";
      setTimeout(connectWebSocket, 3000);
    };
  }
  connectWebSocket();

  // Submit User Message
  function handleUserSubmit(message) {
    if (!message || !message.trim()) return;
    appendMessage("USER", message, "user");
    textInput.value = "";
    isProcessing = true;

    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message })
    })
      .then((res) => res.json())
      .then((data) => {
        isProcessing = false;
        renderResponse(data);
      })
      .catch((err) => {
        isProcessing = false;
        appendMessage("ERROR", "Failed to reach AUREON backend: " + err, "assistant");
      });
  }

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    if (window.aureonSounds) window.aureonSounds.playClick();
    handleUserSubmit(textInput.value);
  });

  // Render Response and Play Speech
  function renderResponse(payload) {
    appendMessage("AUREON CORE", payload.text, "assistant");

    if (payload.backend_used) {
      backendBadge.textContent = payload.backend_used.toUpperCase();
    }

    // Check if a tool returned a screenshot image URL
    if (payload.tool_results && payload.tool_results.length > 0) {
      payload.tool_results.forEach((tool) => {
        if (tool.tool_name === "capture_screenshot" && tool.output && tool.output.url) {
          appendImage(tool.output.url);
        }
      });
    }

    // Handle Destructive Action Confirmation
    if (payload.pending_confirmation) {
      pendingAction = payload.pending_confirmation;
      confirmText.textContent = payload.pending_confirmation.prompt;
      confirmDetails.textContent = JSON.stringify(payload.pending_confirmation.args, null, 2);
      confirmModal.classList.remove("hidden");
      if (window.aureonSounds) window.aureonSounds.playAlert();
    } else {
      if (window.aureonSounds) window.aureonSounds.playComplete();
    }

    // Play synthesized voice if available
    if (payload.voice_text) {
      playVoice(payload.voice_text);
    }
  }

  function playVoice(text) {
    const encoded = encodeURIComponent(text);
    audioPlayer.src = `/api/tts?text=${encoded}`;
    isSpeaking = true;

    audioPlayer.onended = () => {
      isSpeaking = false;
    };
    audioPlayer.onerror = () => {
      isSpeaking = false;
    };

    audioPlayer.play().catch((e) => {
      isSpeaking = false;
      console.warn("Audio autoplay blocked by browser policy; click anywhere to enable audio.", e);
    });
  }

  function appendMessage(sender, content, type) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${type}`;

    const tag = document.createElement("div");
    tag.className = "sender-tag";
    tag.textContent = sender;

    const body = document.createElement("div");
    body.className = "message-content";
    body.textContent = content;

    msgDiv.appendChild(tag);
    msgDiv.appendChild(body);
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function appendImage(url) {
    const imgContainer = document.createElement("div");
    imgContainer.className = "message assistant";
    imgContainer.innerHTML = `
      <div class="sender-tag">SCREENSHOT CAPTURE</div>
      <a href="${url}" target="_blank">
        <img src="${url}" alt="Screenshot" style="max-width:100%; border-radius:6px; border:1px solid var(--border-glow); margin-top:0.4rem;" />
      </a>
    `;
    messagesContainer.appendChild(imgContainer);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  // Confirmation Handlers
  confirmActionBtn.addEventListener("click", () => {
    if (!pendingAction) return;
    confirmModal.classList.add("hidden");
    if (window.aureonSounds) window.aureonSounds.playClick();

    fetch("/api/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmed: true, action: pendingAction })
    })
      .then((res) => res.json())
      .then((data) => renderResponse(data));
    pendingAction = null;
  });

  denyActionBtn.addEventListener("click", () => {
    confirmModal.classList.add("hidden");
    if (window.aureonSounds) window.aureonSounds.playClick();
    if (!pendingAction) return;

    fetch("/api/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmed: false, action: pendingAction })
    })
      .then((res) => res.json())
      .then((data) => renderResponse(data));
    pendingAction = null;
  });

  // Memory Ledger Modal Handlers
  memoryBtn.addEventListener("click", () => {
    if (window.aureonSounds) window.aureonSounds.playClick();
    fetch("/api/memory")
      .then((res) => res.json())
      .then((data) => {
        memoryProfile.textContent = JSON.stringify(data.profile, null, 2);
        memoryLedger.textContent = data.ledger;
        memoryModal.classList.remove("hidden");
      });
  });

  closeMemoryBtn.addEventListener("click", () => {
    if (window.aureonSounds) window.aureonSounds.playClick();
    memoryModal.classList.add("hidden");
  });
});
