# PDF Narrator (Kokoro Edition)

**Updated for Kokoro v1.0!**  
Now setting up is easier—simply install the required Python dependencies (including the updated Kokoro package) and run the app. No more manual downloads or moving model files into specific folders.

PDF Narrator (Kokoro Edition) transforms your PDF documents into audiobooks effortlessly using **advanced text extraction** and **Kokoro TTS** technology. With Kokoro v1.0, the integration is seamless and the setup is as simple as installing the requirements and running the application.

---

## Demo

1. **Screenshot**  
   Check out the GUI in the screenshot below:  
   ![Demo Screenshot](assets/demo.png)

2. **Audio Sample**  
   Listen to a short sample of the generated audiobook:  
   [Audio Sample](https://github.com/user-attachments/assets/02953345-aceb-41f3-babf-1d1606c76641)

---

## Features

- **Intelligent PDF Text Extraction**

  - Skips headers, footers, and page numbers.
  - Optionally splits based on Table of Contents (TOC) or extracts the entire document.

- **Kokoro TTS Integration**

  - Generate natural-sounding audiobooks with the updated [Kokoro v1.0 model](https://huggingface.co/hexgrad/Kokoro-82M).
  - Easily select or swap out different `.pt` voicepacks.

- **User-Friendly GUI**

  - Modern interface built with **ttkbootstrap** (theme selector, scrolled logs, progress bars).
  - Pause/resume and cancel your audiobook generation anytime.

- **Configurable for Low-VRAM Systems**
  - Choose the chunk size for text to accommodate limited GPU resources.
  - Switch to CPU if no GPU is available.

---

## Prerequisites

- **Python 3.8+**
- **FFmpeg** (for audio-related tasks on some systems)
- **Torch** (PyTorch for the Kokoro TTS model)
- Other dependencies as listed in `requirements.txt`

---

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/mateogon/pdf-narrator.git
   cd pdf-narrator
   ```

2. **Create and Activate a Virtual Environment**

   ```bash
   python -m venv venv
   # On Linux/macOS:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install Python Dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install Kokoro v1.0**

   The updated Kokoro package is now available on PyPI. Simply install it:

   ```bash
   pip install kokoro>=1.0.0
   ```

5. **Install FFmpeg** (if required)

   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get install ffmpeg
     ```
   - **macOS**:
     ```bash
     brew install ffmpeg
     ```
   - **Windows**:  
     Download from the [FFmpeg official site](https://ffmpeg.org/download.html) and follow the installation instructions.

---

## Windows Additional Installation Notes

For Windows users, some libraries may require extra steps:

### 1. **Prerequisites**

- **Python 3.12.7**  
  Download and install [Python 3.12.7](https://www.python.org/downloads/). Ensure `python` and `pip` are added to your system's PATH.

- **CUDA 12.4** (for GPU acceleration)  
  Install the [CUDA 12.4 Toolkit](https://developer.nvidia.com/cuda-downloads) if you plan to use GPU acceleration.

### 2. **Installing eSpeak NG**

eSpeak NG is required for phoneme-based operations.

1. **Download the Installer**  
   [eSpeak NG X64 Installer](https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-X64.msi)

2. **Run the Installer**  
   Follow the on-screen instructions.

3. **Set Environment Variables**  
   Add the following environment variables:

   - `PHONEMIZER_ESPEAK_LIBRARY` → `C:\Program Files\eSpeak NG\libespeak-ng.dll`
   - `PHONEMIZER_ESPEAK_PATH` → `C:\Program Files (x86)\eSpeak\command_line\espeak.exe`

   (Right-click "This PC" → Properties → Advanced system settings → Environment Variables)

4. **Verify Installation**

   Open Command Prompt and run:

   ```cmd
   espeak-ng --version
   ```

### 3. **Using Precompiled Wheels for DeepSpeed and lxml**

1. **Download Wheels**

   - **DeepSpeed** (for Python 3.12.7, CUDA 12.4): [DeepSpeed Wheel](https://huggingface.co/NM156/deepspeed_wheel/tree/main)
   - **lxml** (for Python 3.12): [lxml Release](https://github.com/lxml/lxml/releases/tag/lxml-5.3.0)

2. **Install the Wheels**

   Activate your virtual environment and run:

   ```cmd
   pip install path\to\deepspeed-0.11.2+cuda124-cp312-cp312-win_amd64.whl
   pip install path\to\lxml-5.3.0-cp312-cp312-win_amd64.whl
   ```

3. **Verify Installation**

   ```cmd
   deepspeed --version
   pip show lxml
   espeak-ng --version
   ```

---

## Quick Start

1. **Launch the App**

   ```bash
   python main.py
   ```

2. **Select a Mode**

   - **Single PDF**: Choose a specific PDF file and extract its text.
   - **Batch PDFs**: Select a folder with multiple PDFs (the app processes all PDFs, preserving folder structure).
   - **Skip Extraction**: Use pre-extracted text files organized in folders.

3. **Extract Text (for Single/Batch Modes)**

   - The app will split the text into chapters if a Table of Contents (TOC) is available; otherwise, it extracts the entire document.

4. **Configure Kokoro TTS Settings**

   - Select your Kokoro model (the updated package handles this automatically).
   - Choose a `.pt` voicepack (e.g., `voices/af_sarah.pt`). The app automatically derives the language code from the first letter of the voice name.
   - Adjust the chunk size for your system’s VRAM.
   - Choose your desired output format (`.wav` or `.mp3`).

5. **Generate Audiobook**

   - Click **Start Process**.
   - Monitor progress via logs, progress bars, and estimated time.
   - Pause/Resume or Cancel the process as needed.

6. **Enjoy Your Audiobook**
   - Open the output folder to find your generated audio files.

---

## Technical Highlights

### PDF Extraction

- Built on [PyMuPDF](https://pymupdf.readthedocs.io/) for efficient text parsing.
- Cleans headers, footers, page numbers, and unwanted elements.
- Splits text based on chapters (if TOC is available) or extracts the entire document.

### Kokoro TTS

- **Text Normalization & Phonemization**
  - Advanced handling of dates, times, currency, etc.
- **Token-Based Splitting**
  - Splits text into chunks (<510 tokens) to meet model constraints and joins chunked audio into the final output.
- **Voicepacks (.pt)**
  - Each voicepack provides a reference embedding for a given voice.
  - The app derives the language code from the first letter of the voice identifier (e.g., `"af_sarah"` → `a`).

### Low-VRAM/Speed Tips

- **Chunk Size**
  - Adjust according to your GPU’s memory.
- **Device Selection**
  - Switch to CPU mode if a compatible GPU is unavailable.

---

## Contributing

We welcome contributions!

- Fork the repository, create a new branch, and submit a pull request.
- Report bugs or suggest features via [Issues](https://github.com/mateogon/pdf-narrator/issues).

---

## License

This project is released under the [MIT License](LICENSE.md).

---

Enjoy converting your PDFs into immersive audiobooks powered by **Kokoro v1.0 TTS**!
