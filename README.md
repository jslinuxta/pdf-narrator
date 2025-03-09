# PDF Narrator

**Updated for Kokoro v1.0!**  
Now setting up is easier—simply install the required Python dependencies (including the updated Kokoro package) and run the app. No more manual downloads or moving model files into specific folders.

PDF Narrator (Kokoro Edition) transforms your **PDF and EPUB documents** into audiobooks effortlessly using **advanced text extraction** and **Kokoro TTS** technology. With Kokoro v1.0, the integration is seamless and the setup is as simple as installing the requirements and running the application.

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

- **Intelligent Text Extraction**
  - Supports both **PDF** and **EPUB** formats.
  - For PDFs: Skips headers, footers, and page numbers; optionally splits based on Table of Contents (TOC).
  - For EPUBs: Extracts chapters based on internal HTML structure.

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
   ```bash
   pip install kokoro>=1.0.0
   ```

5. **Install FFmpeg (if required)**
   - Ubuntu/Debian: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Windows: Download from the FFmpeg official site

---

## Quick Start

1. **Launch the App**
   ```bash
   python main.py
   ```

2. **Select a Mode**
   - **Single Book:** Choose a PDF or EPUB file and extract its text.
   - **Batch Books:** Select a folder with multiple PDFs and/or EPUBs (processes all, preserving folder structure).
   - **Skip Extraction:** Use pre-extracted text files.

3. **Extract Text**
   - **PDFs:** Splits into chapters if TOC is available; otherwise, extracts entire document.
   - **EPUBs:** Extracts chapters based on internal structure.

4. **Configure Kokoro TTS Settings**
   - Select your Kokoro model and a `.pt` voicepack.
   - Adjust chunk size and output format (`.wav` or `.mp3`).

5. **Generate Audiobook**
   - Click Start Process and monitor progress.
   - Find your audio files in the output folder.

---

## Technical Highlights

- **Text Extraction**
  - PDF: Built on PyMuPDF for efficient parsing, with TOC-based splitting.
  - EPUB: Extracts text from HTML content files within the EPUB structure.

- **Kokoro TTS**
  - Advanced text normalization and phonemization.
  - Splits text into chunks (<510 tokens) and joins audio outputs.

---

## Contributing

Fork the repository, create a branch, and submit a pull request.  
Report bugs or suggest features via Issues.

---

## License

This project is released under the MIT License (LICENSE.md).

---

Enjoy converting your PDFs and EPUBs into immersive audiobooks with Kokoro v1.0 TTS!