document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const backendBadge = document.getElementById("backend-badge");
  const cpuStat = document.getElementById("cpu-stat");
  const ramStat = document.getElementById("ram-stat");
  const orbModeBadge = document.getElementById("orb-mode-badge");
  const audioToggleBtn = document.getElementById("audio-toggle-btn");
  const voiceModeBtn = document.getElementById("voice-mode-btn");
  const stopSpeechBtn = document.getElementById("stop-speech-btn");
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
  let silenceTimer = null;
  let currentTranscript = "";

  // Voice Modes: "instant" (Web Speech API, 0s delay) vs "neural" (Edge-TTS via server)
  let voiceMode = "instant";

  // Register Service Worker for PWA
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  }

  // Audio FX Toggle
  let audioFxEnabled = true;
  audioToggleBtn.addEventListener("click", () => {
    audioFxEnabled = !audioFxEnabled;
    window.aureonSounds.enabled = audioFxEnabled;
    audioToggleBtn.textContent = audioFxEnabled ? "🔊 FX: ON" : "🔇 FX: OFF";
    if (audioFxEnabled) window.aureonSounds.playClick();
  });

  // Voice Mode Toggle
  voiceModeBtn.addEventListener("click", () => {
    if (voiceMode === "instant") {
      voiceMode = "neural";
      voiceModeBtn.textContent = "🎙️ NEURAL TTS";
    } else {
      voiceMode = "instant";
      voiceModeBtn.textContent = "⚡ INSTANT VOICE";
    }
    stopAnySpeaking();
    if (window.aureonSounds) window.aureonSounds.playClick();
  });

  // Instant Audio Stop Function
  function stopAnySpeaking() {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    if (audioPlayer) {
      audioPlayer.pause();
      audioPlayer.currentTime = 0;
      audioPlayer.src = "";
    }
    isSpeaking = false;
    updateOrbBadge();
  }

  stopSpeechBtn.addEventListener("click", () => {
    stopAnySpeaking();
    if (window.aureonSounds) window.aureonSounds.playClick();
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
      orbModeBadge.textContent = "LISTENING...";
      orbModeBadge.style.color = "var(--red-glow)";
      orbModeBadge.style.borderColor = "var(--red-glow)";
    } else if (isProcessing) {
      orbModeBadge.textContent = "PROCESSING...";
      orbModeBadge.style.color = "var(--amber-glow)";
      orbModeBadge.style.borderColor = "var(--amber-glow)";
    } else if (isSpeaking) {
      orbModeBadge.textContent = "SPEAKING...";
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
      speed = 0.07;
      amplitude = 12;
      primaryColor = "rgba(255, 170, 0, ";
    } else if (isSpeaking) {
      speed = 0.08;
      amplitude = 22;
      primaryColor = "rgba(0, 255, 204, ";
    }

    pulsePhase += speed;

    for (let r = 0; r < 3; r++) {
      const ringRadius = baseRadius + r * 22 + Math.sin(pulsePhase + r) * amplitude;
      ctx.beginPath();
      ctx.arc(centerX, centerY, Math.max(ringRadius, 10), 0, Math.PI * 2);
      ctx.strokeStyle = `${primaryColor}${0.75 - r * 0.22})`;
      ctx.lineWidth = 2.2 - r * 0.5;
      ctx.shadowBlur = 14;
      ctx.shadowColor = `${primaryColor}0.9)`;
      ctx.stroke();
    }

    // Core
    ctx.beginPath();
    ctx.arc(centerX, centerY, 38 + Math.sin(pulsePhase * 1.5) * 4, 0, Math.PI * 2);
    ctx.fillStyle = `${primaryColor}0.25)`;
    ctx.fill();

    updateOrbBadge();
    requestAnimationFrame(drawOrb);
  }
  drawOrb();

  // Speech Recognition Setup
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;       // Don't close immediately on brief pause!
    recognition.interimResults = true;    // Show words in real-time as user speaks
    recognition.lang = "en-US";

    recognition.onstart = () => {
      stopAnySpeaking();
      isListening = true;
      currentTranscript = "";
      micBtn.classList.add("listening");
      voiceStatus.textContent = "LISTENING... (SPEAK NOW)";
      voiceStatus.style.color = "var(--red-glow)";
    };

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          currentTranscript += event.results[i][0].transcript;
        } else {
          interim += event.results[i][0].transcript;
        }
      }

      const activeText = (currentTranscript + " " + interim).trim();
      if (activeText) {
        voiceStatus.textContent = `🗣️ "${activeText}"`;
        voiceStatus.style.color = "var(--cyan-glow)";

        // Debounce submit after 1.5s of silence
        clearTimeout(silenceTimer);
        silenceTimer = setTimeout(() => {
          if (isListening && activeText) {
            stopListening();
            handleUserSubmit(activeText);
          }
        }, 1500);
      }
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition error:", event.error);
      clearTimeout(silenceTimer);

      if (event.error === "not-allowed") {
        voiceStatus.textContent = "⚠️ MIC BLOCKED: Allow mic access in browser address bar.";
        voiceStatus.style.color = "var(--red-glow)";
      } else if (event.error === "network") {
        voiceStatus.textContent = "⚠️ BRAVE NOTICE: In brave://settings/privacy, enable Google Speech or use Chrome/Edge.";
        voiceStatus.style.color = "var(--amber-glow)";
      } else if (event.error !== "no-speech") {
        voiceStatus.textContent = `VOICE ERROR: ${event.error.toUpperCase()}`;
      }

      if (event.error !== "no-speech") {
        stopListening();
      }
    };

    recognition.onend = () => {
      clearTimeout(silenceTimer);
      if (isListening) {
        if (currentTranscript.trim()) {
          handleUserSubmit(currentTranscript.trim());
        }
        stopListening();
      }
    };
  } else {
    voiceStatus.textContent = "SPEECH API NOT SUPPORTED IN THIS BROWSER";
  }

  function startListening() {
    if (!recognition) {
      alert("Speech recognition not supported in this browser. Please use Chrome, Edge, or type in the box.");
      return;
    }
    stopAnySpeaking();
    try {
      recognition.start();
    } catch (e) {
      console.warn("Recognition already started or busy:", e);
    }
  }

  function stopListening() {
    isListening = false;
    clearTimeout(silenceTimer);
    micBtn.classList.remove("listening");
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }
    setTimeout(() => {
      if (!isListening && !isProcessing && !isSpeaking) {
        voiceStatus.textContent = "CLICK MIC TO SPEAK";
        voiceStatus.style.color = "var(--cyan-dim)";
      }
    }, 2000);
  }

  function toggleListening() {
    if (isListening) {
      if (currentTranscript.trim()) {
        const textToSubmit = currentTranscript.trim();
        stopListening();
        handleUserSubmit(textToSubmit);
      } else {
        stopListening();
      }
    } else {
      startListening();
    }
  }

  micBtn.addEventListener("click", toggleListening);

  // Push-to-Talk via Spacebar (when not typing in the text box)
  let spacePressed = false;
  window.addEventListener("keydown", (e) => {
    if (e.code === "Escape") {
      stopAnySpeaking();
      stopListening();
      return;
    }

    if (e.code === "Space" && document.activeElement !== textInput && !spacePressed) {
      spacePressed = true;
      e.preventDefault();
      startListening();
    }
  });

  window.addEventListener("keyup", (e) => {
    if (e.code === "Space" && spacePressed) {
      spacePressed = false;
      e.preventDefault();
      setTimeout(() => {
        if (isListening) {
          if (currentTranscript.trim()) {
            handleUserSubmit(currentTranscript.trim());
          }
          stopListening();
        }
      }, 500);
    }
  });

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
    stopAnySpeaking();

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

    // Process Tool Results
    if (payload.tool_results && payload.tool_results.length > 0) {
      payload.tool_results.forEach((tool) => {
        // Screenshot rendering
        if (tool.tool_name === "capture_screenshot" && tool.output && tool.output.url) {
          appendImage(tool.output.url);
        }

        // Automatic URL Tab Launching
        let targetUrl = null;
        if (tool.output && typeof tool.output === "object" && tool.output.url) {
          targetUrl = tool.output.url;
        } else if (typeof tool.output === "string") {
          const match = tool.output.match(/https?:\/\/[^\s\)]+/);
          if (match) targetUrl = match[0];
        }

        if (targetUrl) {
          try {
            window.open(targetUrl, "_blank");
          } catch (e) {
            console.warn("Browser blocked popup:", e);
          }
          appendUrlButton(targetUrl);
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

    // Play synthesized voice immediately
    if (payload.voice_text) {
      playVoice(payload.voice_text);
    }
  }

  // Voice Output (Instant Web Speech or Neural Edge-TTS)
  function playVoice(text) {
    stopAnySpeaking();

    if (!text || !text.trim()) return;

    if (voiceMode === "instant" && "speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;

      const voices = window.speechSynthesis.getVoices();
      const preferredVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("David") || v.name.includes("Guy")));
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      utterance.onstart = () => {
        isSpeaking = true;
        updateOrbBadge();
      };
      utterance.onend = () => {
        isSpeaking = false;
        updateOrbBadge();
      };
      utterance.onerror = () => {
        isSpeaking = false;
        updateOrbBadge();
      };

      window.speechSynthesis.speak(utterance);
    } else {
      const encoded = encodeURIComponent(text);
      audioPlayer.src = `/api/tts?text=${encoded}`;
      isSpeaking = true;
      updateOrbBadge();

      audioPlayer.onended = () => {
        isSpeaking = false;
        updateOrbBadge();
      };
      audioPlayer.onerror = () => {
        isSpeaking = false;
        updateOrbBadge();
      };

      audioPlayer.play().catch(() => {
        isSpeaking = false;
        updateOrbBadge();
      });
    }
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

  function appendUrlButton(url) {
    const btnDiv = document.createElement("div");
    btnDiv.className = "message assistant";
    btnDiv.innerHTML = `
      <div class="sender-tag">WEB ACCESS</div>
      <a href="${url}" target="_blank" style="display:inline-block; margin-top:0.4rem; padding:0.4rem 0.8rem; background:rgba(0,240,255,0.15); border:1px solid var(--cyan-glow); color:var(--cyan-glow); text-decoration:none; border-radius:4px; font-weight:600;">
        🔗 OPEN TAB: ${url}
      </a>
    `;
    messagesContainer.appendChild(btnDiv);
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
