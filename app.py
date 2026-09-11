import streamlit as st
import os
from google import genai
from google.genai import types
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Define permission boundaries for Google Calendar
SCOPES = ['https://googleapis.com', 'https://googleapis.com.events']

# ==========================================
# 1. CORE GOOGLE CALENDAR CONNECTION PIPELINE
# ==========================================
def get_calendar_service():
    """Initializes the secure connection directly from Streamlit configuration secrets."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        secret_data = {"web": dict(st.secrets["GOOGLE_CLIENT_SECRET"])}
        flow = InstalledAppFlow.from_client_config(secret_data, SCOPES)
        creds = flow.run_local_server(
            port=0, 
            authorization_prompt_message="Please visit this URL to authorize the app: {url}",
            success_message="The authentication flow has completed. You may close this window."
        )
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('calendar', 'v3', credentials=creds)

# ==========================================
# 2. DEFINE NATIVE CALENDAR TOOL
# ==========================================
def google_calendar_create_event(name: str, email: str, start_time_iso: str) -> str:
    """Creates a 30-minute meeting on Google Calendar and sends an automated invite email."""
    try:
        service = get_calendar_service()
        start_dt = datetime.fromisoformat(start_time_iso)
        end_dt = start_dt + timedelta(minutes=30)
        end_time_iso = end_dt.isoformat()

        event_payload = {
            'summary': f'Meeting with {name}',
            'description': '30-minute consultation scheduled via Gemini Booking Assistant.',
            'start': {'dateTime': start_time_iso, 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end_time_iso, 'timeZone': 'Asia/Kolkata'},
            'attendees': [{'email': email}],
            'reminders': {'useDefault': True}
        }

        event = service.events().insert(
            calendarId='primary', 
            body=event_payload, 
            sendUpdates='all'
        ).execute()
        
        return f"SUCCESS: Meeting successfully booked! Event Link: {event.get('htmlLink')}"
    except Exception as e:
        return f"ERROR: Failed to book calendar event due to: {str(e)}"

# ==========================================
# 3. STREAMLIT INTERFACE & SECURE LOGIN
# ==========================================
st.set_page_config(page_title="Gemini Booking Engine", page_icon="📅", layout="wide")

# Sidebar Configuration for Key Protection
with st.sidebar:
    st.title("🔐 Authentication")
    # Password box that masks input with dots
    gemini_key = st.text_input(
        "Enter Google GenAI Key:", 
        type="password", 
        placeholder="AIzaSy...",
        help="Get your key from Google AI Studio. It is never stored on the server."
    )
    st.markdown("---")
    st.info("The application UI will unlock automatically once a valid key format is entered.")

# Main Application Frame Control
st.title("🤖 Pure Gemini Booking Engine")
st.subheader("Autonomous scheduling app built with Python & Google GenAI")

# Lock screen logic: Guard the app if the password field is empty
if not gemini_key:
    st.warning("Please enter your Gemini API Key in the left sidebar password box to unlock the chat agent.")
    st.stop()

# Initialize the Google GenAI Engine using the custom typed password key
try:
    client = genai.Client(api_key=gemini_key)
except Exception as e:
    st.error(f"Failed to initialize engine. Verify key validity: {str(e)}")
    st.stop()

# Manage UI persistent messaging chat cache
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "Hello! I am your scheduling assistant. Provide your Name, Email, and preferred Date/Time to book an appointment."}
    ]

# Render chat interface log
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Capture live user text entries
if user_input := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.spinner("Processing automation pipeline..."):
        # Format runtime session array into historical content models
        formatted_history = []
        for m in st.session_state.messages[:-1]:
            role_type = "user" if m["role"] == "user" else "model"
            formatted_history.append(
                types.Content(role=role_type, parts=[types.Part.from_text(text=m["content"])])
            )

        system_instruction = (
            "You are a precise Booking Assistant. Your goal is to collect a user's Name, Email, Date, and Time. "
            "The current real-world time is Friday, September 11, 2026. Use this as your reference point for relative dates. "
            "If any detail is missing, ask for it politely. The moment you have all details and the user confirms, you must "
            "immediately execute the `google_calendar_create_event` function tool call. Never fake a booking."
        )

        try:
            # Call Gemini with native Function tools attached
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_input,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[google_calendar_create_event],
                )
            )

            # Handle automated background function tool actions if triggered by Gemini
            if response.function_calls:
                for call in response.function_calls:
                    if call.name == "google_calendar_create_event":
                        tool_result = google_calendar_create_event(**call.args)
                        
                        final_response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=f"The tool executed with the following result: {tool_result}. Summarize this confirmation cleanly to the user.",
                            config=types.GenerateContentConfig(system_instruction=system_instruction)
                        )
                        agent_reply = final_response.text
            else:
                agent_reply = response.text

        except Exception as api_err:
            agent_reply = f"API Error (Check if your password key is expired or invalid): {str(api_err)}"

        # Append and render assistant answer block
        st.session_state.messages.append({"role": "model", "content": agent_reply})
        with st.chat_message("model"):
            st.write(agent_reply)
