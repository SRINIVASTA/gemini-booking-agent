import streamlit as st
import os
from google import genai
from google.genai import types
from google.oauth2 import service_account  # Added for cloud auth
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials

# ==========================================
# 1. CORE GOOGLE CALENDAR SERVICE PIPELINE
# ==========================================
def get_calendar_service():
    """Initializes a headless connection using a Google Service Account."""
    SCOPES = ['https://googleapis.com']
    
    try:
        # Load the configuration directly from Streamlit Secrets as a standard dictionary
        service_account_info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        
        # Replace the string literal text versions of '\n' with real newline objects
        if "private_key" in service_account_info:
            service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")
        
        # Build the credentials
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, 
            scopes=SCOPES
        )
        
        return build('calendar', 'v3', credentials=creds)
    except Exception as credential_error:
        st.error("🔒 Configuration Error: Verify your GOOGLE_SERVICE_ACCOUNT block inside Streamlit Secrets.")
        raise credential_error
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

        # IMPORTANT: When using a Service Account, we write directly to the 
        # service account's calendar, or a shared target calendar ID.
        event = service.events().insert(
            calendarId='primary', 
            body=event_payload, 
            sendUpdates='all'
        ).execute()
        
        return f"SUCCESS: Meeting successfully booked! Event Link: {event.get('htmlLink')}"
    except Exception as e:
        st.error(f"🔴 CRITICAL TOOL CRASH: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return f"ERROR: Failed to book calendar event due to: {str(e)}"

# ==========================================
# 3. STREAMLIT INTERFACE & SECURE LOGIN
# ==========================================
st.set_page_config(page_title="Gemini Booking Engine", page_icon="📅", layout="wide")

with st.sidebar:
    st.title("🔐 Authentication")
    gemini_key = st.text_input(
        "Enter Google GenAI Key:", 
        type="password", 
        placeholder="AIzaSy...",
        help="Get your key from Google AI Studio. It is never stored on the server."
    )
    st.markdown("---")
    st.info("The application UI will unlock automatically once a valid key format is entered.")

st.title("🤖 Pure Gemini Booking Engine")
st.subheader("Autonomous scheduling app built with Python & Google GenAI")

if not gemini_key:
    st.warning("Please enter your Gemini API Key in the left sidebar password box to unlock the chat agent.")
    st.stop()

try:
    client = genai.Client(api_key=gemini_key)
except Exception as e:
    st.error(f"Failed to initialize engine. Verify key validity: {str(e)}")
    st.stop()

# Initialize Chat Memory in Streamlit Cache
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "content": "Hello! I am your scheduling assistant. Provide your Name, Email, and preferred Date/Time to book an appointment."}
    ]

# Render chat interface history log
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Capture live user text entries
if user_input := st.chat_input("Type your message here..."):
    # Append the new message to display it in UI
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.spinner("Processing automation pipeline..."):
        
        # FIX 2: BUILD THE CONVERSATION HISTORY STRUCTURE CORRECTLY
        formatted_history = []
        for m in st.session_state.messages:
            role_type = "user" if m["role"] == "user" else "model"
            formatted_history.append(
                types.Content(role=role_type, parts=[types.Part.from_text(text=m["content"])])
            )

        system_instruction = (
            "You are a precise Booking Assistant. Your goal is to collect a user's Name, Email, Date, and Time. "
            "The current real-world time is Friday, September 11, 2026. Use this as your reference point for relative dates. "
            "If any detail is missing, ask for it politely. The moment you have all details and the user confirms, you must "
            "immediately execute the `google_calendar_create_event` function tool call by converting the date and time to ISO format. Never fake a booking."
        )

        try:
            # FIX 3: PASS THE FULL SYSTEM CONTEXT HISTORY INSTEAD OF A SINGLE STRING
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=formatted_history, # <-- Fixed history pipeline
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[google_calendar_create_event],
                )
            )

            # Handle native Gemini Function Call Backends
            if response.function_calls:
                for call in response.function_calls:
                    if call.name == "google_calendar_create_event":
                        # Execute local tool
                        tool_result = google_calendar_create_event(**call.args)
                        
                        # FIX 4: RE-APPEND HISTORY + THE FUNCTION CALL + THE RESULT TO KEEP STATE CLEAN
                        # Send back tool response natively to Gemini to summarize
                        final_response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[
                                *formatted_history,
                                response.candidates[0].content, # Contains the AI's requested function call object
                                types.Content(
                                    role="tool",
                                    parts=[
                                        types.Part.from_function_response(
                                            name=call.name,
                                            response={"result": tool_result}
                                        )
                                    ]
                                )
                            ],
                            config=types.GenerateContentConfig(system_instruction=system_instruction)
                        )
                        agent_reply = final_response.text
            else:
                agent_reply = response.text

        except Exception as api_err:
            agent_reply = f"System Processing Error: {str(api_err)}"

        # Append response back to history array
        st.session_state.messages.append({"role": "model", "content": agent_reply})
        with st.chat_message("model"):
            st.write(agent_reply)
