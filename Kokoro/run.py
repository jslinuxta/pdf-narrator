## run.py
from models import build_model
import torch
from scipy.io.wavfile import write
import numpy as np
from kokoro import generate

# Select device
device = 'cuda' if torch.cuda.is_available() else 'cpu'

# Load the model
MODEL = build_model('kokoro-v0_19.pth', device)

# Specify the voice name
VOICE_NAME = 'af_sarah'  # Change this to the desired voice

# Load the voicepack
VOICEPACK = torch.load(f'voices/{VOICE_NAME}.pt', weights_only=True).to(device)
print(f"Loaded voice: {VOICE_NAME}")

# Read the text to synthesize from a file
input_text_file = "37_30_You_and_Your_Research.txt"  # Path to your text file
with open(input_text_file, 'r') as file:
    text = file.read()

# Generate audio
audio_chunks, phoneme_chunks = generate(MODEL, text, VOICEPACK, lang=VOICE_NAME[0])

# Combine and save the normalized audio
combined_audio = np.concatenate(audio_chunks)
normalized_audio = (combined_audio / np.max(np.abs(combined_audio)) * 32767).astype('int16')
output_path = "output_audio.wav"
write(output_path, 24000, normalized_audio)
print(f"Audio saved to {output_path}")

# Debug: Print audio stats
print("Audio waveform preview:", combined_audio[:10])  # Show the first 10 samples
print("Max amplitude:", max(combined_audio), "Min amplitude:", min(combined_audio))
print("Audio data type:", combined_audio.dtype)
