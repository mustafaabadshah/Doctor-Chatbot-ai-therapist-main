import streamlit as st
import requests
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Doctor ChatBot Therapist", page_icon="🩺", layout="centered")


# --- CSS Styling ---
st.markdown("""
<style>
.doctor-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
}
.doctor-avatar {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    border: 4px solid #4F8BF9;
    box-shadow: 0 4px 16px rgba(79,139,249,0.15);
    object-fit: cover;
}
.doctor-title {
    font-size: 2.2rem;
    font-weight: 700;
    color: #2d3a4a;
}
.doctor-desc {
    font-size: 1.1rem;
    color: #4F8BF9;
    font-weight: 500;
}
.chat-outer {
    min-height: 420px;
    max-height: 60vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    background: #fafdff;
    border-radius: 1.2rem;
    box-shadow: 0 2px 12px rgba(79,139,249,0.08);
    padding: 1.2rem;
    margin-bottom: 0.5rem;
}
.chat-bubble {
    padding: 1rem 1.2rem;
    border-radius: 1.2rem;
    margin-bottom: 0.7rem;
    max-width: 80%;
    font-size: 1.08rem;
    word-break: break-word;
}
.user-bubble {
    background: #e3f0ff;
    align-self: flex-end;
}
.doctor-bubble {
    background: #ffffff;
    border-left: 5px solid #4F8BF9;
    align-self: flex-start;
}
.input-row {
    display: flex;
    gap: 0.5rem;
    background: white;
    padding: 0.7rem;
    border-radius: 1rem;
    box-shadow: 0 -2px 8px rgba(79,139,249,0.07);
}
.stTextInput > div > div > input {
    font-size: 1.1rem;
    padding: 0.7rem 1rem;
    border-radius: 1rem;
    border: 1.5px solid #4F8BF9;
}
.stButton > button {
    background: linear-gradient(90deg, #4F8BF9 60%, #7ed6df 100%);
    color: white;
    font-weight: 600;
    border-radius: 1rem;
    font-size: 1.1rem;
    padding: 0.7rem 2rem;
    border: none;
}
.sidebar-medical {
    background: #eaf6fb;
    border-radius: 1.2rem;
    padding: 1.2rem 1rem 1.2rem 1rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 12px rgba(79,139,249,0.10);
    text-align: center;
}
.sidebar-medical img {
    width: 120px;
    margin-bottom: 1rem;
}
.sidebar-medical .doc-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: #2d3a4a;
    margin-bottom: 0.2rem;
}
.sidebar-medical .doc-role {
    font-size: 1rem;
    color: #4F8BF9;
    margin-bottom: 0.5rem;
}
.sidebar-medical .doc-quote {
    font-size: 0.98rem;
    color: #3a4a5a;
    font-style: italic;
    margin-top: 0.7rem;
}
</style>
""", unsafe_allow_html=True)
# --- Sidebar Medical Theme ---
with st.sidebar:
    st.markdown('''<div class="sidebar-medical">
        <img src="https://cdn-icons-png.flaticon.com/512/3774/3774299.png" alt="Medical Illustration" />
    <div class="doc-name">Dr. Mustafa Badshah</div>
        <div class="doc-role">Clinical Psychologist</div>
        <div class="doc-quote">“Your mental health is just as important as your physical health.”</div>
        <hr style="margin:1rem 0;">
        <div style="font-size:0.95rem; color:#4F8BF9;">AI-powered, private & confidential</div>
    </div>''', unsafe_allow_html=True)

# --- Doctor Header ---
st.markdown("""
<div class="doctor-header">
    <img src="https://cdn-icons-png.flaticon.com/512/387/387561.png" class="doctor-avatar" alt="Doctor Avatar" />
    <div>
    <div class="doctor-title">Dr. Mustafa Badshah</div>
        <div class="doctor-desc">Your compassionate AI therapist</div>
    </div>
</div>
""", unsafe_allow_html=True)



# --- Session State ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []



# --- Display Chat (scrollable, input always at bottom, tool UI) ---
chat_html = '<div class="chat-outer" id="chat-outer">'
for i, message in enumerate(st.session_state.chat_history):
    if message["role"] == "user":
        chat_html += f'<div class="chat-bubble user-bubble"><b>You:</b> {message["content"]}</div>'
    else:
        # Check for tool trigger in the next message (if present)
        tool = message.get("tool_called")
        if tool == "emergency_call":
            chat_html += f'<div class="chat-bubble doctor-bubble"><b>Dr. Mustafa Badshah:</b> {message["content"]}<br><span style="color:#e74c3c;font-weight:600;">🚨 Emergency support triggered!</span></div>'
        elif tool == "medication_advice":
            chat_html += f'<div class="chat-bubble doctor-bubble"><b>Dr. Mustafa Badshah:</b> {message["content"]}<br><span style="color:#2980b9;font-weight:600;">💊 Medication advice provided</span></div>'
        elif tool == "appointment_booking":
            chat_html += f'<div class="chat-bubble doctor-bubble"><b>Dr. Mustafa Badshah:</b> {message["content"]}<br><span style="color:#27ae60;font-weight:600;">📅 Appointment booking started</span></div>'
        else:
            chat_html += f'<div class="chat-bubble doctor-bubble"><b>Dr. Mustafa Badshah:</b> {message["content"]}</div>'
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)


# --- Improved Input Row (fixed at bottom, clears after send, Enter to send) ---
import streamlit.components.v1 as components
if "user_input" not in st.session_state:
    st.session_state.user_input = ""


def send_message():
    user_input = st.session_state.user_input.strip()
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.user_input = ""
        try:
            response = requests.post(
                "http://localhost:8000/ask",
                json={"message": user_input},
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                assistant_response = data.get("response", "No response.")
                tool_called = data.get("tool_called", None)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": assistant_response,
                    "tool_called": tool_called
                })
            else:
                st.session_state.chat_history.append({"role": "assistant", "content": "Server error. Please try again."})
        except requests.exceptions.RequestException:
            st.session_state.chat_history.append({"role": "assistant", "content": "Unable to connect to the backend."})

st.markdown('<div class="input-row">', unsafe_allow_html=True)
user_input = st.text_input(
    "How can I help you today?",
    key="user_input",
    placeholder="Type your message here...",
    value=st.session_state.user_input,
    on_change=send_message
)
send_clicked = st.button("Send")
if send_clicked:
    send_message()
st.markdown('</div>', unsafe_allow_html=True)

# --- Auto Scroll JS ---
components.html("""
<script>
var chatOuter = window.parent.document.getElementById('chat-outer');
if(chatOuter) { chatOuter.scrollTop = chatOuter.scrollHeight; }
</script>
""", height=0)
