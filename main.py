import os
import pytz
from datetime import datetime
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Initialize Flask App
app = Flask(__name__)

# Configure Google Gemini AI
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Twilio Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
MY_NUMBER = os.getenv("MY_NUMBER")        # Admin's WhatsApp number
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")  # Twilio Sandbox/Verified number

client = Client(TWILIO_SID, TWILIO_TOKEN)

def get_ist_time():
    """Returns the current time in Indian Standard Time (IST)."""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

def notify_admin(sender_name, sender_number, message_body):
    """Sends a notification alert to the Admin (Shyam) via WhatsApp."""
    alert_payload = (
        f"🔔 *New Message for Shyam!*\n\n"
        f"👤 *Sender:* {sender_name}\n"
        f"📱 *Phone:* {sender_number}\n"
        f"⏰ *Time:* {get_ist_time()}\n"
        f"💬 *Message:* {message_body}"
    )
    
    client.messages.create(
        from_=TWILIO_NUMBER,
        body=alert_payload,
        to=MY_NUMBER
    )

@app.route("/whatsapp", methods=['POST'])
def whatsapp_webhook():
    """Handles incoming WhatsApp messages via Twilio Webhook."""
    # Extracting incoming message data
    incoming_msg = request.values.get('Body', '').strip()
    sender_number = request.values.get('From', '')
    sender_name = request.values.get('ProfileName', 'Guest')
    
    response = MessagingResponse()
    reply = response.message()

    # 1. Handle Welcome Trigger
    if incoming_msg.lower() in ['hi', 'hello', 'star', 'hey']:
        welcome_note = (
            f"Hello {sender_name}! 👋\n\n"
            f"I am *'Star'*, Shyam's AI Assistant. 🚀\n"
            f"Shyam is currently away, but I'm here to help. "
            f"Please leave your message below, and I will forward it "
            f"to him immediately! ✨"
        )
        reply.body(welcome_note)
        return str(response)

    # 2. Forward Message to Admin & Generate AI Reply
    try:
        # Notify the admin about the new message
        notify_admin(sender_name, sender_number, incoming_msg)
        
        # Generate an intelligent AI response using Gemini
        ai_prompt = (
            f"You are Star, a professional AI assistant for Shyam. "
            f"A user named {sender_name} sent this message: '{incoming_msg}'. "
            f"Provide a brief, polite response in English confirming that the "
            f"message has been forwarded to Shyam and address their query if possible."
        )
        
        gen_ai_response = model.generate_content(ai_prompt)
        reply.body(gen_ai_response.text)

    except Exception as e:
        print(f"Error encountered: {e}")
        reply.body("I've received your message, but I'm having trouble processing a smart reply. "
                   "Don't worry, I have already notified Shyam!")

    return str(response)

if __name__ == "__main__":
    # Required for deployment on platforms like Replit or VPS
    app.run(host='0.0.0.0', port=8080)
      
