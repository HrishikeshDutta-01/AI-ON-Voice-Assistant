from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import datetime
import bcrypt
import time
import re
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import yagmail
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

load_dotenv()


PDF_PATH = r"C:\Users\Hrish\Downloads\MajorProject (1).pdf"

def open_pdf():
    if os.path.exists(PDF_PATH):
        os.startfile(PDF_PATH)
        return "Opening your project PDF"
    else:
        return "PDF file not found"

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)
CORS(app)

SECRET_KEY = "this_is_a_very_secure_secret_key_123456789"

# ================= DATABASE =================

client = MongoClient("mongodb://localhost:27017/")
db = client["ai_assistant"]
users_col = db["users"]

# ================= UNIVERSITY DATA =================

uni_data = {
    "hod_cse": "Dr. Mousoomi Bora is the HOD of CSE at Kaziranga University with expertise in machine learning, cybersecurity, and over 8 years of experience.",
    "dean_set": "Dr. Ripunjoy Gogoi is the Dean of SET at Kaziranga University, focused on advancing technical education and innovation.",
    "faculty": {
        "tandrali ray": "Tandrali Ray is an Assistant Professor in CSE at Kaziranga University with an MTech from Tezpur University and BTech from CIT Kokrajhar.",
        "bondita paul": "Dr. Bondita Paul is an Assistant Professor in CSE at Kaziranga University with a PhD from IIIT Guwahati and teaching experience at GLA University.",
        "prarthana dutta": "Dr. Prarthana Dutta is an Assistant Professor in CSE at Kaziranga University with a PhD from NIT Silchar in computer science and engineering."
    }
}

# ================= HELPERS =================

def generate_token(username):
    return jwt.encode({
        "user": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")


def verify_token(req):
    auth = req.headers.get("Authorization")

    if not auth or "Bearer " not in auth:
        return None

    try:
        token = auth.split(" ")[1]
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["user"]
    except Exception as e:
        print("JWT ERROR:", e)
        return None


def boss_reply(text):
    return f"{text}, Boss."

# ================= AUTH =================

@app.route("/api/signup", methods=["POST"])
def signup():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        if users_col.find_one({"username": username}):
            return jsonify({"message": "User already exists"}), 400

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        users_col.insert_one({
            "username": username,
            "password": hashed,
            "erp_user": "",
            "erp_pass": "",
            "memory": []
        })

        return jsonify({"message": "Signup successful"})

    except Exception as e:
        print("SIGNUP ERROR:", e)
        return jsonify({"message": "Server error"}), 500


@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        user = users_col.find_one({"username": username})

        if not user:
            return jsonify({"message": "User not found"}), 401

        if not bcrypt.checkpw(password.encode(), user["password"]):
            return jsonify({"message": "Wrong password"}), 401

        token = generate_token(username)

        return jsonify({"token": token})

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ================= SAVE ERP =================

@app.route("/api/save-erp", methods=["POST"])
def save_erp():
    try:
        user = verify_token(request)

        if not user:
            return jsonify({"message": "Unauthorized"}), 401

        data = request.json

        users_col.update_one(
            {"username": user},
            {"$set": {
                "erp_user": data.get("erp_user"),
                "erp_pass": data.get("erp_pass")
            }}
        )

        return jsonify({"message": "ERP saved"})

    except Exception as e:
        print("ERP SAVE ERROR:", e)
        return jsonify({"message": "Server error"}), 500


# ================= ERP =================

def fetch_attendance(username, password):
    driver = None

    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get("https://kuerp.kazirangauniversity.in/")

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "btnLogIn").click()

        time.sleep(6)

        cards = driver.find_elements(By.XPATH, "//div[contains(@class,'card-box')]")

        for c in cards:
            if "attendance" in c.text.lower():
                c.find_element(By.XPATH, ".//a").click()
                break

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        time.sleep(3)

        body_text = driver.find_element(By.TAG_NAME, "body").text

        numbers = re.findall(r"\d+\.?\d*", body_text)

        for num in numbers[::-1]:
            try:
                if float(num) <= 100:
                    return num
            except:
                continue

        return None

    except Exception as e:
        print("ERP ERROR:", e)
        return None

    finally:
        if driver:
            driver.quit()


# ================= EMAIL SYSTEM =================

def generate_leave_text(days=2):
    return f"""Subject: Leave Application

Dear Sir/Madam,

with due respect i beg to state that ,I would like to request leave for {days} days due to personal reasons.

Thank you.

Yours sincerely,  
Student
"""


def save_as_pdf(text):
    file_path = "leave_application.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(text, styles["Normal"])
    ]

    doc.build(story)

    return file_path


def send_email(receiver, file_path):
    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)

    yag.send(
        to=receiver,
        subject="Leave Application",
        contents="Please find attached leave application.",
        attachments=file_path
    )

    return "Email sent successfully"


def extract_email(cmd):
    match = re.search(r'[\w\.-]+@[\w\.-]+', cmd)
    
    if match:
        return match.group()
    else:
        return EMAIL_USER


def handle_leave_email(cmd):
    match = re.search(r"\d+", cmd)
    
    if match:
        days = match.group()
    else:
        days = "2"

    text = generate_leave_text(days)
    pdf_file = save_as_pdf(text)
    receiver = extract_email(cmd)

    send_email(receiver, pdf_file)

    return f"Leave application for {days} days sent to {receiver}"


# ================= COMMAND =================

@app.route("/api/command", methods=["POST"])
def command():
    try:
        user = verify_token(request)

        if not user:
            return jsonify({"message": "Unauthorized"}), 401

        cmd = request.json.get("command", "").lower()

        print("CMD RECEIVED:", cmd)

        # 🧠 STORE MEMORY
        users_col.update_one(
            {"username": user},
            {"$push": {"memory": cmd}}
        )

        user_data = users_col.find_one({"username": user})

        # GREETING
        if "hello" in cmd or "hi" in cmd:
            msg = boss_reply("Hello, how can I assist you")
            return jsonify({"message": msg, "speech": msg})

        # TIME
        elif "time" in cmd:
            t = datetime.datetime.now().strftime("%H:%M:%S")
            msg = boss_reply(f"The current time is {t}")
            return jsonify({"message": msg, "speech": msg})

        # GOOGLE SEARCH
        elif "search" in cmd:
            query = cmd.replace("search", "").strip()
            url = f"https://www.google.com/search?q={query}"

            msg = boss_reply(f"Searching for {query}")
            return jsonify({"message": msg, "speech": msg, "action": url})

        # YOUTUBE
        elif "youtube" in cmd or "play" in cmd:
            query = cmd
            for word in ["play", "on youtube", "youtube", "search"]:
                query = query.replace(word, "")
            query = query.strip()

            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            msg = boss_reply(f"Playing {query} on YouTube")

            return jsonify({"message": msg, "speech": msg, "action": url})

        # ATTENDANCE
        elif "attendance" in cmd:
            erp_user = user_data.get("erp_user")
            erp_pass = user_data.get("erp_pass")

            if not erp_user:
                msg = boss_reply("Please save ERP credentials first")
                return jsonify({"message": msg, "speech": msg})

            initial_msg = boss_reply("Checking your attendance, please wait")

            result = fetch_attendance(erp_user, erp_pass)

            if result:
                final_msg = boss_reply(f"Your attendance is {result} percent")
            else:
                final_msg = boss_reply("Unable to read attendance data")

            return jsonify({
                "message": final_msg,
                "speech": initial_msg + ". " + final_msg
            })

        # MEMORY
        elif "what did i say" in cmd:
            last = user_data.get("memory", [])[-3:]
            msg = boss_reply(f"You said: {', '.join(last)}")
            return jsonify({"message": msg, "speech": msg})

        # FACULTY
        elif "faculty" in cmd:
            names = ", ".join(uni_data["faculty"].keys())
            msg = boss_reply(f"Some faculty members are {names}")
            return jsonify({"message": msg, "speech": msg})

        elif any(name in cmd for name in uni_data["faculty"]):
            for name, info in uni_data["faculty"].items():
                if name in cmd:
                    msg = boss_reply(info)
                    return jsonify({"message": msg, "speech": msg})

        elif "hod" in cmd and "cse" in cmd:
            msg = boss_reply(uni_data["hod_cse"])
            return jsonify({"message": msg, "speech": msg})

        elif "dean" in cmd and "set" in cmd:
            msg = boss_reply(uni_data["dean_set"])
            return jsonify({"message": msg, "speech": msg})

        # EMAIL FEATURE 🔥
        elif "leave" in cmd and "email" in cmd:
            result = handle_leave_email(cmd)

            return jsonify({
                "message": boss_reply(result),
                "speech": boss_reply(result)
            })
        

        # PPT 
        elif "open pdf" in cmd or "open presentation" in cmd:
            result = open_pdf()

            msg = boss_reply(result)
            return jsonify({
                "message": msg,
                "speech": msg
            })

        # DEFAULT
        else:
            msg = boss_reply("I am still learning")
            return jsonify({"message": msg, "speech": msg})


    except Exception as e:
        print("COMMAND ERROR:", e)
        return jsonify({"message": "Server error"}), 500
# ================= RUN =================

if __name__ == "__main__":
    print("🚀 AI Assistant Running...")
    app.run(port=5000, debug=True)