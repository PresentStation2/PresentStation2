import numpy as np
import pyaudio
from collections import deque
import threading
import wave
import io
import time
from collections import deque


class AudioRecorderRAM:
    """
    Standalone version of AudioRecorderRAM.
    Records audio continuously into RAM and provides:
      • get_buffer_as_numpy()
      • get_buffer_as_wav_bytes()
      • save_to_wav()
    """

    def __init__(self, sample_rate=44100, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = 1

        max_samples = sample_rate * 40  # 50-second rolling buffer
        self.audio_buffer = deque(maxlen=max_samples)

        self.recording = False
        self.lock = threading.Lock()

        self.p = pyaudio.PyAudio()
        self.stream = None

    def start(self):
        """Start microphone input."""
        print("Starting microphone...")
        self.recording = True

        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        print("Microphone active!")

    def record_chunk(self):
        """Read one chunk from the mic and store it in RAM."""
        if not self.recording or not self.stream:
            return False

        try:
            audio_chunk = self.stream.read(
                self.chunk_size,
                exception_on_overflow=False
            )
            audio_array = np.frombuffer(audio_chunk, dtype=np.int16)

            with self.lock:
                self.audio_buffer.extend(audio_array)

            return True

        except Exception as e:
            print("Recording error:", e)
            return False

    def stop(self):
        """Stop microphone and clean up."""
        print("Stopping microphone...")
        self.recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.p.terminate()
        print("Microphone stopped.")

    def get_buffer_as_numpy(self):
        """Return buffer as normalized float32 array (-1 to 1)."""
        with self.lock:
            audio_np = np.array(self.audio_buffer, dtype=np.int16)

        return audio_np.astype(np.float32) / 32768.0

    def get_buffer_as_wav_bytes(self):
        """Return the buffer as in-memory .wav file bytes."""
        with self.lock:
            audio_data = np.array(self.audio_buffer, dtype=np.int16)

        wav_io = io.BytesIO()

        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        wav_io.seek(0)
        return wav_io

    def save_to_wav(self, filename="output.wav"):
        """Save the current buffer to a real .wav file."""
        with self.lock:
            audio_data = np.array(self.audio_buffer, dtype=np.int16)

        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        print(f"Saved {len(audio_data)} samples to {filename}")

if __name__ == "__main__":
    recorder = AudioRecorderRAM()

    recorder.start()
    print("Recording 40 seconds...")
    start = time.time()
    while time.time() - start < 40:
        recorder.record_chunk()
    recorder.stop()

    # Save the wav
    recorder.save_to_wav("test_output.wav")

    # Check numpy buffer
    buf = recorder.get_buffer_as_numpy()
    print("Buffer shape:", buf.shape)

