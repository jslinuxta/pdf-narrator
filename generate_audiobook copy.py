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

def generate_audio_for_file(input_path, model_path, output_path, chunk_size=2500, speaker_ids=None, device="cuda",cancellation_flag=None, total_text_length=0, characters_processed=0, total_processing_time=0.0,update_estimate_callback=None, pause_event=None):
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
    temp_dir = os.path.join(os.path.dirname(output_path), "temp_chunks")
    os.makedirs(temp_dir, exist_ok=True)

    with open(input_path, 'r', encoding='utf-8') as file:
        text = file.read()

    chunks = split_text_smart(text, chunk_size)

    use_default_voices = (speaker_ids is None or len(speaker_ids) == 0)
    voice_index = 0

    file_characters_processed = 0
    file_processing_time = 0.0

    for idx, chunk in enumerate(chunks):
        if cancellation_flag and cancellation_flag():
            print("Process canceled during chunk processing.")
            break
        if pause_event and not pause_event.is_set():
            pause_event.wait()  # Wait until the process is resumed

        chunk_start_time = time.time()

        # Determine speaker and length_scale
        if use_default_voices:
            voice = VOICE_CONFIGS[voice_index]
            length_scale = voice["length_scale"]
            speaker = voice["id"]
        else:
            speaker = speaker_ids[idx % len(speaker_ids)]
            length_scale = 1.0

        chunk_output_path = os.path.join(temp_dir, f"chunk_{idx + 1}.wav")
        print(f"Processing chunk {idx + 1}/{len(chunks)}")

        success = generate_audio_chunk(chunk, model_path, chunk_output_path, speaker=speaker, length_scale=length_scale, device=device)
        chunk_end_time = time.time()

        if success:
            # Update timing and character counters
            chunk_duration = chunk_end_time - chunk_start_time
            file_processing_time += chunk_duration
            file_characters_processed += len(chunk)

            # Update global counters for estimation
            characters_processed += len(chunk)
            total_processing_time += chunk_duration

            # Estimate remaining time
            avg_time_per_character = total_processing_time / characters_processed
            characters_left = total_text_length - characters_processed
            estimated_remaining = avg_time_per_character * characters_left

            if update_estimate_callback:
                update_estimate_callback(estimated_remaining)

        if use_default_voices:
            voice_index = (voice_index + 1) % len(VOICE_CONFIGS)

    # Combine chunks into final output
    combine_start = time.time()
    combine_audio_files(temp_dir, output_path, os.path.splitext(output_path)[1])
    combine_end = time.time()

    file_processing_time += (combine_end - combine_start)

    print(f"Finished file '{input_path}' with {file_characters_processed} characters processed in {int(file_processing_time)} seconds.")
    return file_characters_processed, file_processing_time
def combine_audio_files(temp_dir, output_path, audio_format=".mp3"):
    """
    Combines multiple audio chunks into a single output file.
    :param temp_dir: Directory containing temporary audio chunks.
    :param output_path: Path to the final output file.
    :param audio_format: Desired output format (e.g., ".mp3").
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

