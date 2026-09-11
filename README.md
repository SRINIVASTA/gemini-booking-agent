# 🤖 Pure Gemini Booking Engine

An autonomous, production-grade scheduling chatbot application built with **Python**, **Streamlit**, and the **Google GenAI SDK**. The agent interacts natively with users to extract scheduling parameters (Name, Email, Date, and Time), tracks conversation state accurately across messages, and autonomously updates your calendar via the Google Calendar API using a secure, headless Cloud Service Account setup.

---

## ✨ Features

* **True Autonomous Tool Calling:** Uses Gemini's native function execution pipeline (`tools=[google_calendar_create_event]`) to directly process scheduling payloads instead of simple pattern-matching scripts.
* **Persistent Chat Memory Pipeline:** Structured conversation state architecture prevents the model from resetting or dropping parameters when collecting user context or managing confirmation flows.
* **Headless Cloud Architecture:** Eliminates broken desktop browser authentication loops (`run_local_server` or terminal prompts) by utilizing an offline Google Cloud Service Account credentials layer.
* **Streamlit Interface Lock:** Secure client-side mask hides the workspace interface frame until a valid Gemini API endpoint authorization key format is entered.

---

## 🛠️ Infrastructure Requirements

Make sure your configuration environment contains the following target libraries:

```text
google-genai
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
streamlit
```

---

## 🚀 Setup & Deployment Pipeline

### 1. Provision Your Google Cloud Service Account Bot
To enable headless cloud scheduling without using external middleware like Composio:
1. Navigate to the **[Google Cloud Console](https://google.com)**.
2. Go to **APIs & Services** > **Library**, search for the **Google Calendar API**, and click **Enable**.
3. Head over to **IAM & Admin** > **Service Accounts** and click **Create Service Account**.
4. Set the name identifier (e.g., `gemini-booking-bot`) and proceed to click **Create and Continue**, then click **Done** (skip optional role assignments).
5. Click on the email identifier of your new service account from the list.
6. Navigate to the **Keys** tab, click **Add Key** > **Create New Key**, choose **JSON**, and select **Create**. A configuration key file will download to your machine.

### 2. Configure Your Production Runtime Secrets
Streamlit handles backend environment protection using the `TOML` structural format. Open your downloaded JSON key file with a text editor, copy its contents, and map them to your environment variables using the structure below.

#### Hosted Cloud (Streamlit Community Cloud)
1. Go to your active app dashboard, open **Settings**, and head down to the **Secrets** tab panel box.
2. Paste your data structured exactly like this:

```toml
[GOOGLE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "YOUR_PRIVATE_KEY"
client_email = "your-bot-name@://gserviceaccount.com"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://google.com"
token_uri = "https://googleapis.com"
auth_provider_x509_cert_url = "https://googleapis.com"
client_x509_cert_url = "YOUR_CLIENT_X509_CERT_URL"
universe_domain = "googleapis.com"
```
3. Click **Save**.

#### Local Engine Testing (Offline Desktop Simulation)
If running your app locally, create a new directory path named `.streamlit/` inside the root workspace folder, create a file named `secrets.toml`, and paste the placeholder configuration block shown above directly into it.

### 3. Grant Bot Calendar Access Permissions
Because a Service Account acts as an independent virtual profile identity, your target personal Google Calendar configuration must allow write access for the bot:
1. Open your browser to the **[Google Calendar Workspace Dashboard](https://google.com)**.
2. Hover over your primary calendar name in the left menu, click the **three dots (...)**, and select **Settings and sharing**.
3. Head down to the **Share with specific people or groups** structural segment and click **Add people**.
4. Paste the dummy bot identifier email address generated in Step 1 (`your-bot-name@://gserviceaccount.com`).
5. Toggle the operational permission rights selection to **Make changes to events**, then click **Send**.

---

## 📖 Operational Usage Example

Once the runtime environment deployment completes, launch the interface using the Streamlit execution engine:

```bash
streamlit run app.py
```

Provide your developer API authorization key within the sidebar text panel to unlock the agent conversation model, then execute transaction prompts like the example below:

```text
User: Book a meeting for John Doe, email: johndoe@example.com, on September 12, 2026 at 10:00 AM.

Assistant: Thank you for providing the details. To confirm, you'd like to book a meeting for John Doe at johndoe@example.com on September 12, 2026, at 10:00 AM. Is that correct?

User: yes

Assistant: SUCCESS: Meeting successfully booked! Event Link: https://google.com...
```
