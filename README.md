# 📧 Email Manager - FastAPI Email Automation App

A powerful FastAPI application that automates email processing with Gmail integration, AI-powered summarization, and scheduled reporting.

## 🚀 Features

- **📧 Send Email Endpoint**: Send emails using Jinja2 templates
- **📬 Scheduled Gmail Fetcher**: Automatically fetch emails every 24 hours
- **🧠 AI Summarization**: Summarize emails using LangChain LLMs (OpenAI/Groq)
- **📤 HTML Reports**: Generate and send beautiful HTML summary reports
- **🔒 Secure**: Environment-based configuration for sensitive data

## 📋 Requirements

- Python 3.8+
- Gmail Account with App Password or OAuth2 credentials
- OpenAI API Key or Groq API Key for summarization

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd EmailManager
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Configure Gmail API** (if using OAuth2):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Gmail API
   - Create OAuth2 credentials
   - Download `credentials.json` to project root

## ⚙️ Configuration

Edit your `.env` file:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_ADDRESS=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Gmail API Configuration
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json

# LLM Configuration (choose one)
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key

# Report Configuration
REPORT_RECIPIENT_EMAIL=recipient@example.com

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Gmail Setup Options

**Option 1: App Password (Recommended for simplicity)**
1. Enable 2-factor authentication on your Google account
2. Generate an app password: https://myaccount.google.com/apppasswords
3. Use the app password in `EMAIL_PASSWORD`

**Option 2: OAuth2 (More secure)**
1. Set up Gmail API credentials as described above
2. The app will prompt for authentication on first run

## 🚦 Usage

### Start the Application

```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### Send Email
```bash
POST /send-email/
Content-Type: application/json

{
    "to_email": "recipient@example.com",
    "subject": "Test Email",
    "body": "This is a test email body."
}
```

#### Health Check
```bash
GET /health
```

#### Application Status
```bash
GET /status
```

#### Manual Report Trigger
```bash
POST /trigger-report/
```

### Scheduled Features

- **Daily Email Fetching**: Automatically runs every 24 hours
- **Email Summarization**: Uses AI to create concise summaries
- **HTML Report Generation**: Creates beautiful summary reports
- **Automatic Email Delivery**: Sends reports to configured recipient

## 📁 Project Structure

```
EmailManager/
├── main.py                 # FastAPI app and routes
├── email_utils.py          # Email sending functionality
├── gmail_utils.py          # Gmail API integration
├── summarizer.py           # LangChain LLM summarization
├── templates/              # Jinja2 templates
│   ├── email_template.html # General email template
│   └── summary_report.html # Daily report template
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🔧 Development

### Running Tests

```bash
# Add test files and run
python -m pytest tests/
```

### Code Style

```bash
# Format code (if you have black installed)
black .

# Type checking (if you have mypy installed)
mypy .
```

## 🐛 Troubleshooting

### Common Issues

1. **Gmail Authentication Fails**
   - Ensure 2FA is enabled and app password is correct
   - Check that "Less secure app access" is enabled (if not using app password)

2. **LLM Summarization Not Working**
   - Verify API keys are correct
   - Check internet connectivity
   - Review logs for specific error messages

3. **Scheduled Tasks Not Running**
   - Check application logs
   - Ensure the app is running continuously
   - Verify environment variables are loaded

### Logs

The application provides detailed logging. Check console output for:
- Authentication status
- Email fetching progress
- Summarization results
- Scheduled task execution

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Open an issue in the repository