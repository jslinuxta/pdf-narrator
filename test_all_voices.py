import os
import time
from kokoro import KPipeline
from generate_audiobook_kokoro import generate_audio_for_file_kokoro

# Custom text to use for TTS
custom_text = """There is no individual or collective identity that does not take into account one’s connection to those who create us, the source from which we emerged.
"""

# Create a test input file
input_dir = "test_input_kokoro"
os.makedirs(input_dir, exist_ok=True)
input_file = os.path.join(input_dir, "custom.txt")
with open(input_file, "w", encoding="utf-8") as f:
    f.write(custom_text)

# Define all the voices to test
voices = [
    "af_heart", "af_alloy", "af_aoede", "af_bella", "af_jessica",
    "af_kore", "af_nicole", "af_nova", "af_river", "af_sarah", "af_sky",
    "am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael",
    "am_onyx", "am_puck", "am_santa",
    "bf_alice", "bf_emma", "bf_isabella", "bf_lily",
    "bm_daniel", "bm_fable", "bm_george", "bm_lewis"
]

# Create an output directory for generated audio files
output_dir = "test_output_kokoro"
os.makedirs(output_dir, exist_ok=True)

# Initialize the KPipeline for the target language.
# (Here we use lang_code "a" – adjust if needed for your model.)
pipeline = KPipeline(lang_code="a")

# Loop over each voice and generate audio
for voice in voices:
    print(f"\nGenerating audio for voice: {voice}")
    output_file = os.path.join(output_dir, f"output_{voice}.wav")
    generate_audio_for_file_kokoro(
        input_path=input_file,
        pipeline=pipeline,
        voice=voice,
        output_path=output_file,
        speed=1,
        split_pattern=r'\n+',
        cancellation_flag=lambda: False,
        progress_callback=None,
        pause_event=None
    )
    print(f"Audio generated: {output_file}")
    time.sleep(1)
