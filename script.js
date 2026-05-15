// ================== ELEMENTS ==================
const btn = document.getElementById("startBtn");
const chat = document.getElementById("chat");

// ================== ADD MESSAGE ==================
function addMessage(message, type = "info") {
    if (!chat) return;

    const div = document.createElement("div");

    if (type === "user") {
        div.className = "user-msg";
        div.innerText = "You: " + message;
    }
    else if (type === "ai") {
        div.className = "ai-msg";
        div.innerText = "AI: " + message;
    }
    else if (type === "error") {
        div.style.color = "red";
        div.innerText = message;
    }
    else {
        div.style.color = "gray";
        div.innerText = message;
    }

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}


// ================== AUTH BUTTON ==================
function updateAuthButton() {
    const btn = document.getElementById("authBtn");
    if (!btn) return;

    if (localStorage.getItem("token")) {
        btn.innerText = "Logout";
    } else {
        btn.innerText = "Login";
    }
}

function handleAuth() {
    if (localStorage.getItem("token")) {
        logout();
    } else {
        window.location.href = "signup.html";
    }
}


// ================== LOGIN CHECK ==================
function isLoggedIn() {
    return !!localStorage.getItem("token");
}

if (!isLoggedIn()) {
    setTimeout(() => {
        addMessage("⚠ Please login first", "error");
    }, 500);
}


// ================== SPEECH RECOGNITION ==================
const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    alert("Use Google Chrome for voice support.");
}

const recognition = SpeechRecognition ? new SpeechRecognition() : null;

if (recognition) {
    recognition.lang = "en-US";
    recognition.interimResults = false;
}


// ================== SPEAK ==================
function speak(text) {
    const speech = new SpeechSynthesisUtterance(text);
    speech.lang = "en-US";
    speech.rate = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(speech);
}


// ================== BUTTON ==================
if (btn && recognition) {
    btn.onclick = () => {
        if (!isLoggedIn()) {
            addMessage("🔐 Please login first", "error");
            speak("Please login first Boss");
            return;
        }

        addMessage("🎤 Listening...", "info");

        try {
            recognition.start();
        } catch (err) {
            console.log("Recognition restart");
        }
    };
}


// ================== VOICE RESULT ==================
if (recognition) {
    recognition.onresult = async function (event) {

        let text = event.results[0][0].transcript;
        addMessage(text, "user");

        try {
            let res = await fetch("http://127.0.0.1:5000/api/command", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + localStorage.getItem("token")
                },
                body: JSON.stringify({ command: text })
            });

            if (res.status === 401) {
                addMessage("🔐 Please login first", "error");
                speak("Please login first Boss");
                return;
            }

            if (!res.ok) {
                throw new Error("Server not responding");
            }

            let data = await res.json();

            const message = data.message || "No response";
            const speechText = data.speech || message;

            addMessage(message, "ai");
            speak(speechText);

            // 🔥 HANDLE ACTION (Google / YouTube)
            if (data.action) {
                window.open(data.action, "_blank");
            }

        } catch (error) {
            console.error("FETCH ERROR:", error);
            addMessage("⚠ Backend not connected", "error");
            speak("Backend is not connected Boss");
        }
    };
}


// ================== ERROR ==================
if (recognition) {
    recognition.onerror = function (event) {

        console.log("Speech error:", event.error);

        if (event.error === "network") {
            addMessage("❌ Check internet connection", "error");
            speak("Network error Boss");
        } 
        else if (event.error === "not-allowed") {
            addMessage("❌ Microphone blocked", "error");
            speak("Microphone permission denied Boss");
        } 
        else {
            addMessage("❌ Speech error: " + event.error, "error");
        }
    };

    recognition.onend = () => {
        console.log("Recognition ended");
    };
}


// ================== WAVEFORM ==================
const canvas = document.getElementById("waveCanvas");

if (canvas) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();

    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {

        const source = audioContext.createMediaStreamSource(stream);
        const analyser = audioContext.createAnalyser();

        analyser.fftSize = 256;
        source.connect(analyser);

        const ctx = canvas.getContext("2d");

        function draw() {
            requestAnimationFrame(draw);

            const data = new Uint8Array(analyser.frequencyBinCount);
            analyser.getByteFrequencyData(data);

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            for (let i = 0; i < 100; i++) {
                const height = data[i] / 2;

                ctx.fillStyle = "#22d3ee";
                ctx.fillRect(i * 5, canvas.height - height, 3, height);
            }
        }

        draw();

    }).catch(() => {
        addMessage("⚠ Microphone access denied", "error");
    });
}


// ================== AUTH ==================
async function signup(username, password) {
    try {
        const res = await fetch("http://127.0.0.1:5000/api/signup", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();
        alert(data.message);

    } catch {
        alert("Signup failed");
    }
}

async function login(username, password) {
    try {
        const res = await fetch("http://127.0.0.1:5000/api/login", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (data.token) {
            localStorage.setItem("token", data.token);
            alert("Login successful");
            updateAuthButton(); // 🔥 update UI
        } else {
            alert(data.message);
        }

    } catch {
        alert("Login failed");
    }
}

function logout() {
    localStorage.removeItem("token");
    alert("Logged out");
    updateAuthButton(); // 🔥 update UI
}


// ================== INIT ==================
updateAuthButton();