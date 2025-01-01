from Kokoro.models import build_model
import torch
from scipy.io.wavfile import write
import numpy as np
from Kokoro.kokoro import generate

# Select device
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Load the model
MODEL = build_model('/home/mateo/Desktop/PdfExtract/models/kokoro-v0_19.pth', device)

# List of voice names to generate audio for
VOICE_NAMES = ['am_adam','af_sarah','af','af_sky']  # Add desired voice names here

# Read the text to synthesize from a file
input_text_file = "/home/mateo/Desktop/PdfExtract/test_text.txt"  # Path to your text file
with open(input_text_file, 'r') as file:
    text = file.read()

# Loop through each voice and generate audio
for voice_name in VOICE_NAMES:
    try:
        # Load the voicepack
        voicepack_path = f'Kokoro/voices/{voice_name}.pt'
        VOICEPACK = torch.load(voicepack_path, weights_only=True).to(device)
        print(f"Loaded voice: {voice_name}")

        # Generate audio
        audio_chunks, phoneme_chunks = generate(MODEL, text, VOICEPACK, lang=voice_name[0])

        # Combine and save the normalized audio
        combined_audio = np.concatenate(audio_chunks)
        normalized_audio = (combined_audio / np.max(np.abs(combined_audio)) * 32767).astype('int16')
        output_path = f"output_audio_{voice_name}.wav"
        write(output_path, 24000, normalized_audio)
        print(f"Audio saved to {output_path}")

        # Debug: Print audio stats
        print(f"Audio stats for {voice_name}:")
        print("  Audio waveform preview:", combined_audio[:10])  # Show the first 10 samples
        print("  Max amplitude:", max(combined_audio), "Min amplitude:", min(combined_audio))
        print("  Audio data type:", combined_audio.dtype)

    except Exception as e:
        print(f"Failed to generate audio for {voice_name}: {e}")
