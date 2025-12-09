from fastapi import FastAPI
import threading
import pyaudio
import wave
import time
import numpy as np
import requests
from collections import deque
from FeatureExtractor import ProcessSingleFile
import os
import sys
from Categorizer import Categorize
import serial
import time

app = FastAPI()

categorized_values = []
real_time_categories = []

dataPath = sys.argv[1]
logName = os.path.join(os.path.split(dataPath)[0], 'featureExtractor.log')

is_recording = False
rolling_buffer = deque(maxlen=32000 * 40)
full_recording = deque()
buffer_lock = threading.Lock()

def send_data_back_to_laravel(data):
    url = "http://127.0.0.1:8000/api/save-to-db"
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, json=data)
        print("Data sent to Laravel successfully", data)
        print("URL:", url)
        print("Status code:", response.status_code)
        #print("Raw response:", response.json())
    except Exception as e:
        print("Error sending data to Laravel:", e)

def buffer_analyzer():
    global rolling_buffer, buffer_lock, is_recording, real_time_categories
    time.sleep(40)
    while is_recording:

        with buffer_lock:
            buffer_array = np.array(rolling_buffer, dtype=np.int16)
        print("Processing now start")
        features_buffer = ProcessSingleFile(buffer_array, logName, 'FE_Setup.json') #import ml module and call ml function here if im correct on buffer_array
        cat = Categorize(features_buffer, 1)
        real_time_categories.append(cat[1])
        real_time_categories.append(cat[2])
        real_time_categories.append(cat[3])
        #ser = serial.Serial(port ='/dev/ttyUSB0', baudrate=9600, timeout=1)
        #time.sleep(2) 
        #ser.write(f'C{real_time_categories[0]}\n'.encode())
        for i in features_buffer:
            print('Buffer value: ', i)
        print("Processing now end")
        time.sleep(20)

def record_audio(duration, user_id):
    global is_recording, rolling_buffer, full_recording, buffer_lock, categorized_values
    is_recording = True
    with buffer_lock:
        full_recording.clear()
        rolling_buffer.clear()

    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 32000
    BUFFER_SECONDS = 40
    
    BUFFER_SIZE = RATE * BUFFER_SECONDS
    BUFFER_SIZE = (BUFFER_SIZE // CHUNK) * CHUNK

    stream = None
    p = None
    try:
        p = pyaudio.PyAudio()

        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)
        
        threading.Thread(target=buffer_analyzer, daemon=True).start()

        start_time = time.time()
        while time.time() - start_time < duration+10:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_chunk = np.frombuffer(data, dtype=np.int16)
            with buffer_lock:
                full_recording.extend(audio_chunk)
                rolling_buffer.extend(audio_chunk)
        # Save full recording
        with buffer_lock:
            full_array = np.array(full_recording, dtype=np.int16)
        print("Processing now start")
        features_full = ProcessSingleFile(full_array, logName, 'FE_Setup.json') #import ml module and call ml function here if im correct on full_array
        for i in features_full:
            print('Full value: ', i)
        durationMinutes = float(duration / 60)
        categorized_values = Categorize(features_full, durationMinutes)
        categorized_values[0]['user_id'] = user_id
        web_categories = categorized_values[0]
        for i in features_full:
            print('Full value: ', i)
        print("Processing now end")

        wf_full = wave.open("full_audio.wav", 'wb')
        wf_full.setnchannels(CHANNELS)
        wf_full.setsampwidth(p.get_sample_size(FORMAT))
        wf_full.setframerate(RATE)
        wf_full.writeframes(full_array.tobytes())
        wf_full.close()

        # Save 40-second buffer
        with buffer_lock:
            buffer_array = np.array(rolling_buffer, dtype=np.int16)
        wf_buffer = wave.open("buffer_audio.wav", 'wb')
        wf_buffer.setnchannels(CHANNELS)
        wf_buffer.setsampwidth(p.get_sample_size(FORMAT))
        wf_buffer.setframerate(RATE)
        wf_buffer.writeframes(buffer_array.tobytes())
        wf_buffer.close()

        print("Recording finished and saved")

    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if p is not None: 
            p.terminate()
        is_recording = False


    # Send callback to Laravel
    send_data_back_to_laravel(web_categories)

@app.post("/start-recording")
def start_recording(data: dict):
    global is_recording
    if is_recording:
        return {"error": "Recording already in progress"}
    if not is_recording:
        duration = int(data["duration"])
        user_id = data["user_id"]
        threading.Thread(target=record_audio, args=(duration,user_id), daemon=True).start()
        return {"status": is_recording, "duration": duration}