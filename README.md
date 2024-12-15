# PDF Narrator

## Overview

Transform PDF documents into audiobooks effortlessly using advanced text extraction and text-to-speech technology. This tool is optimized for efficiency, making it ideal for low-VRAM systems and immersive reading experiences.

## Demo

Below is a preview of the PDF to Audiobook conversion process:

![Demo Screenshot](assets/demo.png)

## Features

- 🔍 **Intelligent PDF Text Extraction**: Removes headers, footers, and page numbers.
- 📖 **Chapter or Full-Book Conversion**: Extract based on Table of Contents (TOC) or the entire document.
- 🎙️ **Customizable Text-to-Speech Settings**: Supports multiple TTS models and speaker configurations.
- 💻 **Low-Resource Processing**: Adjusts chunk sizes dynamically for lower-VRAM systems.
- 🎨 **User-Friendly GUI with Theme Customization**: Switch themes easily and save preferences.

---

## Prerequisites

- **Python** 3.8+
- **FFmpeg**: Required for audio processing.
- **Piper TTS**: For high-quality text-to-speech conversion.

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/mateogon/pdf-narrator.git
   cd pdf-narrator
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**

   - **Ubuntu/Debian**:
     ```bash
     sudo apt-get install ffmpeg
     ```
   - **macOS**:
     ```bash
     brew install ffmpeg
     ```
   - **Windows**: Download and install from the [FFmpeg official site](https://ffmpeg.org/download.html).

5. **Download Recommended Voice Model**

   - Visit the [Hugging Face Piper Voices](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/libritts/high) page.
   - Download the `en_US-libritts-high.onnx` model and its corresponding `en_US-libritts-high.onnx.json` file.
   - Place the downloaded files in the `models/en/` directory:
     ```bash
     mkdir -p models/en
     mv /path/to/en_US-libritts-high.onnx models/en/
     mv /path/to/en_US-libritts-high.onnx.json models/en/
     ```

6. **Speaker ID and Voice Samples**
   - Use **Speaker ID 8** for the recommended voice.
   - Listen to available [voice samples](https://rhasspy.github.io/piper-samples/) for customization options.

---

## Quick Start

1. **Launch the App**

   ```bash
   python main.py
   ```

2. **Select PDF**

   - Browse and select a PDF file.
   - Choose extraction mode: _chapters_ or _full book_.

3. **Configure Audio Settings**

   - Select a Piper TTS model.
   - Choose speaker IDs (optional).
   - Adjust chunk size for compatibility with your system.
   - Select audio output format (`.wav` or `.mp3`).

4. **Generate Audiobook**
   - Click **Start Process**.
   - Monitor progress in real-time with progress bars and logs.

---

## Technical Highlights

### PDF Extraction

- **Automatic Cleaning**: Removes headers, footers, page numbers, and excessive whitespace.
- **TOC Segmentation**: If the document has a TOC, chapters are split accordingly.
- **Full-Book Mode**: Extracts the entire document if no TOC is available or desired.

### Audio Generation

- **Chunk-Based Processing**: Splits text into manageable chunks for processing.
- **Multi-Speaker Support**: Customize speaker IDs for varied narration.
- **VRAM-Friendly**: Dynamically adjusts chunk size based on system performance.

---

## Performance Optimization

- **Use GPU (CUDA)**: Select GPU as the processing device for faster TTS generation.
- **Adjust Chunk Size**: Reduce the chunk size if your system has limited VRAM.
- **Experiment with Models**: Piper's performance depends on the selected model and speaker IDs.

---

## Limitations

- **PDF Quality**: Extraction accuracy depends on the structure of the source PDF.
- **TTS Quality**: The quality of the generated audiobook may vary depending on the Piper model.
- **Processing Time**: Large documents may require significant time to process.

---

## Use Cases

- **Academia**: Convert research papers and textbooks into audiobooks.
- **Books**: Create audiobooks from eBooks or PDFs.
- **Documentation**: Narrate user manuals or technical documents.
- **Education**: Enhance learning with immersive reading.

---

## Recommended Workflow

1. Select a PDF file.
2. Choose TOC-based or full-book extraction.
3. Configure Piper TTS settings (model, speaker, chunk size).
4. Generate the audiobook.
5. Use the audiobook for immersive reading or standalone listening.

---

## Contributing

Contributions are welcome! If you have ideas for improvements or new features, please open an issue or create a pull request.

---

## Acknowledgments

- [Piper TTS](https://github.com/rhasspy/piper): High-quality text-to-speech engine.
- [PyMuPDF](https://pymupdf.readthedocs.io/): PDF parsing and text extraction library.
- [ttkbootstrap](https://ttkbootstrap.readthedocs.io/): Modern GUI framework for Python applications.
