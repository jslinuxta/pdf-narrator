# ui.py

import tkinter as tk
from tkinter import filedialog
from PyQt6.QtWidgets import QApplication, QFileDialog
from tkinter import scrolledtext
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import os
from extract import extract_book
# Import only Kokoro's audiobook generator
from generate_audiobook_kokoro import generate_audiobooks_kokoro, generate_audio_for_all_voices_kokoro
import sys
import threading
import time
import json
def available_voices():
        """Return the same hard-coded list of available voices."""
        return [
            "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica", "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
            "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck", "am_santa",
            "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
            "bm_daniel", "bm_fable", "bm_george", "bm_lewis",
            "jf_alpha", "jf_gongitsune", "jf_nezumi", "jf_tebukuro", "jm_kumo",
            "zf_xiaobei", "zf_xiaoni", "zf_xiaoxiao", "zf_xiaoyi", "zm_yunjian", "zm_yunxi", "zm_yunxia", "zm_yunyang",
            "ef_dora", "em_alex", "em_santa",
            "ff_siwis",
            "hf_alpha", "hf_beta", "hm_omega", "hm_psi",
            "if_sara", "im_nicola",
            "pf_dora", "pm_alex", "pm_santa"
        ]
class LogRedirector:
    def __init__(self, write_callback):
        self.write_callback = write_callback
        self.is_logging = False  # Prevent recursion

    def write(self, message):
        if self.is_logging:  # Avoid recursive logging
            return

        self.is_logging = True
        try:
            if message.strip():  # Avoid empty messages
                self.write_callback(message)
        finally:
            self.is_logging = False  # Reset flag

    def flush(self):
        pass  # Not needed for tkinter text widgets

class SourceFrame(tb.Frame):
    """
    Frame for PDF source selection and extraction options.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        # Variables
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.pdf_path = tk.StringVar()
        self.pdf_folder = tk.StringVar()
        self.manual_extracted_dir = tk.StringVar()
        self.extracted_text_dir = tk.StringVar()
        self.use_toc = tk.BooleanVar(value=True)
        self.extract_mode = tk.StringVar(value="chapters")
        self.source_option = tk.StringVar(value="single")  

        # Integrated source selection frame with combined radio buttons and file selection
        source_selection_frame = tb.Labelframe(self, text="Source Selection", padding=10, bootstyle="info")
        source_selection_frame.pack(fill=tk.X, pady=5, padx=10)

        # Row 1: Single Book Option
        single_row = tb.Frame(source_selection_frame)
        single_row.pack(fill=tk.X, pady=5, padx=5)
        
        tb.Radiobutton(
            single_row, 
            text="Single Book (PDF/EPUB)", 
            variable=self.source_option, 
            value="single",
            command=self._update_ui,
            width=21
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tb.Label(single_row, text="File:").pack(side=tk.LEFT, padx=(5,20))
        self.single_entry = tb.Entry(single_row, textvariable=self.pdf_path)
        self.single_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.single_browse_btn = tb.Button(single_row, text="Browse", command=self._browse_single_pdf)
        self.single_browse_btn.pack(side=tk.LEFT, padx=5)

        # Row 2: Batch Books Option
        batch_row = tb.Frame(source_selection_frame)
        batch_row.pack(fill=tk.X, pady=5, padx=5)
        
        tb.Radiobutton(
            batch_row, 
            text="Batch Books", 
            variable=self.source_option, 
            value="batch",
            command=self._update_ui,
            width=21
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tb.Label(batch_row, text="Folder:").pack(side=tk.LEFT, padx=5)
        self.batch_entry = tb.Entry(batch_row, textvariable=self.pdf_folder)
        self.batch_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.batch_browse_btn = tb.Button(batch_row, text="Browse", command=self._browse_pdf_folder)
        self.batch_browse_btn.pack(side=tk.LEFT, padx=5)

        # Row 3: Skip Extraction Option
        skip_row = tb.Frame(source_selection_frame)
        skip_row.pack(fill=tk.X, pady=5, padx=5)
        
        tb.Radiobutton(
            skip_row, 
            text="Use Existing Text", 
            variable=self.source_option, 
            value="skip",
            command=self._update_ui,
            width=21
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        tb.Label(skip_row, text="Folder:").pack(side=tk.LEFT, padx=5)
        self.skip_entry = tb.Entry(skip_row, textvariable=self.manual_extracted_dir)
        self.skip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.skip_browse_btn = tb.Button(skip_row, text="Browse", command=self._browse_extracted_folder)
        self.skip_browse_btn.pack(side=tk.LEFT, padx=5)

        # Separator
        tb.Separator(self, orient='horizontal').pack(fill=tk.X, pady=15, padx=10)

        # TOC & Extraction Mode with better styling
        options_frame = tb.Labelframe(self, text="Extraction Options", padding=10)
        options_frame.pack(fill=tk.X, pady=10, padx=10)

        toc_check = tb.Checkbutton(options_frame, text="Use TOC (if available)", variable=self.use_toc, padding=5)
        toc_check.pack(anchor=tk.W, padx=10, pady=10)
        
        mode_frame = tb.Frame(options_frame)
        mode_frame.pack(anchor=tk.W, padx=10, pady=10)
        tb.Label(mode_frame, text="Extract by: ").pack(side=tk.LEFT)
        tb.Radiobutton(mode_frame, text="Chapters", variable=self.extract_mode, value="chapters", padding=5).pack(side=tk.LEFT)
        tb.Radiobutton(mode_frame, text="Whole Book", variable=self.extract_mode, value="whole", padding=5).pack(side=tk.LEFT, padx=10)

        # Separator
        tb.Separator(self, orient='horizontal').pack(fill=tk.X, pady=15, padx=10)

        # Extracted Text Directory with better styling
        out_frame = tb.Labelframe(self, text="Output Directory", padding=10)
        out_frame.pack(pady=10, fill=tk.X, padx=10)
        
        tb.Label(out_frame, text="Extracted Text Directory (auto):").pack(anchor=tk.W, padx=5, pady=5)
        tb.Entry(out_frame, textvariable=self.extracted_text_dir, state=READONLY).pack(fill=tk.X, expand=True, padx=5, pady=5)

        # Initialize UI
        self._update_ui()

    def _update_ui(self):
        """
        Enable/disable controls based on the selected source option.
        """
        option = self.source_option.get()

        # Disable all entry fields and buttons first
        for widgets in [
            (self.single_entry, self.single_browse_btn),
            (self.batch_entry, self.batch_browse_btn),
            (self.skip_entry, self.skip_browse_btn)
        ]:
            for widget in widgets:
                widget.configure(state=tk.DISABLED)

        # Enable only the selected option's widgets
        if option == "single":
            self.single_entry.configure(state=tk.NORMAL)
            self.single_browse_btn.configure(state=tk.NORMAL)
        elif option == "batch":
            self.batch_entry.configure(state=tk.NORMAL)
            self.batch_browse_btn.configure(state=tk.NORMAL)
        elif option == "skip":
            self.skip_entry.configure(state=tk.NORMAL)
            self.skip_browse_btn.configure(state=tk.NORMAL)

    def _toggle_frame(self, frame, enable=True):
        """
        Enable or disable all widgets in a frame.
        """
        state = tk.NORMAL if enable else tk.DISABLED
        for child in frame.winfo_children():
            child.configure(state=state)

    def _browse_single_pdf(self):
        # Initialize or reuse the existing QApplication instance
        qt_app = QApplication.instance() or QApplication(sys.argv)

        # Open QFileDialog to select a single file (PDF or EPUB)
        path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Book File",
            self.project_dir,
            "Book Files (*.pdf *.epub);;PDF Files (*.pdf);;EPUB Files (*.epub);;All Files (*.*)"
        )
        if path:  # If a file was selected
            self.pdf_path.set(path)

            # Auto-populate extracted_text_dir for the single file
            book_name = os.path.splitext(os.path.basename(path))[0]
            extracted_text_dir = os.path.join(self.project_dir, "extracted_books", book_name)
            self.extracted_text_dir.set(extracted_text_dir)

            # Update the audiobook output folder in the parent app
            if hasattr(self.master.master, 'audio_frame'):  # Ensure parent has the audio_frame attribute
                self.master.master.audio_frame.update_audio_output_dir(book_name)

    def _browse_pdf_folder(self):
        # Initialize or reuse the existing QApplication instance
        qt_app = QApplication.instance() or QApplication(sys.argv)

        # Open QFileDialog to select a folder
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Folder Containing Books (PDF/EPUB)",
            self.project_dir
        )
        if folder:  # If a folder was selected
            self.pdf_folder.set(folder)

            # Get the last part of the folder name
            folder_name = os.path.basename(folder.rstrip(os.sep))

            # Set extracted_text_dir as the base output folder for batch mode
            extracted_text_dir = os.path.join(self.project_dir, "extracted_books", folder_name)
            self.extracted_text_dir.set(extracted_text_dir)

            # Update the audiobook output folder in the parent app
            if hasattr(self.master.master, 'audio_frame'):  # Ensure parent has the audio_frame attribute
                self.master.master.audio_frame.update_audio_output_dir(folder_name)


    def _browse_extracted_folder(self):
        # Initialize or reuse the existing QApplication instance
        qt_app = QApplication.instance() or QApplication(sys.argv)

        # Open QFileDialog to select a folder
        folder = QFileDialog.getExistingDirectory(
            None,
            "Select Existing Text Folder",
            self.project_dir
        )
        if folder:  # If a folder was selected
            self.manual_extracted_dir.set(folder)

            # Update the audiobook output folder in the parent app
            if hasattr(self.master.master, 'audio_frame'):  # Ensure parent has the audio_frame attribute
                book_name = os.path.basename(folder.rstrip(os.sep))  # Get the last folder name
                self.master.master.audio_frame.update_audio_output_dir(book_name)


    # Methods to get user selections
    def get_source_option(self):
        return self.source_option.get()

    def get_pdf_path(self):
        return self.pdf_path.get()

    def get_pdf_folder(self):
        return self.pdf_folder.get()

    def get_manual_extracted_dir(self):
        return self.manual_extracted_dir.get()

    def get_extracted_text_dir(self):
        return self.extracted_text_dir.get()

    def get_use_toc(self):
        return self.use_toc.get()

    def get_extract_mode(self):
        return self.extract_mode.get()

class AudioFrame(tb.Frame):
    """
    Frame for Kokoro voice selection + audiobook settings.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        # Variables
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        # Set default voice to "am_liam" (no longer a file path)
        self.voicepack = tk.StringVar(value="am_liam")
        self.chunk_size = tk.IntVar(value=510)
        self.audio_format = tk.StringVar(value=".wav")
        self.audio_output_dir = tk.StringVar()
        self.device = tk.StringVar(value="cuda")

        # Voice Selection with better grouping
        voicepack_frame = tb.Labelframe(self, text="Voice Selection", padding=10, bootstyle="info")
        voicepack_frame.pack(fill=tk.X, pady=10, padx=10)

        voice_row = tb.Frame(voicepack_frame)
        voice_row.pack(fill=tk.X, pady=5)
        
        tb.Label(voice_row, text="Voice:").pack(side=tk.LEFT, padx=5)
        # Use the available voices list instead of scanning .pt files
        voice_list = available_voices()
        voicepack_combo = tb.Combobox(
            voice_row,
            textvariable=self.voicepack,
            values=voice_list,
            state="readonly",
            width=30
        )
        voicepack_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # If there are voices, select the first one by default
        if voice_list:
            voicepack_combo.current(0)
        
        # Separator
        tb.Separator(self, orient='horizontal').pack(fill=tk.X, pady=15, padx=10)

        # Audio Generation Settings with better styling
        settings_frame = tb.Labelframe(self, text="Generation Settings", padding=10)
        settings_frame.pack(fill=tk.X, pady=10, padx=10)

        # Chunk Size with better UI
        chunk_frame = tb.Frame(settings_frame)
        chunk_frame.pack(fill=tk.X, pady=10)

        tb.Label(chunk_frame, text="Chunk Size:").pack(side=tk.LEFT, padx=5)
        
        # Use predefined options instead of a spinbox
        chunk_options = ["510 (Small)", "1020 (Medium)", "2040 (Large)"]
        chunk_combo = tb.Combobox(
            chunk_frame, 
            values=chunk_options, 
            state="readonly",
            width=15
        )
        chunk_combo.current(0)  # Select the first option by default
        chunk_combo.pack(side=tk.LEFT, padx=5)
        chunk_combo.bind("<<ComboboxSelected>>", self._update_chunk_size)

        # Audio Format
        format_frame = tb.Frame(settings_frame)
        format_frame.pack(fill=tk.X, pady=10)

        tb.Label(format_frame, text="Output Format:").pack(side=tk.LEFT, padx=5)
        formats = [".wav (High Quality)", ".mp3 (Smaller Size)"]
        format_combo = tb.Combobox(
            format_frame, 
            values=formats, 
            state="readonly",
            width=20
        )
        format_combo.current(0)  # Select the first option by default
        format_combo.pack(side=tk.LEFT, padx=5)
        format_combo.bind("<<ComboboxSelected>>", self._update_audio_format)

        # Device Selection with better styling
        device_frame = tb.Frame(settings_frame)
        device_frame.pack(fill=tk.X, pady=10)

        tb.Label(device_frame, text="Processing Device:").pack(side=tk.LEFT, padx=5)
        tb.Radiobutton(device_frame, text="GPU (CUDA) - Faster", variable=self.device, value="cuda", padding=5).pack(side=tk.LEFT, padx=5)
        tb.Radiobutton(device_frame, text="CPU - More Compatible", variable=self.device, value="cpu", padding=5).pack(side=tk.LEFT, padx=5)

        # Separator
        tb.Separator(self, orient='horizontal').pack(fill=tk.X, pady=15, padx=10)

        # Output Directory with better styling
        output_frame = tb.Labelframe(self, text="Output Location", padding=10)
        output_frame.pack(fill=tk.X, pady=10, padx=10)

        tb.Label(output_frame, text="Audiobook Output Folder:").pack(anchor=tk.W, padx=5, pady=5)
        tb.Entry(output_frame, textvariable=self.audio_output_dir, state=READONLY).pack(fill=tk.X, expand=True, padx=5, pady=5)

    def get_voicepack(self):
        """
        Returns the selected voice name (no longer a file path).
        """
        return self.voicepack.get()
    # Add new methods for the enhanced functionality
    def _update_chunk_size(self, event):
        """Update chunk size based on combobox selection"""
        selection = event.widget.get()
        if "Small" in selection:
            self.chunk_size.set(510)
        elif "Medium" in selection:
            self.chunk_size.set(1020)
        elif "Large" in selection:
            self.chunk_size.set(2040)

    def _update_audio_format(self, event):
        """Update audio format based on combobox selection"""
        selection = event.widget.get()
        if "wav" in selection:
            self.audio_format.set(".wav")
        elif "mp3" in selection:
            self.audio_format.set(".mp3")


    def get_device(self):
        return self.device.get()

    def update_audio_output_dir(self, book_name):
        """
        Dynamically update the audiobook output folder based on the book name.
        """
        if book_name:
            audio_output_dir = os.path.join(self.project_dir, "audiobooks", book_name)
            os.makedirs(audio_output_dir, exist_ok=True)
            self.audio_output_dir.set(audio_output_dir)
        else:
            self.audio_output_dir.set("")

    def get_audio_output_dir(self):
        return self.audio_output_dir.get()

    def get_voicepack(self):
        """
        Returns the absolute path to the Kokoro .pt voicepack file
        """
        selected_vp = self.voicepack.get()
        return  selected_vp if selected_vp else ""

    def get_chunk_size(self):
        return self.chunk_size.get()

    def get_audio_format(self):
        return self.audio_format.get()

class ProgressFrame(tb.Frame):
    """
    Frame for showing progress bars, logs, and controlling start/pause/cancel.
    The buttons themselves are moved to the main app for visibility.
    """
    def __init__(self, master, app, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.app = app
        self.pause_event = threading.Event()
        self.pause_event.set()

        # Variables
        self.extract_progress = tk.DoubleVar(value=0.0)
        self.audio_progress = tk.DoubleVar(value=0.0)
        self.status_text = tk.StringVar(value="Ready to process")
        self.estimated_time_text = tk.StringVar(value="N/A")
        self.current_file_text = tk.StringVar(value="")
        self.progress_count_text = tk.StringVar(value="")
        self.percentage_text = tk.StringVar(value="0%")
        self.extract_percent = tk.StringVar(value="0%")
        self.audio_percent = tk.StringVar(value="0%")
        
        # Setup the UI components
        self.setup_ui()
        
        # Redirect stdout and stderr to the UI
        sys.stdout = LogRedirector(self.log_message)
        sys.stderr = LogRedirector(self.log_message)
        
        self.cancellation_flag = False
        self.process_thread = None
        self.running = False
        
    def setup_ui(self):
        """Set up the progress tab UI components"""
        # Action buttons at the top (always visible)
        # Remove the "light" bootstyle from the btn_frame to use default background
        btn_frame = tb.Frame(self)
        btn_frame.pack(fill=tk.X, pady=(10, 5), padx=10)
        
        # Create the unified status and progress section
        top_section = tb.Frame(self)
        top_section.pack(fill=tk.X, pady=5)
        
        unified_frame = tb.Labelframe(top_section, text="Process Status", padding=10, bootstyle="info")
        unified_frame.pack(fill=tk.X, pady=5)
        
        # Status indicators in the top row
        status_row = tb.Frame(unified_frame)
        status_row.pack(fill=tk.X, pady=(0, 10))
        
        # Left side: Current status and file
        status_left = tb.Frame(status_row)
        status_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        status_label = tb.Label(status_left, text="Status:", width=8)
        status_label.pack(side=tk.LEFT, padx=(0, 5))
        tb.Label(status_left, textvariable=self.status_text, font="-weight bold").pack(side=tk.LEFT)
        
        # Right side: Time remaining and count
        status_right = tb.Frame(status_row)
        status_right.pack(side=tk.RIGHT)
        
        tb.Label(status_right, text="Time Left:").pack(side=tk.LEFT, padx=(10, 5))
        tb.Label(status_right, textvariable=self.estimated_time_text).pack(side=tk.LEFT)
        
        # Current file info
        file_row = tb.Frame(unified_frame)
        file_row.pack(fill=tk.X, pady=(0, 10))
        
        tb.Label(file_row, text="Current:", width=8).pack(side=tk.LEFT, padx=(0, 5))
        tb.Label(file_row, textvariable=self.current_file_text).pack(side=tk.LEFT)
        
        tb.Label(file_row, textvariable=self.progress_count_text).pack(side=tk.RIGHT)
        
        # Progress bars with enhanced styling
        tb.Separator(unified_frame, orient='horizontal').pack(fill=tk.X, pady=5)
        
        # Extract progress with better visual styling
        extract_row = tb.Frame(unified_frame)
        extract_row.pack(fill=tk.X, pady=5)
        
        # Use an icon or distinctive marker
        tb.Label(extract_row, text="📄", font="-size 12").pack(side=tk.LEFT, padx=(0, 5))
        tb.Label(extract_row, text="Text Extraction:").pack(side=tk.LEFT)
        
        tb.Label(extract_row, textvariable=self.extract_percent, width=5).pack(side=tk.RIGHT)
        
        tb.Progressbar(unified_frame, variable=self.extract_progress, maximum=100, 
                    bootstyle="info").pack(fill=tk.X, pady=(0, 10))
        
        # Audio generation progress
        audio_row = tb.Frame(unified_frame)
        audio_row.pack(fill=tk.X, pady=5)
        
        tb.Label(audio_row, text="🔊", font="-size 12").pack(side=tk.LEFT, padx=(0, 5))
        tb.Label(audio_row, text="Audio Generation:").pack(side=tk.LEFT)
        
        tb.Label(audio_row, textvariable=self.audio_percent, width=5).pack(side=tk.RIGHT)
        
        tb.Progressbar(unified_frame, variable=self.audio_progress, maximum=100,
                    bootstyle="success").pack(fill=tk.X)
        
        # Log section with clear button
        log_frame = tb.Labelframe(self, text="Process Logs", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 5))
        
        log_header = tb.Frame(log_frame)
        log_header.pack(fill=tk.X, pady=(0, 5))
        
        clear_log_btn = tb.Button(log_header, text="Clear Logs", bootstyle="secondary-outline", 
                                command=lambda: self.log_text.delete(1.0, tk.END))
        clear_log_btn.pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Create the buttons in the fixed area with better grouping
        # Use default frame without bootstyle to inherit theme background
        control_group = tb.Frame(btn_frame)
        control_group.pack(side=tk.LEFT, pady=5)
        
        self.start_button = tb.Button(
            control_group, 
            text="▶ Start Process", 
            bootstyle="success", 
            command=self._start_process_thread,
            width=15
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 15))
        
        # Group pause/resume together
        pause_resume_group = tb.Frame(control_group)
        pause_resume_group.pack(side=tk.LEFT)
        
        self.pause_button = tb.Button(
            pause_resume_group, 
            text="⏸ Pause", 
            bootstyle="warning", 
            command=self._pause_process,
            width=10
        )
        self.pause_button.pack(side=tk.LEFT, padx=(0, 5))

        self.resume_button = tb.Button(
            pause_resume_group, 
            text="⏯ Resume", 
            bootstyle="info", 
            command=self._resume_process,
            state=tk.DISABLED,
            width=10
        )
        self.resume_button.pack(side=tk.LEFT)
        
        # Visual separator
        tb.Separator(btn_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=5)
        
        # Cancel on its own
        self.cancel_button = tb.Button(
            btn_frame, 
            text="⏹ Cancel", 
            bootstyle="danger", 
            command=self._cancel_process,
            state=tk.DISABLED,
            width=10
        )
        self.cancel_button.pack(side=tk.LEFT, pady=5)
    # Add/modify methods to update the new UI elements
    def update_extract_progress(self, value):
        self.extract_progress.set(value)
        self.extract_percent.set(f"{int(value)}%")

    def update_audio_progress(self, value):
        self.audio_progress.set(value)
        self.audio_percent.set(f"{int(value)}%")
    def set_current_file(self, filename):
        """Update the current file being processed"""
        if filename:
            self.current_file_text.set(filename)
        else:
            self.current_file_text.set("None")

    def set_progress_count(self, current, total):
        """Update the progress count (e.g., "Processing file 2 of 15")"""
        if current and total:
            self.progress_count_text.set(f"File {current} of {total}")
        else:
            self.progress_count_text.set("")


    def _start_process_thread(self):
        # Start the process in a background thread
        if self.process_thread and self.process_thread.is_alive():
            self.log_message("A process is already running.")
            return

        self.running = True
        self.cancel_button.config(state=NORMAL)
        self.start_button.config(state=DISABLED)
        self.process_thread = threading.Thread(target=self._start_process, daemon=True)
        self.process_thread.start()

    def _start_process(self):
        self.log_message("Starting process...")
        self.set_status("Extracting text...")
        self.update_extract_progress(0)
        self.update_audio_progress(0)
        self.set_current_file("Initializing...")
        self.set_progress_count(0, 0)
        self.cancellation_flag = False

        try:
            source_option = self.app.source_frame.get_source_option()
            use_toc = self.app.source_frame.get_use_toc()
            extract_mode = self.app.source_frame.get_extract_mode()
            source_folder = self.app.source_frame.get_pdf_folder()  # Batch source folder
            extracted_root = self.app.source_frame.get_extracted_text_dir()  # Base for extracted output
            manual_extracted_dir = self.app.source_frame.get_manual_extracted_dir()

            # Remove model_path reference
            # Extract the voice identifier from the selected voicepack path.
            voicepack = self.app.audio_frame.get_voicepack()
            # For example, "Kokoro/voices/af_sarah.pt" becomes "af_sarah"
            voice = os.path.splitext(os.path.basename(voicepack))[0]
            chunk_size = self.app.audio_frame.get_chunk_size()
            audio_format = self.app.audio_frame.get_audio_format()
            audio_root = self.app.audio_frame.get_audio_output_dir()
            device = self.app.audio_frame.get_device()

            all_extracted_folders = []

            if source_option == "skip":
                # Skip extraction, recursively process the folder structure
                if not os.path.isdir(manual_extracted_dir):
                    raise Exception("Manual extracted folder is invalid or doesn't exist.")

                # Recursively find all text files and keep the folder structure
                for root, _, files in os.walk(manual_extracted_dir):
                    if any(file.lower().endswith(".txt") for file in files):  # Process folders with .txt files
                        rel_path = os.path.relpath(root, manual_extracted_dir)
                        output_subfolder = os.path.join(audio_root, rel_path)
                        
                        os.makedirs(output_subfolder, exist_ok=True)
                        all_extracted_folders.append((root, output_subfolder))

                self.update_extract_progress(100)

            elif source_option == "batch":
                if not os.path.isdir(source_folder):
                    raise Exception("Batch source folder is invalid or doesn't exist.")

                # Recursively find all PDFs and process them
                book_files = []
                for root, _, files in os.walk(source_folder):
                    for file in files:
                        if file.lower().endswith(('.pdf', '.epub')):
                            book_files.append(os.path.join(root, file))

                if not book_files:
                    raise Exception("No PDF or EPUB files found in the selected folder.")

                total_pdfs = len(book_files)
                for i, pdf_path in enumerate(book_files, start=1):
                    if self.cancellation_flag:
                        raise Exception("Process canceled by user during batch extraction.")

                    filename = os.path.basename(pdf_path)
                    self.set_current_file(filename)
                    # Calculate relative path and replicate folder structure
                    rel_path = os.path.relpath(pdf_path, source_folder)
                    folder_part = os.path.dirname(rel_path)
                    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
                    extracted_text_base = os.path.join(extracted_root, folder_part)
                    os.makedirs(extracted_text_base, exist_ok=True)

                    def extraction_progress_callback(progress):
                        self.update_extract_progress(int((i - 1 + progress / 100) / total_pdfs * 100))
                        if self.cancellation_flag:
                            raise Exception("Process canceled by user.")

                    # Extract PDF to its designated folder
                    extract_book(
                        pdf_path, use_toc=use_toc, extract_mode=extract_mode,
                        output_dir=extracted_text_base, progress_callback=extraction_progress_callback
                    )
                    self.log_message(f"Extracted: {pdf_path}, saved to {extracted_text_base}")
                    all_extracted_folders.append((extracted_text_base, os.path.join(audio_root, folder_part)))

                self.update_extract_progress(100)

            else:
                # Single PDF
                pdf_path = self.app.source_frame.get_pdf_path()
                if not os.path.isfile(pdf_path):
                    raise Exception("Single PDF path is invalid or doesn't exist.")
                book_name = os.path.splitext(os.path.basename(pdf_path))[0]

                def extraction_progress_callback(progress):
                    self.update_extract_progress(progress)
                    if self.cancellation_flag:
                        raise Exception("Process canceled by user.")

                extract_book(
                    pdf_path,
                    use_toc=use_toc,
                    extract_mode=extract_mode,
                    output_dir=extracted_root,  # e.g. "extracted_books"
                    progress_callback=extraction_progress_callback
                )

                self.update_extract_progress(100)
                all_extracted_folders.append((extracted_root, os.path.join(audio_root, book_name)))
                self.log_message(f"Extracted: {book_name}, saved to {extracted_root}")

            # Audiobook generation
            self.set_status("Generating audiobook...")
            self.update_audio_progress(10)

            total_folders = len(all_extracted_folders)
            for i, (input_folder, output_folder) in enumerate(all_extracted_folders, start=1):
                folder_name = os.path.basename(input_folder)
                self.set_current_file(folder_name)
                self.set_progress_count(i, total_folders)
                if self.cancellation_flag:
                    raise Exception("Process canceled by user during TTS generation.")

                os.makedirs(output_folder, exist_ok=True)

                

                generate_audiobooks_kokoro(
                    input_dir=input_folder,
                    lang_code=voice[0],           # default language code (adjust if needed)
                    voice=voice,             # use the UI-selected voice
                    output_dir=output_folder,
                    audio_format=audio_format,
                    speed=1,
                    split_pattern=r'\n+',
                    progress_callback=lambda progress: self.update_audio_progress(
                        int((i - 1 + progress / 100) / total_folders * 100)
                    ),
                    cancellation_flag=lambda: self.cancellation_flag,
                    update_estimate_callback=self.set_estimated_time,
                    pause_event=self.pause_event,
                    file_callback = lambda filename, i, total: (
                        self.set_current_file(filename),
                        self.set_progress_count(i, total)
                    )
                )

                self.log_message(f"Audiobook generation completed for: {input_folder}. Output: {output_folder}")
                self.update_audio_progress(int(i / total_folders * 100))

            self.set_status("Process completed successfully.")
            self.update_audio_progress(100)

        except Exception as e:
            self.log_message(f"Error occurred: {e}")
            self.set_status("Process failed.")
        finally:
            self.running = False
            self.cancel_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            self.set_current_file("")
            self.set_progress_count(0, 0)


    def _pause_process(self):
        self.pause_event.clear()  # Pause the process
        self.pause_button.config(state=DISABLED)
        self.resume_button.config(state=NORMAL)
        self.log_message("Process paused.")

    def _resume_process(self):
        self.pause_event.set()  # Resume the process
        self.resume_button.config(state=DISABLED)
        self.pause_button.config(state=NORMAL)
        self.log_message("Process resumed.")

    def _cancel_process(self):
        self.log_message("Canceling process...")
        self.cancellation_flag = True
        self.set_status("Process canceling...")

        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=1)  # Wait briefly
            self.running = False
            self.start_button.config(state=NORMAL)
            self.cancel_button.config(state=DISABLED)

    def log_message(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def set_status(self, status):
        self.status_text.set(status)

    def set_estimated_time(self, seconds_left):
        if seconds_left <= 0:
            self.estimated_time_text.set("Processing complete!")
            self.percentage_text.set("100% complete")
            return
            
        # Format time in appropriate units
        m, s = divmod(int(seconds_left), 60)
        h, m = divmod(m, 60)
        
        if h > 0:
            time_str = f"{h}h {m}m {s}s"
        elif m > 0:
            time_str = f"{m}m {s}s"
        else:
            time_str = f"{s}s"
            
        self.estimated_time_text.set(f"{time_str}")
        
        # Update percentage display if we have the data
        if hasattr(self, 'audio_progress'):
            progress = self.audio_progress.get()
            self.percentage_text.set(f"{int(progress)}% complete")

class AudiobookApp(tb.Window):
    """
    Main application window, uses a ttkbootstrap Notebook with three tabs:
      1) Source (PDF extraction)
      2) Audio (Kokoro model/voicepack selection)
      3) Progress & Logs
    """
    CONFIG_FILE = "config.json"
    def configure_styles(self):
        style = tb.Style()
        style.configure('TLabel', font=('Helvetica', 10))
        style.configure('TButton', padding=5)
        style.configure('TLabelframe', padding=10)
        style.configure('TRadiobutton', padding=5)
        style.configure('TCheckbutton', padding=5)

    def __init__(self, *args, **kwargs):
        self.selected_theme = self._load_theme_from_config()
        super().__init__(*args, themename=self.selected_theme, **kwargs)
        tb.Style().theme_use(self.selected_theme)  # Set initial theme
        self.configure_styles()
        self.title("PDF Narrator")
        self.geometry("1000x800")
        self.minsize(850, 700)  # Slightly larger minimum size to ensure buttons are visible

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create a main container frame with grid layout
        self.main_container = tb.Frame(self)
        self.main_container.pack(fill=BOTH, expand=True)
        self.main_container.grid_rowconfigure(1, weight=1)  # This makes the notebook row expandable
        self.main_container.grid_columnconfigure(0, weight=1)

        # Header (fixed at top)
        header_frame = tb.Frame(self.main_container)
        header_frame.grid(row=0, column=0, sticky="ew", pady=10)
        
        title_label = tb.Label(header_frame, text="PDF Narrator", font="-size 16 -weight bold")
        title_label.pack()
        
        subtitle_label = tb.Label(header_frame, text="Convert your PDFs and EPUBs into narrated audiobooks")
        subtitle_label.pack(pady=(5, 0))

        # Notebook tabs (fixed at top, below header)
        self.notebook = tb.Notebook(self.main_container)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5) # sticky="nsew" makes it expand in all directions
        
        # Create frames for each tab
        self.source_tab = tb.Frame(self.notebook)
        self.audio_tab = tb.Frame(self.notebook)
        self.progress_tab = tb.Frame(self.notebook)
        self.voice_test_tab = tb.Frame(self.notebook)

        self.notebook.add(self.source_tab, text="Source")
        self.notebook.add(self.audio_tab, text="Audio")
        self.notebook.add(self.progress_tab, text="Progress & Logs")
        self.notebook.add(self.voice_test_tab, text="Voice Test")

        # Create scrollable content area for each tab
        self.setup_scrollable_tab(self.source_tab, SourceFrame)
        self.setup_scrollable_tab(self.audio_tab, AudioFrame)

        self.setup_progress_tab()

        # Set up the scrollable content for the Voice Test tab
        self.setup_scrollable_tab(self.voice_test_tab, VoiceTestFrame)

        # Footer (fixed at bottom)
        footer_frame = tb.Frame(self.main_container)
        footer_frame.grid(row=3, column=0, sticky="ew", pady=5)
        
        self.open_output_button = tb.Button(footer_frame, text="Open Extracted Text Folder", command=self._open_output_folder)
        self.open_output_button.pack(side=LEFT, padx=10)

        self.open_audio_output_button = tb.Button(
            footer_frame, 
            text="Open Audiobook Folder", 
            command=self._open_audiobook_folder
        )
        self.open_audio_output_button.pack(side=LEFT, padx=10)

        # Theme Selector
        theme_selector_frame = tb.Frame(footer_frame)
        theme_selector_frame.pack(side=RIGHT, padx=10)

        tb.Label(theme_selector_frame, text="Theme:").pack(side=LEFT)
        self.theme_var = tk.StringVar(value=self.selected_theme)
        themes = tb.Style().theme_names()
        self.theme_combo = tb.Combobox(
            theme_selector_frame, 
            textvariable=self.theme_var, 
            values=themes, 
            state="readonly", 
            width=15
        )
        self.theme_combo.pack(side=LEFT, padx=5)
        self.theme_combo.bind("<<ComboboxSelected>>", self._change_theme)

        exit_button = tb.Button(footer_frame, text="Exit", command=self.on_close)
        exit_button.pack(side=RIGHT, padx=10)
        reset_button = tb.Button(
            footer_frame, 
            text="Reset Settings", 
            bootstyle="secondary",
            command=self._reset_config
        )
        reset_button.pack(side=tk.RIGHT, padx=10)

        self.load_config()
    def _reset_config(self):
        """Reset all settings to default values"""
        if tk.messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            # Reset source settings
            self.source_frame.source_option.set("single")
            self.source_frame.pdf_path.set("")
            self.source_frame.pdf_folder.set("")
            self.source_frame.manual_extracted_dir.set("")
            self.source_frame.extracted_text_dir.set("")
            self.source_frame.use_toc.set(True)
            self.source_frame.extract_mode.set("chapters")
            
            # Reset audio settings
            self.audio_frame.voicepack.set("voices/am_liam.pt") 
            self.audio_frame.chunk_size.set(510)
            self.audio_frame.audio_format.set(".wav")
            self.audio_frame.device.set("cuda")
            
            # Update UI
            self.source_frame._update_ui()
            
            tk.messagebox.showinfo("Settings Reset", "All settings have been reset to default values.")

    def _open_output_folder(self):
        output_dir = self.source_frame.get_extracted_text_dir()
        if output_dir and os.path.isdir(output_dir):
            self._open_folder(output_dir)
        else:
            tk.messagebox.showwarning("Warning", "No valid output directory selected.")

    def _open_audiobook_folder(self):
        audio_dir = self.audio_frame.get_audio_output_dir()
        if audio_dir and os.path.isdir(audio_dir):
            self._open_folder(audio_dir)
        else:
            tk.messagebox.showwarning("Warning", "No valid audiobook output directory selected.")
    def _open_folder(self, folder_path):
        """Safely open a folder using the appropriate method for the OS"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folder_path)
            elif os.name == 'posix':  # macOS or Linux
                import subprocess
                subprocess.Popen(['xdg-open', folder_path])
        except Exception as e:
            tk.messagebox.showerror("Error", f"Could not open folder: {str(e)}")

    def _change_theme(self, event):
        new_theme = self.theme_var.get()
        tb.Style().theme_use(new_theme)
        self.selected_theme = new_theme
        self.configure_styles()  # Reapply custom styles

    def _load_theme_from_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get("theme", "flatly")
            except Exception as e:
                print(f"Failed to load theme from config: {e}")
        return "flatly"  # Default theme
    
    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)

                    # Load source option and paths
                    self.source_frame.source_option.set(config.get("source_option", "single"))
                    self.source_frame.pdf_path.set(config.get("pdf_path", ""))
                    self.source_frame.pdf_folder.set(config.get("pdf_folder", ""))
                    self.source_frame.manual_extracted_dir.set(config.get("manual_extracted_dir", ""))
                    self.source_frame.extracted_text_dir.set(config.get("extracted_text_dir", ""))

                    # Update audio output directory based on source option
                    if config["source_option"] == "single" and config.get("pdf_path"):
                        book_name = os.path.splitext(os.path.basename(config["pdf_path"]))[0]
                    elif config["source_option"] == "batch" and config.get("pdf_folder"):
                        book_name = os.path.basename(config["pdf_folder"].rstrip(os.sep))
                    elif config["source_option"] == "skip" and config.get("manual_extracted_dir"):
                        book_name = os.path.basename(config["manual_extracted_dir"].rstrip(os.sep))
                    else:
                        book_name = ""
                    
                    if book_name:
                        self.update_audio_output_dir(book_name)

                    # Load audio settings - remove model_path
                    self.audio_frame.voicepack.set(config.get("voicepack", "voices/am_liam.pt"))
                    self.audio_frame.chunk_size.set(config.get("chunk_size", 510))
                    self.audio_frame.audio_format.set(config.get("audio_format", ".wav"))

                    # Load theme
                    self.selected_theme = config.get("theme", "flatly")
                    self.theme_var.set(self.selected_theme)
                    tb.Style().theme_use(self.selected_theme)

                    # Update UI based on the loaded source option
                    self.source_frame._update_ui()

            except Exception as e:
                print(f"Failed to load config: {e}")

    def save_config(self):
        config = {
            "source_option": self.source_frame.get_source_option(),  # Save selected mode
            "pdf_path": self.source_frame.get_pdf_path(),
            "pdf_folder": self.source_frame.get_pdf_folder(),
            "manual_extracted_dir": self.source_frame.get_manual_extracted_dir(),
            "extracted_text_dir": self.source_frame.get_extracted_text_dir(),  # Save extracted text directory
            # Remove model_path
            "voicepack": self.audio_frame.get_voicepack(),
            "chunk_size": self.audio_frame.get_chunk_size(),
            "audio_format": self.audio_frame.get_audio_format(),
            "theme": self.selected_theme,
        }
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    def update_audio_output_dir(self, book_name):
        self.audio_frame.update_audio_output_dir(book_name)

    def on_close(self):
        print("Application is closing.")  # Debug
        self.save_config()
        self.destroy()
    def _configure_canvas_window(self, event):
            # Update the canvas window width to match the canvas width
            self.content_canvas.itemconfig(self.canvas_window, width=event.width)
        
    def setup_scrollable_tab(self, tab_frame, content_class):
        # Make tab_frame use all available space
        tab_frame.pack_propagate(False)

        # Create an extra container frame inside the tab_frame
        container = tb.Frame(tab_frame)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas and scrollbar for scrollable content inside the container
        canvas = tk.Canvas(container)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tb.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create frame inside canvas for content
        scrollable_frame = tb.Frame(canvas)
        scrollable_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Configure canvas to adjust to frame size for scrolling
        def configure_frame(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable_frame.bind("<Configure>", configure_frame)
        
        # Ensure the scrollable frame expands to the width of the canvas
        def configure_canvas(event):
            canvas.itemconfig(scrollable_frame_id, width=event.width)
        canvas.bind("<Configure>", configure_canvas)
        
        # Enable mousewheel scrolling on the entire app and the scrollable frame
        self.bind_mousewheel(canvas)
        scrollable_frame.bind_all("<MouseWheel>", lambda event: self._on_mousewheel(event, canvas))
        scrollable_frame.bind_all("<Button-4>", lambda event: self._on_mousewheel(event, canvas))
        scrollable_frame.bind_all("<Button-5>", lambda event: self._on_mousewheel(event, canvas))
        
        # Create and add content to the scrollable frame
        content = content_class(scrollable_frame)
        content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Save reference to the content
        if content_class == SourceFrame:
            self.source_frame = content
        elif content_class == AudioFrame:
            self.audio_frame = content

    def setup_progress_tab(self):
        # Progress tab should use all available space
        self.progress_tab.pack_propagate(False)
        
        # Create a container for the progress tab
        progress_container = tb.Frame(self.progress_tab)
        progress_container.pack(fill=tk.BOTH, expand=True)
        
        # Create a scrollable area for the logs
        canvas = tk.Canvas(progress_container)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tb.Scrollbar(progress_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10))
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create frame inside canvas for logs content
        scrollable_frame = tb.Frame(canvas)
        scrollable_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Configure canvas to adjust to frame size
        def configure_frame(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", configure_frame)
        
        # Make sure the scrollable frame expands to the width of the canvas
        def configure_canvas(event):
            canvas.itemconfig(scrollable_frame_id, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas)
        
        # Enable mousewheel scrolling
        self.bind_mousewheel(canvas)
        
        # Create the ProgressFrame with modified layout
        self.progress_frame = ProgressFrame(scrollable_frame, app=self)
        self.progress_frame.pack(fill=tk.BOTH, expand=True)
    def bind_mousewheel(self, canvas):
        # Bind the event globally on the entire window
        self.bind_all("<MouseWheel>", lambda event: self._on_mousewheel(event, canvas))  # Windows
        self.bind_all("<Button-4>", lambda event: self._on_mousewheel(event, canvas))   # Linux scroll up
        self.bind_all("<Button-5>", lambda event: self._on_mousewheel(event, canvas))   # Linux scroll down


    def _on_mousewheel(self, event, canvas):
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            canvas.yview_scroll(-1, "units")
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            canvas.yview_scroll(1, "units")
        return "break"

class VoiceTestFrame(tb.Frame):
    """
    Frame for testing TTS voices with sample text.
    """
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_text = tk.StringVar(value="This is a sample text to test how the voice sounds. You can modify this text to hear different words and expressions.")
        self.test_mode = tk.StringVar(value="single")
        self.selected_voice = tk.StringVar()
        self.test_output_dir = tk.StringVar(value=os.path.join(self.project_dir, "voice_tests"))
        
        os.makedirs(self.test_output_dir.get(), exist_ok=True)
        
        # Test Mode Selection remains unchanged...
        mode_frame = tb.Labelframe(self, text="Test Mode", padding=10, bootstyle="info")
        mode_frame.pack(fill=tk.X, pady=10, padx=10)
        
        tb.Radiobutton(
            mode_frame, 
            text="Test Single Voice", 
            variable=self.test_mode, 
            value="single",
            command=self._update_ui,
            padding=5
        ).pack(anchor=tk.W, padx=10, pady=5)
        tb.Radiobutton(
            mode_frame, 
            text="Test All Available Voices", 
            variable=self.test_mode, 
            value="all",
            command=self._update_ui,
            padding=5
        ).pack(anchor=tk.W, padx=10, pady=5)
        self.voice_container = tb.Frame(self)
        self.voice_container.pack(fill=tk.X, pady=10)
        # Voice Selection (for single voice mode)
        self.voice_frame = tb.Labelframe(self.voice_container, text="Voice Selection", padding=10, bootstyle="info")
        self.voice_frame.pack(fill=tk.X)
        voice_row = tb.Frame(self.voice_frame)
        voice_row.pack(fill=tk.X, pady=5)
        tb.Label(voice_row, text="Select Voice:").pack(side=tk.LEFT, padx=5)
        voicepacks = available_voices()
        voice_combo = tb.Combobox(
            voice_row,
            textvariable=self.selected_voice,
            values=voicepacks,
            state="readonly",
            width=30
        )
        voice_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        if voicepacks:
            voice_combo.current(0)
        
        # Sample Text Input
        text_frame = tb.Labelframe(self, text="Sample Text", padding=10)
        text_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self.text_input = scrolledtext.ScrolledText(text_frame, height=5, wrap=tk.WORD)
        self.text_input.pack(fill=tk.X, pady=5, padx=5)
        self.text_input.insert(tk.END, self.test_text.get())
        
        # Output directory frame
        output_frame = tb.Labelframe(self, text="Output Location", padding=10)
        output_frame.pack(fill=tk.X, pady=10, padx=10)
        
        output_row = tb.Frame(output_frame)
        output_row.pack(fill=tk.X, pady=5)
        
        tb.Label(output_row, text="Test Outputs:").pack(side=tk.LEFT, padx=5)
        tb.Entry(output_row, textvariable=self.test_output_dir, state=READONLY).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tb.Button(output_row, text="Open Folder", command=self._open_output_folder).pack(side=tk.LEFT, padx=5)
        
        # Buttons to run/stop the test
        buttons_frame = tb.Frame(self)
        buttons_frame.pack(fill=tk.X, pady=20, padx=10)
        
        tb.Button(
            buttons_frame, 
            text="▶ Run Voice Test", 
            bootstyle=SUCCESS,
            command=self._run_test,
            width=20
        ).pack(side=tk.LEFT, padx=10)
        
        tb.Button(
            buttons_frame, 
            text="⏹ Stop Test", 
            bootstyle=DANGER,
            command=self._stop_test,
            width=15,
            state=tk.DISABLED
        ).pack(side=tk.LEFT, padx=10)
        
        # Status label
        self.status_label = tb.Label(buttons_frame, text="Ready to test voices")
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # Progress bar for tests
        progress_frame = tb.Frame(self)
        progress_frame.pack(fill=tk.X, pady=10, padx=20)
        
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progressbar = tb.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progressbar.pack(fill=tk.X, pady=5)
        
        # Label to show current progress
        self.progress_label = tb.Label(progress_frame, text="")
        self.progress_label.pack(pady=5)
        
        # Initialize test thread and cancellation flag
        self.test_thread = None
        self.cancellation_flag = False
        
        # Update UI based on initial mode
        self._update_ui()
    
    def _update_ui(self):
        """Update UI based on selected test mode"""
        if self.test_mode.get() == "single":
            self.voice_frame.pack(fill=tk.X, pady=10, padx=10)
        else:
            self.voice_frame.pack_forget()
    
    
    def _open_output_folder(self):
        """Open the voice test output folder"""
        output_dir = self.test_output_dir.get()
        if output_dir and os.path.isdir(output_dir):
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(output_dir)
                elif os.name == 'posix':  # macOS or Linux
                    import subprocess
                    subprocess.Popen(['xdg-open', output_dir])
            except Exception as e:
                tk.messagebox.showerror("Error", f"Could not open folder: {str(e)}")
        else:
            tk.messagebox.showwarning("Warning", "No valid output directory.")
    
    def _run_test(self):
        """Run the voice test in a separate thread"""
        if self.test_thread and self.test_thread.is_alive():
            tk.messagebox.showinfo("Test in Progress", "A voice test is already running.")
            return
        
        # Get the latest text from the text widget
        test_text = self.text_input.get("1.0", tk.END).strip()
        if not test_text:
            tk.messagebox.showwarning("Warning", "Please enter some text to test.")
            return
        
        # Reset cancellation flag
        self.cancellation_flag = False
        
        # Create the test thread
        self.test_thread = threading.Thread(
            target=self._run_test_thread,
            args=(test_text,),
            daemon=True
        )
        
        # Enable the Stop button
        for widget in self.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, tb.Button) and child['text'] == "Stop Test":
                    child.configure(state=NORMAL)
        
        # Start the thread
        self.test_thread.start()
    
    def _stop_test(self):
        """Stop the currently running test"""
        if self.test_thread and self.test_thread.is_alive():
            self.cancellation_flag = True
            self.status_label.config(text="Stopping test...")
        else:
            tk.messagebox.showinfo("No Test Running", "There is no voice test currently running.")
    
    def _run_test_thread(self, test_text):
        """Run the voice test in a background thread"""
        try:
            if self.test_mode.get() == "single":
                # For single voice testing
                voice = os.path.splitext(os.path.basename(self.selected_voice.get()))[0]
                self.status_label.config(text=f"Testing voice: {voice}")
                total_voices = 1
                self.progress_label.config(text=f"Testing voice 1/1: {voice}")
                output_file = os.path.join(self.test_output_dir.get(), f"test_{voice}.wav")
                
                from generate_audiobook_kokoro import test_single_voice_kokoro
                test_single_voice_kokoro(
                    input_text=test_text,
                    voice=voice,
                    output_path=output_file,
                    lang_code="a",  # Adjust if needed for your model
                    speed=1,
                    split_pattern=r'\n+',
                    cancellation_flag=lambda: self.cancellation_flag,
                    progress_callback=lambda progress, duration: self.progress_var.set(progress),
                    pause_event=None
                )
                self.progress_var.set(100)
            else:
                # For testing all available voices
                # Create a temporary text file for the test
                test_dir = os.path.join(self.project_dir, "voice_test_temp")
                os.makedirs(test_dir, exist_ok=True)
                
                test_file = os.path.join(test_dir, "test_text.txt")
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(test_text)
                    
                voices = available_voices()
                total_voices = len(voices)
                self.status_label.config(text=f"Testing all {total_voices} voices")

                from generate_audiobook_kokoro import generate_audio_for_all_voices_kokoro
                generate_audio_for_all_voices_kokoro(
                    input_path=test_file,
                    lang_code="a",  # Adjust if needed for your model
                    voices=voices,
                    output_dir=self.test_output_dir.get(),
                    speed=1,
                    split_pattern=r'\n+',
                    cancellation_flag=lambda: self.cancellation_flag,
                    progress_callback=lambda progress, duration: self.progress_var.set(progress),
                    pause_event=None
                )
                # Clean up the temporary file
                if os.path.exists(test_file):
                    os.remove(test_file)
                    
                # When done, set progress to 100%
                self.progress_var.set(100)
            
            if not self.cancellation_flag:
                self.status_label.config(text="Voice testing completed!")
            
            # Optionally prompt to open the output folder
            if tk.messagebox.askyesno("Test Complete", "Voice test completed. Open the output folder?"):
                self._open_output_folder()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.config(text=f"Error: {str(e)}")
        finally:
            # Re-enable the Run button and disable the Stop button
            for widget in self.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, tb.Button) and child['text'] == "Stop Test":
                        child.configure(state=DISABLED)
                    elif isinstance(child, tb.Button) and child['text'] == "Run Voice Test":
                        child.configure(state=NORMAL)