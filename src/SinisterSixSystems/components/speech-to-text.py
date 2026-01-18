from faster_whisper import WhisperModel

class FasterWhisperCTranslate2ASR:
    def __init__(self, model_size="large-v2", device="cpu"):
        """
        model_size: model name from HuggingFace ("large-v2", "medium", etc.)
        device: "cuda" or "cpu"
        """
        # Load the model with CTranslate2 backend automatically
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type="float32"  # quantized for efficiency
        )

    def transcribe(self, audio_path):
        segments, info = self.model.transcribe(audio_path)
        text = ""
        for segment in segments:
            text += segment.text + " "
        return text.strip()

# ---------------- Example Usage ----------------
if __name__ == "__main__":
    audio_file = "/kaggle/input/audio2/B1-Track 12.3.wav"

    asr = FasterWhisperCTranslate2ASR(model_size="large-v2", device="cpu")
    transcription = asr.transcribe(audio_file)
    print("Transcription:\n", transcription)
