import cv2
import sounddevice as sd
import wave
import numpy as np
import time
import os
import requests
from twilio.rest import Client

# Twilio credentials for WhatsApp
account_sid = "ACc86a1e4cbcf30b45dda804d49ce51e9d"
auth_token = "48f4dafde962582fb25bc0914ff5c844"
twilio_whatsapp_number = "whatsapp:+14155238886"  # Twilio's WhatsApp sandbox number
emergency_whatsapp_number = "whatsapp:+917058972300"  # Replace with the recipient's WhatsApp number

# Parameters for audio recording
duration = 5  # Duration for audio recording in seconds
sample_rate = 44100  # in Hz
channels = 2  # Stereo

# Create the "Audio" folder if it doesn't exist
if not os.path.exists('Audio'):
    os.makedirs('Audio')

# Create the "Pictures" folder if it doesn't exist
if not os.path.exists('Pictures'):
    os.makedirs('Pictures')

# Load YOLO object detection model
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Initialize webcam
cap = cv2.VideoCapture(0)

# Variables to track image saving time
last_saved_time = time.time()  # Keep track of the last time an image was saved
image_save_interval = 5  # Time in seconds between saving images

# Function to record audio
def record_audio():
    timestamp = int(time.time())
    audio_file = f"Audio/continuous_audio_{timestamp}.wav"
    print(f"Starting audio recording to {audio_file}...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=channels, dtype='int16')
    sd.wait()
    
    with wave.open(audio_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit audio
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data.tobytes())
    
    print(f"Audio saved as {audio_file}")
    return audio_file

# Function to send image and audio to the Node.js server
def send_files_to_server(image_file, audio_file):
    url = 'http://192.168.39.112:3001/send-email'  # Replace with your Node.js server's IP address and port
    
    files = {
        'image': open(image_file, 'rb'),
        'audio': open(audio_file, 'rb')
    }
   
    try:
        response = requests.post(url, files=files)
        
        # Check the response from the server
        if response.status_code == 200:
            print("Files sent successfully!")
        else:
            print(f"Failed to send files. Status code: {response.status_code}")
            print(f"Response content: {response.content.decode()}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")


# Function to send WhatsApp message
def send_whatsapp_message():
    client = Client(account_sid, auth_token)
    try:
        message = client.messages.create(
            to=emergency_whatsapp_number,
            from_=twilio_whatsapp_number,
            body="Emergency Alert: A person has been detected. Immediate action is required."
        )
        print(f"WhatsApp message sent to {emergency_whatsapp_number}. Message SID: {message.sid}")
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Detect objects using YOLO
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Analyze detected objects
    detected = False
    image_file = None  # Default to None to ensure it's initialized
    audio_file = None  # Default to None to ensure it's initialized
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5 and class_id == 0:  # class_id 0 corresponds to 'person' in YOLO
                detected = True
                timestamp = int(time.time())
                
                # Save image only if 5 seconds have passed since the last saved image
                if time.time() - last_saved_time >= image_save_interval:
                    image_file = f"Pictures/detected_image_{timestamp}.jpg"
                    cv2.imwrite(image_file, frame)
                    last_saved_time = time.time()  # Update the last saved time
                    print(f"Person detected and image saved as {image_file}")

    # Start audio recording if a person is detected
    if detected:
        audio_file = record_audio()
        if image_file and audio_file:  # Ensure both image and audio files are defined
            send_files_to_server(image_file, audio_file)  # Send the image and audio to the Node.js server
            send_whatsapp_message()  # Send WhatsApp alert

    # Display the image in a window
    cv2.imshow("Frame", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
