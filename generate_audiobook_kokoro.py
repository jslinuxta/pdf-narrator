import os
import time
import numpy as np
import torch
import soundfile as sf  # new: using soundfile instead of scipy.io.wavfile.write
from kokoro import KPipeline

def generate_audio_for_file_kokoro(
    input_path,
    pipeline,         # a KPipeline instance (initialized with the proper lang_code)
    voice,            # e.g. "af_heart"
    output_path,
    speed=1,
    split_pattern=r'\n+',
    cancellation_flag=None,
    progress_callback=None,
    pause_event=None
):
    # 1. Read the text file
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    if cancellation_flag and cancellation_flag():
        print("Process canceled before generating audio.")
        return

    if pause_event and not pause_event.is_set():
        pause_event.wait()

    audio_chunks = []
    # 2. Generate audio chunks using the new KPipeline call
    #    (each iteration yields: graphemes, phonemes, audio)
    #    Optionally, you can time each chunk to update progress.
    start_chunk = time.time()
    for chunk_index, (gs, ps, audio) in enumerate(pipeline(text, voice=voice, speed=speed, split_pattern=split_pattern)):
        if cancellation_flag and cancellation_flag():
            print("Process canceled during audio generation.")
            break
        if pause_event and not pause_event.is_set():
            pause_event.wait()

        # (Optional) measure chunk time for progress estimation
        chunk_duration = time.time() - start_chunk
        start_chunk = time.time()
        chars_in_chunk = len(gs)
        if progress_callback:
            progress_callback(chars_in_chunk, chunk_duration)
        # Convert to numpy if needed
        if isinstance(audio, torch.Tensor):
            audio = audio.cpu().numpy()
        audio_chunks.append(audio)

    if not audio_chunks:
        print(f"No audio was generated for file: {input_path}")
        return

    # 3. Concatenate and normalize to int16 (sample rate is assumed 24000)
    combined_audio = np.concatenate(audio_chunks)
    normalized_audio = (combined_audio / np.max(np.abs(combined_audio)) * 32767).astype(np.int16)
    sf.write(output_path, normalized_audio, 24000)
    print(f"Audio saved to {output_path}")


def generate_audiobooks_kokoro(
    input_dir,
    lang_code,        # language code for the pipeline (e.g. 'a' for American English)
    voice,            # voice to use (e.g. "af_heart")
    output_dir=None,
    audio_format=".wav",
    speed=1,
    split_pattern=r'\n+',
    progress_callback=None,         # receives progress updates (e.g. percentage)
    cancellation_flag=None,
    update_estimate_callback=None,    # receives time-estimate updates (optional)
    pause_event=None,
    file_callback=None
):
    print(f"Input directory: {input_dir}")
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")

    # Determine output directory if not provided
    if output_dir is None:
        book_name = os.path.basename(os.path.normpath(input_dir))
        output_dir = os.path.join(os.path.dirname(input_dir), f"{book_name}_audio")
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    # Gather .txt files and sort them
    files = sorted(f for f in os.listdir(input_dir) if f.lower().endswith('.txt'))
    total_files = len(files)

    # Initialize a KPipeline for the target language
    pipeline = KPipeline(lang_code=lang_code)

    # (Optional) Pre-calculate total text length for timing estimates
    total_text_length = 0
    for f in files:
        with open(os.path.join(input_dir, f), 'r', encoding='utf-8') as tempf:
            total_text_length += len(tempf.read())
    print(f"Files to process: {total_files}, Total text length: {total_text_length} characters")
    total_characters_processed = 0
    total_time_spent = 0.0
    recent_times = []

    def chunk_progress_callback(chars_in_chunk, chunk_duration):
        nonlocal total_characters_processed, total_time_spent
        if chars_in_chunk <= 0:
            return

        total_characters_processed += chars_in_chunk
        total_time_spent += chunk_duration

        # Avoid division by zero
        if total_characters_processed == 0:
            return

        # Calculate average time per character
        avg_time_per_char = total_time_spent / total_characters_processed

        # Estimate total time for processing the entire text
        estimated_total_time = avg_time_per_char * total_text_length

        # Calculate remaining time (make sure it's not negative)
        remaining_time = max(0, estimated_total_time - total_time_spent)

        # Optionally, you can smooth this value using a low-pass filter if it's still too jumpy.
        if update_estimate_callback:
            update_estimate_callback(max(1, int(remaining_time)))


    print("=== Starting audiobook generation ===")
    generated_files = []
    for i, text_file in enumerate(files, start=1):
        if cancellation_flag and cancellation_flag():
            print("Process canceled before file:", text_file)
            break

        print(f"\n=== Processing file {i}/{total_files}: {text_file} ===")
        if progress_callback:
            progress_callback(int((i / total_files) * 100))
        input_path = os.path.join(input_dir, text_file)
        if file_callback:
            file_callback(f"Processing chapter: {text_file}", i, total_files)
        base_name = os.path.splitext(text_file)[0]
        output_path = os.path.join(output_dir, f"{base_name}{audio_format}")
        print(f"Generating audio for: {input_path}")
        print(f"Output file: {output_path}")

        start_time = time.time()
        generate_audio_for_file_kokoro(
            input_path=input_path,
            pipeline=pipeline,
            voice=voice,
            output_path=output_path,
            speed=speed,
            split_pattern=split_pattern,
            cancellation_flag=cancellation_flag,
            progress_callback=chunk_progress_callback,
            pause_event=pause_event
        )
        elapsed = time.time() - start_time
        print(f"Processed {text_file} in {elapsed:.2f} seconds.")
        generated_files.append(output_path)

    return generated_files

def generate_audio_for_all_voices_kokoro(
    input_path,
    lang_code,
    voices,
    output_dir,
    speed=1,
    split_pattern=r'\n+',
    cancellation_flag=lambda: False,
    progress_callback=None,
    pause_event=None
):
    """
    Generate audio samples for all specified voices from the input text file.
    This function loops over each voice, generating an audio file in the output directory.
    """
    import os
    from kokoro import KPipeline

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize pipeline only once
    pipeline = KPipeline(lang_code=lang_code)
    
    total_voices = len(voices)
    for i, voice in enumerate(voices, start=1):
        print(f"Generating audio for voice: {voice} ({i}/{total_voices})")
        # Define output file for this voice
        output_file = os.path.join(output_dir, f"test_{voice}.wav")
        
        # Generate audio for this voice using your existing function
        generate_audio_for_file_kokoro(
            input_path=input_path,
            pipeline=pipeline,
            voice=voice,
            output_path=output_file,
            speed=speed,
            split_pattern=split_pattern,
            cancellation_flag=cancellation_flag,
            progress_callback=progress_callback,
            pause_event=pause_event
        )
        # Optionally update progress based on voice count
        if progress_callback:
            progress_callback((i / total_voices) * 100)
            
    print("Completed audio generation for all voices.")
