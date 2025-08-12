from groq import Groq
from config import GROQ_API_KEY
from typing import List, Tuple

import threading

# In-memory storage for last appointment (thread-safe for FastAPI dev use)
last_appointment = {"date": None, "time": None}
appointment_lock = threading.Lock()

SYSTEM_PROMPT = """You are Dr. Mustafa Badshah, a warm and experienced clinical psychologist. 
Respond to patients with:
1. Emotional attunement ("I can sense how difficult this must be...")
2. Gentle normalization ("Many people feel this way when...")
3. Practical guidance ("What sometimes helps is...")
4. Strengths-focused support ("I notice how you're...")
Key principles:
- Never use brackets or labels
- Blend elements seamlessly
- Vary sentence structure
- Use natural transitions
- Mirror the user's language level
- Always keep the conversation going by asking open-ended questions to dive into the root cause of patients' problems
"""

def query_medgemma(prompt: str) -> str:
    """
    Calls a Groq model (LLaMA3-70B) with a therapist personality profile.
    Returns responses as an empathic mental health professional.
    """
    try:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=350,
            temperature=0.7,
            top_p=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "I'm having technical difficulties, but I want you to know your feelings matter. Please try again shortly."

def parse_response(stream: List[dict]) -> Tuple[str, str]:
    """
    Parse the streamed response from Groq, extracting the final response and tool called (if any).
    For simplicity, assumes no tools are called unless distress is detected.
    """
    final_response = ""
    tool_called_name = None
    for chunk in stream:
        if chunk.get("content"):
            final_response += chunk["content"]

    # Tool triggers (check both user input and LLM response, with flexible matching)
    import re
    def normalize(text):
        return re.sub(r'[^a-z0-9\s]', '', text.lower())

    distress_keywords = [
        # direct crisis
        "crisis", "emergency", "hurt myself", "kill myself", "end my life", "suicidal", "die", "cant go on", "give up", "ending my life", "no reason to live", "need help immediately", "urgent help", "im in a crisis", "i am in crisis", "need help now", "suicide",
        # indirect/colloquial
        "panic attack", "panic", "anxiety attack", "feel unsafe", "need to call me", "call me now", "need urgent help", "need someone to talk to urgently", "need immediate help", "help me now", "talk to me now", "need to talk now", "need support now",
        # call-related
        "phone call", "call me", "want to talk", "call doctor", "call therapist", "want phone call", "need phone call", "can you call me", "can i get a call"
    ]
    medication_keywords = [
        "medication", "medicine", "prescribe", "antidepressant", "meds", "prescription", "take my meds", "medication advice", "medicine for depression", "medicine for anxiety",
        # indirect/colloquial
        "should i take pills", "should i take medicine", "do i need medication", "can you give me medicine", "can you prescribe something", "should i use antidepressants", "should i use anxiety medication"
    ]
    appointment_keywords = [
        "appointment", "book", "schedule", "see a doctor", "visit a doctor", "make an appointment", "doctor appointment", "consultation", "book a session", "want appointment", "need appointment",
        # indirect/colloquial
        "find doctor", "find therapist", "therapist near me", "doctor near me", "want doctor like you", "need to see someone", "need to see a doctor", "can i see you", "can i book with you", "can i talk to a doctor", "can i talk to a therapist",
        # call-related
        "phone call", "call me", "want to talk", "call doctor", "call therapist", "want phone call", "need phone call", "can you call me", "can i get a call"
    ]

    # Accept user_message as an optional argument for direct checking
    import inspect
    user_message = None
    frame = inspect.currentframe()
    try:
        outer_frames = inspect.getouterframes(frame)
        for f in outer_frames:
            if 'query' in f.frame.f_locals:
                user_message = f.frame.f_locals['query'].message
                break
    except Exception:
        user_message = None
    finally:
        del frame

    def contains_keywords(text, keywords):
        norm = normalize(text)
        return any(kw in norm for kw in keywords)

    def extract_datetime(text):
        # Simple regex for date and time (e.g., 12/8/2025 11:00am, 2/8/2025 11:00am, 12-8-2025 11:00, etc.)
        import re
        date_time_pattern = r'(\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b)[,\s]*(\d{1,2}:\d{2}(?:\s*[ap]m)?)?'
        match = re.search(date_time_pattern, text, re.IGNORECASE)
        if match:
            date = match.group(1)
            time = match.group(2) if match.group(2) else None
            return date, time
        return None, None

    def is_appointment_details_request(text):
        # Check if user is asking for details/confirmation or who the appointment is with
        keywords = ["details", "confirm", "where", "when", "info", "information", "summary", "remind", "reminder",
                    "who is my appointment with", "to whom", "with whom", "who am i seeing", "doctor name", "therapist name", "who is my doctor", "who is my therapist"]
        norm = normalize(text)
        return any(kw in norm for kw in keywords)

    lower_resp = final_response.lower()
    # Check user message first, then LLM response
    # Emergency tool: detect phone number and simulate call
    if (user_message and contains_keywords(user_message, distress_keywords)) or contains_keywords(final_response, distress_keywords):
        tool_called_name = "emergency_call"
        import re
        phone_match = re.search(r'(\+?\d[\d\s\-]{7,}\d)', user_message or "")
        if phone_match:
            number = phone_match.group(1).replace(" ", "")
            final_response = f"Detected distress. Alerting emergency support at {number}. Please stay where you are—help is on the way."
        elif user_message and ("call me" in (user_message or "").lower()):
            final_response = "Detected distress. Alerting emergency support and attempting to contact you. Please stay where you are—help is on the way."
        else:
            final_response = "Detected distress. Connecting to emergency support."
    # Medication tool: detect medicine suggestion requests
    elif (user_message and contains_keywords(user_message, medication_keywords)) or contains_keywords(final_response, medication_keywords):
        tool_called_name = "medication_advice"
        med_request_keywords = ["suggest medicine", "suggest medicines", "what medicine", "what medicines", "which medicine", "which medicines", "recommend medicine", "recommend medicines", "medicine name", "medication name", "drug name", "antidepressant name", "anxiety medicine"]
        if user_message and any(kw in (user_message or "").lower() for kw in med_request_keywords):
            final_response = (
                "I'm not able to recommend or prescribe specific medications. However, common types of medications for depression and anxiety include SSRIs (like sertraline, fluoxetine), SNRIs (like venlafaxine), and others. "
                "The right medication depends on your unique situation, medical history, and a doctor's evaluation. Please consult a licensed psychiatrist or your primary care provider to discuss what might be best for you. If you have questions about medication types, side effects, or how to talk to your doctor, let me know—I'm here to help you make informed decisions."
            )
        else:
            # More supportive, context-aware medication advice
            final_response = (
                "It sounds like you may be considering medication as part of your mental health journey. "
                "While I can't prescribe medication, I can provide general information and support. "
                "It's important to consult a licensed psychiatrist or your primary care provider for a personalized evaluation. "
                "If you have questions about how medication might help, possible side effects, or how to talk to your doctor about it, let me know—I'm here to help you make informed decisions."
            )
    elif (user_message and contains_keywords(user_message, appointment_keywords)) or contains_keywords(final_response, appointment_keywords):
        tool_called_name = "appointment_booking"
        # Try to extract date/time from user message
        date, time = extract_datetime(user_message or "")
        doctor_name = "Dr. Mustafa Badshah"
        if date:
            with appointment_lock:
                last_appointment["date"] = date
                last_appointment["time"] = time
            if time:
                final_response = f"Your appointment with {doctor_name} is scheduled for {date} at {time}. If you need to change it, let me know!"
            else:
                final_response = f"Your appointment with {doctor_name} is scheduled for {date}. If you need to add a time or change it, let me know!"
        elif user_message and is_appointment_details_request(user_message):
            with appointment_lock:
                date = last_appointment["date"]
                time = last_appointment["time"]
            if date:
                if time:
                    final_response = f"Your appointment is with {doctor_name} on {date} at {time}. If you need to change it, let me know!"
                else:
                    final_response = f"Your appointment is with {doctor_name} on {date}. If you need to add a time or change it, let me know!"
            else:
                final_response = f"You have not provided an appointment date yet. Please provide your preferred date and time to book with {doctor_name}."
        else:
            final_response = f"I can help you book an appointment with {doctor_name}. Please provide your preferred date and time, and I'll guide you through the process."

    return tool_called_name, final_response.strip()

# Mock graph object for streaming compatibility with main.py
class Graph:
    def stream(self, inputs: dict, stream_mode: str = "updates") -> List[dict]:
        """
        Calls the Groq API in non-streaming mode to avoid backend timeout.
        """
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=inputs["messages"],
            max_tokens=350,
            temperature=0.7,
            top_p=0.9,
            stream=False
        )
        # Wrap the response in a list of dicts to match expected output
        return [{"content": response.choices[0].message.content.strip()}]

graph = Graph()