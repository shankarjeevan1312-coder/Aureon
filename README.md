# AUREON — Autonomous Local Voice & System Assistant
## Complete Production Application Suite

**AUREON** is an advanced autonomous voice-driven operating intelligence designed for desktop and mobile systems. Operating as your primary digital operator on Windows, AUREON executes system commands, manages communications, orchestrates complex workflows, and maintains persistent context while providing concise verbal communication.

---

## ⚡ Complete Feature Matrix

- **Dual-Tier LLM Intelligence**:
  - **Primary**: NVIDIA Nemotron API (`integrate.api.nvidia.com`), 40 RPM free tier with zero token exhaustion.
  - **Fallback**: Local Ollama (`mistral` / `llama3`) running locally on GPU/CPU.
  - **Offline Diagnostic**: Built-in deterministic intent router for zero-dependency offline use.
- **Deep Windows System & Hardware Tools (17 Integrated Tools)**:
  - `get_system_status`: Real-time CPU load, memory consumption, and disk statistics.
  - `get_battery_status`: Battery percentage, AC power connection, and estimated runtime.
  - `get_network_info`: Hostname, local IP, network adapter traffic (sent/received MB).
  - `volume_control`: Adjust or mute/unmute Windows master audio volume.
  - `capture_screenshot`: Capture high-resolution desktop screen, save to `data/screenshots/`, and display inline in the HUD.
  - `list_active_windows`: Inspect foreground open applications and window titles.
  - `clipboard_read` & `clipboard_write`: Read or populate the Windows clipboard.
  - `run_powershell`: Execute system shell commands with dangerous command token inspection.
  - `read_file` & `write_file`: Read or write local files.
  - `delete_file` & `kill_process`: Destructive actions guarded by interactive user approval modals.
  - `launch_app` & `open_url`: Launch desktop programs (Notepad, Code, Paint, Chrome, etc.) and search web.
  - `send_email` & `create_task_reminder`: Communication stubs and task reminders.
- **Autonomous Background Workflow Scheduler**:
  - `aureon/scheduler/task_scheduler.py`: Background interval runner monitoring `data/active_tasks.json`.
  - Automatically executes scheduled health checks, telemetry snapshots, and logs to `memory_ledger.md`.
- **Procedural Cybernetic Web Audio Synthesizer**:
  - `sounds.js`: Real-time synthesizer generating futuristic UI chimes (Wake, Completion, Red-Alert Klaxon, Click) with zero external MP3 assets.
- **Native Desktop & Mobile PWA Modes**:
  - **Desktop Window**: `run_desktop.bat` / `desktop.py` launches a borderless, dedicated application window without browser tabs.
  - **Mobile PWA**: `manifest.json` and `sw.js` allowing installation directly onto home screen on Android/iOS devices connecting over your Wi-Fi network.
- **Persistent Contextual Memory**:
  - Preconfigured for user **`revanthbarthu`** in `data/user_profile.json` and `data/memory_ledger.md`.
- **Standalone Windows Executable Builder**:
  - `build_exe.bat`: Compiles the entire system into a standalone `dist/Aureon/Aureon.exe` bundle.

---

## 🏗 Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│         NATIVE DESKTOP WINDOW / MOBILE PWA HUD          │
│  (Cybernetic UI, Web Audio Synth, Mic Speech, Telemetry)│
└──────────────────┬──────────────────────────────────────┘
                   │ (HTTP REST / WebSocket)
                   ▼
┌─────────────────────────────────────────────────────────┐
│              AUREON FASTAPI BACKEND                     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ AUREON ORCHESTRATOR                              │   │
│  │ - NVIDIA Nemotron & Local Ollama Router          │   │
│  │ - Safety Gatekeeper & Confirmation Quarantine   │   │
│  │ - Contextual Memory Manager                      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────┐  │
│  │ Task         │ │ Edge-TTS     │ │ 17 Native      │  │
│  │ Scheduler    │ │ Speech Synth │ │ System Tools   │  │
│  └──────────────┘ └──────────────┘ └────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Local Storage (data/)                            │   │
│  │ - user_profile.json                              │   │
│  │ - memory_ledger.md                               │   │
│  │ - active_tasks.json                              │   │
│  │ - screenshots/                                   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Launch Native Desktop Window
Double-click:
```cmd
run_desktop.bat
```
This opens AUREON in a sleek, borderless desktop application window.

### 2. Launch Web / Mobile Server
Or launch the server directly:
```cmd
run.bat
```
Access in your browser or from a mobile phone on the same Wi-Fi:
👉 **`http://localhost:8000`** (or `http://<your-pc-ip>:8000`)

### 3. Compile Standalone Windows Executable
To build a standalone `.exe`:
```cmd
build_exe.bat
```
The output executable will be placed in `dist/Aureon/Aureon.exe`.

---

## 🧪 Verification & Test Suite

To run the complete automated test suite across all 15 tests:
```powershell
cd C:\Users\barth\.gemini\antigravity\scratch\aureon
.\.venv\Scripts\python.exe -m pytest -v tests/
```
Output:
```text
======================= 15 passed in 12.17s =======================
```

---

## 🛡 Operating Protocols

1. **Brevity Rule**: Voice responses are kept under 3 sentences for natural, quick speech playback.
2. **Strict Safety Protocol**: Any destructive command (file deletion, process killing) immediately quarantines execution and opens an interactive confirmation dialogue.
3. **Continuous Memory**: Any statement starting with *"Remember that..."* is permanently indexed in `data/memory_ledger.md` and re-injected into future context.
