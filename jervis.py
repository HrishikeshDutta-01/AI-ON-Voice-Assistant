import speech_recognition as sr
import pyttsx3
import threading
import time
import webbrowser
import customtkinter as ctk

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# 🔐 YOUR LOGIN
ERP_USER = "et22bthcs038@kazirangauniversity.in"
ERP_PASS = "Hrishi2004"


# ================= UI =================
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.title("AI-on Assistant")
app.geometry("600x450")

output = ctk.CTkTextbox(app, height=300, width=520)
output.pack(pady=20)


# ================= VOICE =================
engine = pyttsx3.init()
engine.setProperty("rate", 185)

def speak(text):
    output.insert("end", f"AI-on: {text}\n")
    output.see("end")

    def run():
        engine.say(text)
        engine.runAndWait()

    threading.Thread(target=run, daemon=True).start()


# ================= LISTEN =================
recognizer = sr.Recognizer()

def listen():
    try:
        with sr.Microphone() as source:
            output.insert("end", "🎤 Listening...\n")
            output.see("end")

            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5)

        text = recognizer.recognize_google(audio)
        output.insert("end", f"You: {text}\n")
        output.see("end")

        return text.lower()

    except:
        speak("I didn't catch that")
        return ""


# ================= ERP AUTOMATION =================
def check_attendance():
    driver = None

    try:
        speak("Opening ERP")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.maximize_window()
        driver.get("https://kuerp.kazirangauniversity.in/")

        # LOGIN
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        driver.find_element(By.ID, "username").send_keys(ERP_USER)
        driver.find_element(By.ID, "password").send_keys(ERP_PASS)
        driver.find_element(By.ID, "btnLogIn").click()

        speak("Logged in")

        time.sleep(5)

        # CLICK ATTENDANCE BUTTON
        attendance_btn = WebDriverWait(driver, 40).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//a[contains(@href,'student_registered_subjects')]"
            ))
        )

        driver.execute_script("arguments[0].scrollIntoView();", attendance_btn)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", attendance_btn)

        speak("Fetching attendance")

        # WAIT FOR PAGE
        time.sleep(5)

        # 🔥 GET ALL VALUES
        elements = driver.find_elements(By.XPATH, "//th[contains(@class,'text-center')]")

        values = []

        for el in elements:
            text = el.text.strip()

            # only numbers like 0.00, 75.23
            if text and text.replace(".", "").isdigit():
                values.append(text)

        print("ALL VALUES:", values)

        if values:
            attendance = values[-1]   # take last value
            speak(f"Your attendance is {attendance} percent")
        else:
            speak("Attendance not found")

    except Exception as e:
        print("ERROR:", e)
        speak("Failed to fetch attendance")

    finally:
        if driver:
            driver.quit()


# ================= COMMAND =================
def process_command(cmd):

    if "attendance" in cmd:
        threading.Thread(target=check_attendance, daemon=True).start()

    elif "open erp" in cmd:
        webbrowser.open("https://kuerp.kazirangauniversity.in/")
        speak("Opening ERP")

    elif "hello" in cmd:
        speak("Hello, how can I help you")

    else:
        speak("I didn't understand")


# ================= MAIN =================
def start():
    speak("AI-on is ready")

    while True:
        cmd = listen()
        if cmd:
            process_command(cmd)


# ================= BUTTON =================
btn = ctk.CTkButton(
    app,
    text="Start Assistant",
    command=lambda: threading.Thread(target=start, daemon=True).start()
)

btn.pack(pady=10)

app.mainloop()