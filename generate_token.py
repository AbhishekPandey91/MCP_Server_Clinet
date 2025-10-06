import os
import base64
from email.mime.text import MIMEText
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import tool
from langgraph.prebuilt import create_react_agent
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Gmail API setup - Full access required for drafts, send, read
SCOPES = [
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_gmail_service():
    """Get Gmail API service"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

# Initialize Gmail service
print("🔐 Initializing Gmail service...")
gmail_service = get_gmail_service()
print("✅ Gmail service ready!")

# Define custom Gmail tools
@tool
def create_gmail_draft(to: str, subject: str, message: str) -> str:
    """
    Create a draft email in Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        message: Email body content
    
    Returns:
        Success message with draft ID
    """
    try:
        email_message = MIMEText(message)
        email_message['to'] = to
        email_message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode('utf-8')
        draft = gmail_service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        
        return f"✅ Draft created successfully! Draft ID: {draft['id']}"
    except Exception as e:
        return f"❌ Error creating draft: {str(e)}"

@tool
def send_gmail_message(to: str, subject: str, message: str) -> str:
    """
    Send an email via Gmail.
    
    Args:
        to: Recipient email address
        subject: Email subject
        message: Email body content
    
    Returns:
        Success message with message ID
    """
    try:
        email_message = MIMEText(message)
        email_message['to'] = to
        email_message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode('utf-8')
        sent_message = gmail_service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return f"✅ Email sent successfully! Message ID: {sent_message['id']}"
    except Exception as e:
        return f"❌ Error sending email: {str(e)}"

@tool
def search_gmail(query: str, max_results: int = 5) -> str:
    """
    Search Gmail messages.
    
    Args:
        query: Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
        max_results: Maximum number of results to return (default: 5)
    
    Returns:
        List of matching emails with subject and snippet
    """
    try:
        results = gmail_service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "No messages found matching your query."
        
        email_list = []
        for msg in messages:
            message = gmail_service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='metadata',
                metadataHeaders=['Subject', 'From']
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            snippet = message.get('snippet', '')
            
            email_list.append(f"From: {from_email}\nSubject: {subject}\nSnippet: {snippet}\n")
        
        return "\n---\n".join(email_list)
    except Exception as e:
        return f"❌ Error searching emails: {str(e)}"

@tool
def get_latest_gmail_messages(count: int = 5) -> str:
    """
    Get the latest emails from inbox.
    
    Args:
        count: Number of latest emails to retrieve (default: 5)
    
    Returns:
        List of latest emails with details
    """
    try:
        results = gmail_service.users().messages().list(
            userId='me',
            maxResults=count,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "No messages found in inbox."
        
        email_list = []
        for msg in messages:
            message = gmail_service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            snippet = message.get('snippet', '')
            
            email_list.append(f"Date: {date}\nFrom: {from_email}\nSubject: {subject}\nSnippet: {snippet}\n")
        
        return "\n---\n".join(email_list)
    except Exception as e:
        return f"❌ Error getting emails: {str(e)}"

# Collect all tools
tools = [
    create_gmail_draft,
    send_gmail_message,
    search_gmail,
    get_latest_gmail_messages
]

print(f"✅ Loaded {len(tools)} Gmail tools: {[tool.name for tool in tools]}\n")

# Initialize LLM
print("🤖 Initializing LLM...")
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
    temperature=0,
)

# Create agent
print("🚀 Creating agent...")
agent_executor = create_react_agent(llm, tools)

print("\n" + "="*60)
print("Gmail Agent Ready!")
print("="*60 + "\n")

# Example query
example_query = "Schedule an email for abhi1shek2pandey@gmail.com for asking him to go out for trip , also telling him the benefits of trip , that will be automatically sned at 2:40 pm from my side my name is Abhishek pandey "

print(f"📝 Query: {example_query}\n")
print("-"*60 + "\n")

# Stream results
events = agent_executor.stream(
    {"messages": [("user", example_query)]},
    stream_mode="values",
)

for event in events:
    event["messages"][-1].pretty_print()

print("\n" + "="*60)
print("✅ Done!")
print("="*60)