# generate_audiobook.py
import os
import subprocess
import re
import shutil
import time

DEFAULT_TARGET_DURATION = 65  # 1 minute and 5 seconds

# Default voice configs if no speakers are provided
VOICE_CONFIGS = [
    {"id": 380, "length_scale": DEFAULT_TARGET_DURATION/52},
    {"id": 275, "length_scale": DEFAULT_TARGET_DURATION/68},
    {"id": 181, "length_scale": DEFAULT_TARGET_DURATION/79},
    {"id": 859, "length_scale": DEFAULT_TARGET_DURATION/77},
    {"id": 868, "length_scale": DEFAULT_TARGET_DURATION/67},
    {"id": 8, "length_scale": DEFAULT_TARGET_DURATION/63},
]



def split_text_smart(text, chunk_size):
    if len(text) <= chunk_size:
        return [text]

    hierarchy = [
        r'\n\n',
        r'\.\n',
        r'\.',
        r',',
        r':',
        r'\n',
        r' '
    ]

    for pattern in hierarchy:
        split_points = [m.start() for m in re.finditer(pattern, text)]
        split_points = [p for p in split_points if p < chunk_size]

        if split_points:
            cut_point = split_points[-1] + 1
            return [text[:cut_point].strip()] + split_text_smart(text[cut_point:].strip(), chunk_size)

    backtrack_point = text.rfind(' ', 0, chunk_size)
    if backtrack_point == -1:
        backtrack_point = chunk_size
    return [text[:backtrack_point].strip()] + split_text_smart(text[backtrack_point:].strip(), chunk_size)

def generate_audio_chunk(chunk, model_path, output_path, speaker=None, length_scale=1.0, device="cuda"):
    # Build command
    cmd = f'echo "{chunk}" | piper --model "{model_path}" --output_file "{output_path}" --{device} --length-scale {length_scale}'
    if speaker is not None:
        cmd += f' --speaker {speaker}'

    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to process chunk. Error: {e}")
        return False

def generate_audiobooks(input_dir, model_path, speaker_ids=None, chunk_size=2500, audio_format=".wav", output_dir=None, progress_callback=None, device="cuda", cancellation_flag=None, update_estimate_callback=None, pause_event=None):
    """
    Generate audiobook from text files in input_dir.
    :param input_dir: Directory containing .txt files.
    :param model_path: Path to the TTS model (.onnx file).
    :param speaker_ids: List of speaker IDs or empty for no speaker param.
    :param chunk_size: Maximum characters per chunk.
    :param audio_format: ".wav" or ".mp3"
    :param output_dir: Directory to store generated audiobook files.
    :return: List of generated audio file paths.
    """
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory '{input_dir}' does not exist.")
    
    if output_dir is None:
        book_name = os.path.basename(os.path.normpath(input_dir))
        output_dir = os.path.join(os.path.dirname(input_dir), f"{book_name}_audio")
        os.makedirs(output_dir, exist_ok=True)

    files = [f for f in os.listdir(input_dir) if f.lower().endswith('.txt')]
    files.sort()
    
    # Calculate total text length
    total_text_length = 0
    for f in files:
        with open(os.path.join(input_dir, f), 'r', encoding='utf-8') as tempf:
            total_text_length += len(tempf.read())
    
    total_characters_processed = 0
    total_time_spent = 0.0

    recent_times = []

    def chunk_done_callback(chars_in_chunk, chunk_duration):
        nonlocal total_characters_processed, total_time_spent, recent_times

        # Update totals
        total_characters_processed += chars_in_chunk
        total_time_spent += chunk_duration

        # Update sliding window of recent times
        recent_times.append(chunk_duration / chars_in_chunk)
        if len(recent_times) > 5:  # Keep only the last 5 records
            recent_times.pop(0)

        # Weighted average of recent and overall averages
        recent_avg_time_per_char = sum(recent_times) / len(recent_times)
        overall_avg_time_per_char = total_time_spent / total_characters_processed
        weighted_avg_time_per_char = (recent_avg_time_per_char * 0.7 + overall_avg_time_per_char * 0.3)

        # Estimate remaining time
        chars_left = total_text_length - total_characters_processed
        remaining_time = weighted_avg_time_per_char * chars_left

        # Clamp remaining time to avoid premature zero
        remaining_time = max(remaining_time, weighted_avg_time_per_char * 100)

        # Pass updated time to the callback
        if update_estimate_callback:
            update_estimate_callback(remaining_time)

    total_files = len(files)
    generated_files = []
    file_counter = 1

    for text_file in files:
        if cancellation_flag and cancellation_flag():
            print("Process canceled before file:", text_file)
            break

        progress = int((file_counter / total_files) * 100)
        if progress_callback:
            progress_callback(progress)

        input_path = os.path.join(input_dir, text_file)
        base_name = os.path.splitext(text_file)[0]
        output_path = os.path.join(output_dir, f"{base_name}{audio_format}")

        print(f"Processing file: {input_path}")
        generate_audio_for_file(input_path, model_path, output_path, chunk_size, speaker_ids, device, cancellation_flag, chunk_done_callback, pause_event)
        generated_files.append(output_path)
        file_counter += 1

    return generated_files

def combine_audio_files(temp_dir, output_path, audio_format=".wav"):
    """
    Combines multiple audio chunks into a single output file.
    :param temp_dir: Directory containing temporary audio chunks.
    :param output_path: Path to the final output file.
    :param audio_format: Desired output format (e.g., ".wav").
    """
    input_file_list = os.path.join(temp_dir, "file_list.txt")
    with open(input_file_list, 'w') as file_list:
        for chunk_file in sorted(os.listdir(temp_dir)):
            if chunk_file.endswith(".wav"):  # Add only WAV files to the list
                chunk_file_path = os.path.join(temp_dir, chunk_file)
                file_list.write(f"file '{chunk_file_path}'\n")

    if audio_format == ".mp3":
        cmd_combine = (
            f'ffmpeg -y -f concat -safe 0 -i "{input_file_list}" '
            f'-vn -ar 44100 -ac 2 -b:a 192k "{output_path}"'
        )
    else:
        # Default to WAV if no transcoding is needed
        cmd_combine = (
            f'ffmpeg -y -f concat -safe 0 -i "{input_file_list}" '
            f'-c copy "{output_path}"'
        )

    print(f"Combining chunks into {output_path}")
    try:
        subprocess.run(cmd_combine, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to combine audio files. Error: {e}")
        raise


def generate_audio_for_file(input_path, model_path, output_path, chunk_size=2500, speaker_ids=None, device="cuda", cancellation_flag=None, chunk_done_callback=None, pause_event=None):
    temp_dir = os.path.join(os.path.dirname(output_path), "temp_chunks")
    os.makedirs(temp_dir, exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as file:
        text = file.read()

    chunks = split_text_smart(text, chunk_size)
    voice_index = 0
    use_default_voices = (speaker_ids is None or len(speaker_ids) == 0)

    for idx, chunk in enumerate(chunks):
        if cancellation_flag and cancellation_flag():
            print("Process canceled during chunk processing.")
            return
        if pause_event and not pause_event.is_set():
            pause_event.wait()  # Wait until the process is resumed
        if use_default_voices:
            voice = VOICE_CONFIGS[voice_index]
            length_scale = voice["length_scale"]
            speaker = voice["id"]
        else:
            speaker = speaker_ids[idx % len(speaker_ids)]
            length_scale = 1.0

        chunk_output_path = os.path.join(temp_dir, f"chunk_{idx + 1}.wav")
        print(f"Processing chunk {idx + 1}/{len(chunks)} with speaker {speaker}, length_scale {length_scale}, device {device}")

        chunk_start_time = time.time()
        success = generate_audio_chunk(chunk, model_path, chunk_output_path, speaker=speaker, length_scale=length_scale, device=device)
        chunk_end_time = time.time()
        if success and chunk_done_callback:
            chunk_done_callback(len(chunk), chunk_end_time - chunk_start_time)

        if use_default_voices:
            voice_index = (voice_index + 1) % len(VOICE_CONFIGS)

    try:
        combine_audio_files(temp_dir, output_path, os.path.splitext(output_path)[1])
    except Exception as e:
        print(f"Failed to combine audio files. Error: {e}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    print(f"Audio generation complete: {output_path}")
