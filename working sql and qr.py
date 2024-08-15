import cv2
from pyzbar.pyzbar import decode
import pyttsx3
import datetime
import speech_recognition as sr
import os
from PIL import Image
import numpy as np
import time
import mysql.connector

# Initialize text-to-speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def speak(audio):
    """Convert text to speech."""
    engine.say(audio)
    engine.runAndWait()

def wish_me():
    """Greet the user based on the time of day."""
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")
    speak("I'm ADA, your library assistant")

def take_command():
    """Listen to user voice commands and return the recognized text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source, timeout=5)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        # Remove unwanted prefix from the query
        if 'result2:' in query:
            query = query.replace("result2:", "").strip()
    except Exception as e:
        print(e)
        print("Unable to Recognize your voice.")
        return "None"
    return query

def process_frame(frame):
    """Process each frame to detect and decode barcodes."""
    try:
        # Convert the frame from BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert the RGB frame to a PIL image
        pil_image = Image.fromarray(rgb_frame)
        # Decode barcodes in the PIL image
        barcodes = decode(pil_image)
        return barcodes
    except Exception as e:
        print(f"Error processing frame: {e}")
        return []

def load_used_barcodes(file_path):
    """Load used barcodes from a file."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return set(line.strip() for line in file)
        return set()
    except Exception as e:
        print(f"Error loading used barcodes: {e}")
        return set()

def save_used_barcodes(file_path, used_barcodes):
    """Save used barcodes to a file."""
    try:
        with open(file_path, 'w') as file:
            for barcode in used_barcodes:
                file.write(f"{barcode}\n")
    except Exception as e:
        print(f"Error saving used barcodes: {e}")

def connect_to_database(host, user, password, database):
    """Connect to the existing MySQL database."""
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return conn
    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")
        speak("Unable to connect to the database.")
        return None

def sign_in(conn, barcode_data, name):
    """Sign in a new user with barcode and name."""
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO qr (barcode, name) VALUES (%s, %s)", (barcode_data, name))
        conn.commit()
        speak(f"Sign-in successful. Welcome, {name}.")
    except mysql.connector.IntegrityError:
        speak("This ID is already registered.")
    except Exception as e:
        print(f"Error during sign-in: {e}")
        speak("An error occurred during sign-in.")

def log_in(conn, barcode_data):
    """Log in an existing user based on barcode."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM qr WHERE barcode = %s", (barcode_data,))
        result = cursor.fetchone()
        if result:
            speak(f"Welcome back, {result[0]}.")
        else:
            speak("Barcode not recognized. Please sign in first.")
    except Exception as e:
        print(f"Error during log-in: {e}")
        speak("An error occurred during log-in.")

def manual_sign_in(conn):
    """Manually sign in by typing ID and name."""
    barcode_data = input("Enter your ID: ")
    name = input("Enter your name: ")
    sign_in(conn, barcode_data, name)

def manual_log_in(conn):
    """Manually log in by typing ID."""
    barcode_data = input("Enter your ID: ")
    log_in(conn, barcode_data)

def main_library_system(db_config, camera_index=3):
    """Main function to handle library system operations."""
    try:
        time.sleep(2)
        speak('Hi, I\'m ADA, your automated library assistant. Please say "sign in", "log in", or "manual" to continue.')
        query = take_command()

        conn = connect_to_database(**db_config)
        if conn is None:
            return
        if 'sign in' in query:
            speak("Please show your ID.")
            time.sleep(2)
             
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            cap.set(3, 640)  # Set width
            cap.set(4, 480)  # Set height
            if not cap.isOpened():
                speak("Sorry, the camera couldn't be opened. Please check your camera.")
                return
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    speak("Failed to capture image. Check camera functionality.")
                    return

                barcodes = process_frame(frame)
                if barcodes:
                    barcode_data = barcodes[0].data.decode('utf-8')
                    speak("Please state your name.")
                    name = take_command().title()
                    sign_in(conn, barcode_data, name)
                    break

                cv2.imshow('Barcode Scanner', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cap.release()
            cv2.destroyAllWindows()

        elif 'log in' in query or 'login' in query:
            speak("Please show your ID.")
            time.sleep(2)
            
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            cap.set(3, 640)  # Set width
            cap.set(4, 480)  # Set height

            if not cap.isOpened():
                speak("Sorry, the camera couldn't be opened. Please check your camera.")
                return
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    speak("Failed to capture image. Check camera functionality.")
                    return

                barcodes = process_frame(frame)
                if barcodes:
                    barcode_data = barcodes[0].data.decode('utf-8')
                    log_in(conn, barcode_data)
                    break

                cv2.imshow('Barcode Scanner', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()
        
        elif 'manual' in query:
            speak("Please choose 'sign in' or 'log in' by typing.")
            manual_query = input("Type 'sign in' or 'log in': ").lower()
            if 'sign in' in manual_query:
                manual_sign_in(conn)
            elif 'log in' in manual_query:
                manual_log_in(conn)
            else:
                speak("Invalid input. Please try again.")
        
        else:
            speak("Command not recognized. Please try again.")
        
        conn.close()

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        speak("An unexpected error occurred. Please try again.")

if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    
    # Database connection configuration
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'studentqr'
    }
    
    while True:
        main_library_system(db_config)
        
        speak("Do you want to start another session? Say 'yes' to continue or 'no' to exit.")
        response = take_command().lower()
        if 'no' in response or 'exit' in response:
            speak("Goodbye!")
            break
