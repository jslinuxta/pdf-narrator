import os
import time
import numpy as np
import torch
from scipy.io.wavfile import write

# Kokoro imports
from Kokoro.models import build_model
from Kokoro.kokoro import generate


def generate_audio_for_file_kokoro(
    input_path,
    model,
    voicepack,
    output_path,
    device="cuda",
    cancellation_flag=None,
    progress_callback=None,
    pause_event=None,
    max_tokens=510
):
    """
    Read a single .txt file, pass its entire text to Kokoro's `generate`,
    and then write out a single combined audio file.
    No extra chunking is done here; chunking happens inside Kokoro.
    """

    # 1. Read the file text
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 2. (Optional) check for cancellation or pause
    if cancellation_flag and cancellation_flag():
        print("Process canceled before generating audio.")
        return

    if pause_event and not pause_event.is_set():
        pause_event.wait()

    # 3. Generate audio via Kokoro
    #    We pass `progress_callback` so Kokoro can report chunk-by-chunk progress.
    audio_chunks, phoneme_chunks = generate(
        model=model,
        text=text,
        voicepack=voicepack,
        lang='a',         # Adjust if your voice name implies a different language code
        speed=1,
        max_tokens=max_tokens,
        progress_callback=progress_callback,
        cancellation_flag = cancellation_flag
    )

    # 4. Combine all chunks into one NumPy array
    if not audio_chunks:
        print(f"No audio was generated for file: {input_path}")
        return

    combined_audio = np.concatenate(audio_chunks)

    # 5. Normalize to int16 for WAV
    normalized_audio = (combined_audio / np.max(np.abs(combined_audio)) * 32767).astype('int16')

    # 6. Save as 24 kHz WAV (adjust if your model uses a different sample rate)
    write(output_path, 24000, normalized_audio)
    print(f"Audio saved to {output_path}")


def generate_audiobooks_kokoro(
    input_dir,
    model_path,
    voicepack_path,
    output_dir=None,
    audio_format=".wav",
    progress_callback=None,
    device="cuda",
    cancellation_flag=None,
    update_estimate_callback=None,
    pause_event=None,
    max_tokens=510
):
    """
    Generate audiobooks from .txt files inside `input_dir`, using Kokoro TTS.
    """

    # 1. Validate input
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")

    # 2. Determine output directory
    if output_dir is None:
        book_name = os.path.basename(os.path.normpath(input_dir))
        output_dir = os.path.join(os.path.dirname(input_dir), f"{book_name}_audio")
    os.makedirs(output_dir, exist_ok=True)

    # 3. Get .txt files
    files = [f for f in os.listdir(input_dir) if f.lower().endswith('.txt')]
    files.sort()
    total_files = len(files)

    # 4. Load Kokoro model + voicepack
    device = device if (torch.cuda.is_available() and device == "cuda") else "cpu"
    print(f"Loading model from: {model_path} (device={device})")
    MODEL = build_model(model_path, device)

    print(f"Loading voicepack from: {voicepack_path}")
    VOICEPACK = torch.load(voicepack_path, weights_only=True).to(device)

    # 5. (Optional) measure total text length for time estimates
    total_text_length = 0
    for f in files:
        with open(os.path.join(input_dir, f), 'r', encoding='utf-8') as tempf:
            total_text_length += len(tempf.read())

    total_characters_processed = 0
    total_time_spent = 0.0

    # 6. Define an internal chunk callback for Kokoro
    def kokoro_chunk_done_callback(chars_in_chunk, chunk_duration):
        """
        Called by Kokoro for each chunk; used to track time & update estimates.
        """
        nonlocal total_characters_processed, total_time_spent

        total_characters_processed += chars_in_chunk
        total_time_spent += chunk_duration

        if update_estimate_callback and total_characters_processed > 0:
            avg_time_per_char = total_time_spent / total_characters_processed
            chars_left = total_text_length - total_characters_processed
            remaining_time = avg_time_per_char * chars_left
            update_estimate_callback(remaining_time)

    generated_files = []
    for i, text_file in enumerate(files, start=1):
        # Check for cancellation
        if cancellation_flag and cancellation_flag():
            print("Process canceled before file:", text_file)
            break

        # Basic progress (file level)
        progress_percent = int((i / total_files) * 100)
        if progress_callback:
            progress_callback(progress_percent)

        input_path = os.path.join(input_dir, text_file)
        base_name = os.path.splitext(text_file)[0]
        output_path = os.path.join(output_dir, f"{base_name}{audio_format}")

        print(f"\n=== Generating audio for: {input_path} ===")
        generate_audio_for_file_kokoro(
            input_path=input_path,
            model=MODEL,
            voicepack=VOICEPACK,
            output_path=output_path,
            device=device,
            cancellation_flag=cancellation_flag,
            progress_callback=kokoro_chunk_done_callback,  # pass chunk callback to Kokoro
            pause_event=pause_event,
            max_tokens=max_tokens
        )

        generated_files.append(output_path)

    return generated_files
