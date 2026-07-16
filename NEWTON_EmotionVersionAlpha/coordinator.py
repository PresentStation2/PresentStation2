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

'''import serial'''
import time
from sound import play_sound

app = FastAPI()

categorized_values = []

'''real_time_categories = ['idle', 'meanF0','happy']'''

dataPath = sys.argv[1]
logName = os.path.join(os.path.split(dataPath)[0], 'featureExtractor.log')

is_recording = False
'''rolling_buffer = deque(maxlen=32000 * 40)'''
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

'''def buffer_analyzer(duration):
    #start_time=time.time()
    #end_time=start_time+duration
    
    global rolling_buffer, buffer_lock, is_recording, real_time_categories
    ser = serial.Serial(port ='/dev/ttyACM0', baudrate=115200)
    serf = serial.Serial(port ='/dev/ttyUSB0', baudrate=115200)
    ser.write(f"timer stop\n".encode())
    ser.write(f"timer {duration}\n".encode())
    ser.write(f"body average\n".encode()) #body in initialization
    serf.write(f"good\n".encode()) #face initialization
    #play sounds for start
    play_sound('/home/pi/Machine-Learning-AGS/NEWTON_EmotionVersionAlpha/sounds/level-win.wav')
    time.sleep(3)
    play_sound('/home/pi/Machine-Learning-AGS/NEWTON_EmotionVersionAlpha/sounds/race-start-beeps.wav')
    ser.write(f"tracking on\n".encode()) #position tracking
    ser.write("timer start\n".encode())
    current_category = "average"
    time.sleep(25)
    amount_loops=int((duration-40)/15)
    remainder=duration %20
    while amount_loops>0:
        #time.sleep(15)
        amount_loops=amount_loops-1
   # while time.time()<end_time:
        time.sleep(20)
        with buffer_lock:
            buffer_array = np.array(rolling_buffer, dtype=np.int16)
        print("Processing now start")
        try:    
            features_buffer = ProcessSingleFile(buffer_array, logName, 'FE_Setup.json') #import ml module and call ml function here if im correct on buffer_array
        except:
            ser.write(f"body idle\n".encode()) #body set to idle
            serf.write(f"good\n".encode()) #face set to happy

        cat = Categorize(features_buffer, 1)
        real_time_categories[0]=cat[1] #color
        real_time_categories[1]=cat[2] #face
        real_time_categories[2]=cat[3] #icon
        
        body = real_time_categories[0]
        face = real_time_categories[1]
        icon = real_time_categories[2]
        serf.write(f"{face}\n".encode()) #face
        ser.write(f"icon {icon}\n".encode()) #icon
        ser.write(f"body {body}\n".encode()) #body
        print({face},{body},{icon})

        #Nodding
        if current_category == "extreme" and body == "average":
            #Nodding yes
            ser.write(f"nod\n".encode())
        if current_category == "extreme" and body == "good":
            #Nodding yes
            ser.write(f"nod\n".encode())
        if current_category == "average" and body == "good":
            #Nodding yes
            ser.write(f"nod\n".encode())

        current_category = body

        for i in features_buffer:
            print('Buffer value: ', i)
        print("Processing now end")
        
    time.sleep(remainder)
    ser.write(f"tracking off\n".encode()) #position tracking

    
    ser.write(f"body idle\n".encode()) #body set to idle
    serf.write(f"good\n".encode()) #face set to happy
'''

def record_audio(duration, user_id):
    global is_recording, rolling_buffer, full_recording, buffer_lock, categorized_values
    is_recording = True
    with buffer_lock:
        '''full_recording.clear()
        rolling_buffer.clear()'''

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
        
        '''worker=threading.Thread(target=buffer_analyzer, args=(duration,), daemon=True)
        worker.start()'''
        
        time.sleep(10)
        
        start_time = time.time()
        #end_time=start_time+duration
        while time.time() - start_time < duration:
        #while end_time<time.time():
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_chunk = np.frombuffer(data, dtype=np.int16)
            with buffer_lock:
                full_recording.extend(audio_chunk)
                #rolling_buffer.extend(audio_chunk)
        # Save full recording
        with buffer_lock:
            full_array = np.array(full_recording, dtype=np.int16)
        print("Recording finished and saved")
        #play_sound('/home/pi/Machine-Learning-AGS/NEWTON_EmotionVersionAlpha/sounds/applause.wav')
        
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        if p is not None: 
            p.terminate()
        is_recording = False
    '''worker.join()'''

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

     # Save 40-second buffer
    #with buffer_lock:
       #buffer_array = np.array(rolling_buffer, dtype=np.int16)

    #print("Recording finished and saved")

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