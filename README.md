# 🚀 OpenFlow

<p align="center">
  <img src="resources/icon.png" width="128" style="border-radius:24px"/>
</p>

<p align="center">
  <b>A macOS-native, GPU-accelerated, streaming speech-to-text menu bar app.</b>
</p>

---

**OpenFlow** is an open-source, local-first alternative to Wispr Flow. It provides instant voice dictation into any application using Apple Silicon's Neural Engine (via MLX) for ultra-low latency transcription.

## ✨ Features

- **⚡️ Ultra-Low Latency**: Optimized for Apple Silicon using MLX (Metal) and `faster-whisper`.
- **🔒 Private & Local**: All processing happens on-device. No audio ever leaves your Mac.
- **🎙️ Voice-Reactive UI**: Beautiful, floating overlay that responds to your voice in real-time.
- **⌨️ Universal Dictation**: Inserts text directly into any active application via Accessibility APIs.
- **🔇 Smart Denoising**: Integrated RNNoise for crystal-clear audio capture even in noisy environments.
- **📦 Easy Installation**: Simple `brew` formula or manual setup.

## 📥 Installation

### Option 1: Homebrew (Mac)

Install directly from the repository:

```bash
# This installs the latest version from the main branch
brew install --HEAD https://raw.githubusercontent.com/sammy4321/OpenFlow/main/brew/openflow.rb
```

*Note: Once a stable release is tagged (v1.0.0), you can install without `--HEAD`.*

### Option 2: Manual Build

Requires Python 3.11+ and `portaudio`.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sammy4321/OpenFlow.git
   cd OpenFlow
   ```

2. **Run the installer:**
   ```bash
   # This script sets up a virtual environment, compiles dependencies, and downloads models.
   make install
   ```

3. **Run the app:**
   ```bash
   make run
   ```

## 🛠️ Usage

1. **Launch OpenFlow**. You'll see a small icon in your menu bar.
2. **Hold `Right Command` (cmd_r)** to start dictating.
   - An overlay will appear at the bottom of your screen.
   - Speak naturally.
3. **Release the key** to finish.
   - The text will be instantly transcribed and typed into your active window.

> **Note:** On first launch, you must grant **Accessibility Permissions** when prompted. This allows OpenFlow to type text on your behalf.

## ⚙️ Configuration

### Changing Models
By default, OpenFlow uses the `tiny` model for maximum speed (`<300ms`). You can switch to larger models for better accuracy:

```bash
# Run with a specific model size
openflow --model base
openflow --model small
openflow --model medium
```

Supported models: `tiny`, `base`, `small`, `medium`, `large-v3`.
_Functionality depends on your machine's memory._

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
