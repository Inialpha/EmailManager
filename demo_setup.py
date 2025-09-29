#!/usr/bin/env python3
"""
Demo setup script for Email Manager.
This script demonstrates how to configure and run the Email Manager application.
"""
import os
import shutil
from datetime import datetime

def create_demo_env():
    """Create a demo .env file with placeholder values."""
    demo_env_content = f"""# Email Manager Demo Configuration
# Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# Email Configuration (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password

# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# LLM Configuration (choose one)
# Option 1: OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Option 2: Groq (alternative to OpenAI)
# GROQ_API_KEY=gsk_your-groq-api-key-here

# Report Configuration
REPORT_RECIPIENT_EMAIL=reports@example.com

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
"""
    
    with open('.env', 'w') as f:
        f.write(demo_env_content)
    
    print("✅ Created .env file with demo configuration")
    print("📝 Please edit .env with your actual credentials before running the app")

def create_sample_gmail_credentials():
    """Create a sample credentials.json template."""
    credentials_template = """{
  "installed": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}"""
    
    with open('credentials.json.example', 'w') as f:
        f.write(credentials_template)
    
    print("✅ Created credentials.json.example template")
    print("📝 Rename to credentials.json and add your Gmail API credentials")

def show_setup_instructions():
    """Display setup instructions."""
    instructions = """
🚀 Email Manager Setup Instructions
===============================

1. SMTP Email Configuration:
   - Use Gmail with App Password (recommended)
   - Enable 2FA on your Google account
   - Generate app password: https://myaccount.google.com/apppasswords
   - Update EMAIL_ADDRESS and EMAIL_PASSWORD in .env

2. Gmail API Setup (for fetching emails):
   - Go to https://console.cloud.google.com/
   - Create project and enable Gmail API
   - Create OAuth2 credentials
   - Download and rename to credentials.json

3. LLM Configuration:
   - Option A: Get OpenAI API key from https://platform.openai.com/
   - Option B: Get Groq API key from https://console.groq.com/
   - Add key to .env file

4. Run the Application:
   pip install -r requirements.txt
   python main.py

5. Test the API:
   - Open http://localhost:8000 for API docs
   - Use /send-email/ endpoint to send emails
   - Check /status for scheduler information
   - Use /trigger-report/ to manually run email reports

📧 Email Features:
- Send templated emails via API
- Automatic Gmail fetching (24h intervals)  
- AI-powered email summarization
- Beautiful HTML reports
- Comprehensive logging

🔧 Troubleshooting:
- Check logs for authentication errors
- Verify environment variables are loaded
- Test individual components via /health endpoint
- Ensure proper port availability (8000)

Happy emailing! 📬
"""
    print(instructions)

def main():
    """Main setup function."""
    print("🛠️  Email Manager Demo Setup")
    print("=" * 40)
    
    # Create demo configuration files
    create_demo_env()
    create_sample_gmail_credentials()
    
    # Show setup instructions
    show_setup_instructions()
    
    print("\n🎉 Demo setup complete!")
    print("📖 See README.md for detailed documentation")

if __name__ == "__main__":
    main()