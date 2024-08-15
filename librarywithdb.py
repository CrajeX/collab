import os
import time
import pyttsx3
import datetime
import speech_recognition as sr
import mysql.connector  # Only import datetime once
from pyzbar import pyzbar
import cv2
import json
import random
import sqlite3
import mysql.connector

global book_id
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)

def speak(audio):
    engine.say(audio)
    engine.runAndWait()



def wish_me():
    hour = datetime.datetime.now().hour
    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")

    speak("I'm ADA, your library assistant")

def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source=source)
        audio = r.listen(source, timeout=5)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")

        # Check if 'result2:' is in the recognized query and remove it
        if 'result2:' in query:
            query = query.replace("result2:", "").strip()

    except Exception as e:
        print(e)
        print("Unable to Recognize your voice.")
        return "None"

    return query


def date_and_time():
    try:
        dtnow = datetime.datetime.now()
        am_pm = "AM" if dtnow.hour < 12 else "PM"
        hour_12 = dtnow.hour % 12 if dtnow.hour % 12 != 0 else 12  # Convert to 12-hour format
        date = dtnow.strftime(f'%Y-%m-%d {hour_12}:%M {am_pm}')
        return date
    except Exception as e:
        print(e)
def connect_to_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="studentqr"
        )
        return conn
    except mysql.connector.Error as e:
        print(e)
def search_book():
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'studentqr'
    }

    while True:
        conn = None
        cursor = None

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            speak("By title, or by genre?")
            part_term = take_command()  # Example: "title" or "genre"
            
            if part_term == "None":  # Handle case where voice is not recognized
                speak("Sorry, I didn't catch that. Please try again.")
                continue
            
            # Validate part_term to ensure it's a valid column name
            valid_columns = ['title', 'genre']
            if part_term not in valid_columns:
                speak("Sorry, I didn't understand. Please choose either 'title' or 'genre'.")
                continue

            speak(f"What is the {part_term}?")
            search_term = take_command()  # Example: "psychology"

            if search_term == "None":  # Handle case where voice is not recognized
                speak("Sorry, I didn't catch that. Please try again.")
                continue

            # Correct query to search for a specific term in a column
            query = f"SELECT * FROM book_info WHERE {part_term} LIKE %s"
            cursor.execute(query, ('%' + search_term + '%',))

            # Fetch all matching rows
            results = cursor.fetchall()

            if results:
                speak("Here are the books you can borrow:")
                for row in results:
                    print(row)
                    speak(str(row))
                break  # Exit the loop if successful
            else:
                speak("No books found with the given criteria.")
                break  # Exit the loop if no books found

        except mysql.connector.Error as e:
            print(f"Database error: {e}")
            speak("An error occurred while searching the database.")
            break  # Exit the loop on database error
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            speak("An unexpected error occurred.")
            break  # Exit the loop on unexpected error
        finally:
            # Ensure resources are closed
            if cursor:
                cursor.close()
            if conn:
                conn.close()
def main_library():
    wish_me()
    speak("What you want to do?")
    query = take_command()
    if 'search book' in query or 'search' and 'book' in query:
        search_book()
    
if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    
    search_book()