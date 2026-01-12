# Gmail Pub/Sub Integration

A full-stack application for managing Gmail notifications using Google Cloud Pub/Sub, featuring an AI-powered agent for email analysis and lead generation.

## 🚀 Features

- **Gmail Integration**: OAuth2-based Gmail authentication
- **Real-time Notifications**: Google Cloud Pub/Sub for Gmail push notifications
- **AI Agent**: Intelligent email analysis using LangGraph
- **Lead Management**: Automatic lead extraction and dashboard
- **React Frontend**: Modern UI for managing emails and leads
- **FastAPI Backend**: High-performance REST API

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- Google Cloud Platform account
- Gmail account

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/prathamsurti/gmail-pub-sub.git
cd gmail-pub-sub
```

### 2. Google Cloud Platform Setup

#### Create a GCP Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Gmail API
   - Cloud Pub/Sub API

#### Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. Configure the consent screen if prompted
4. Choose **Web application** as application type
5. Add authorized redirect URIs:
   - `http://localhost:8000/oauth2callback`
   - Add your production URL if deploying
6. Download the credentials and save as `tokenai-credential.json` in the `backend/` folder

#### Create Service Account (for Pub/Sub)
1. Go to **IAM & Admin** → **Service Accounts**
2. Click **Create Service Account**
3. Grant roles: **Pub/Sub Admin**
4. Create and download JSON key
5. Save as `service-account-key.json` in the `backend/` folder

#### Set up Pub/Sub
1. Go to **Pub/Sub** → **Topics**
2. Create a topic (e.g., `gmail-notifications`)
3. Create a subscription for the topic (e.g., `gmail-pull-sub`)

### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env
```

#### Configure `.env` file

Edit `backend/.env` with your values:

```env
# Google OAuth Credentials
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Google Service Account for Pub/Sub
GOOGLE_APPLICATION_CREDENTIALS=backend/service-account-key.json

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Pub/Sub Configuration
PUBSUB_TOPIC=projects/your-project-id/topics/gmail-notifications
PUBSUB_SUBSCRIPTION=projects/your-project-id/subscriptions/gmail-pull-sub
```

#### Place Credential Files

Ensure these files are in the `backend/` folder:
- `tokenai-credential.json` (OAuth credentials)
- `service-account-key.json` (Service account key)

### 4. Gmail Agent Setup

```bash
cd gmail_agent

# Install dependencies
pip install -r requirements.txt
```

**Note**: The Gmail agent requires an API key for the AI model. Configure it according to your AI service provider.

### 5. Frontend Setup

```bash
cd client

# Install dependencies
npm install

# For development
npm start

# For production build
npm run build
```

## 🚦 Running the Application

### Start Backend Server

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

### Start Frontend (Development)

```bash
cd client
npm start
```

The frontend will be available at `http://localhost:3000`

### API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📁 Project Structure

```
gmail-pub-sub/
├── backend/                # FastAPI backend
│   ├── main.py            # Main API server
│   ├── listener.py        # Pub/Sub listener
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment variables (not tracked)
├── client/                # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   └── utils/        # Utility functions
│   ├── public/           # Static files
│   └── package.json      # Node dependencies
├── gmail_agent/          # AI agent for email analysis
│   ├── agents/           # Agent implementations
│   ├── graph.py          # LangGraph workflow
│   └── api.py            # Agent API
└── README.md
```

## 🔐 Security Notes

- **Never commit** credential files (`.json` files with secrets)
- **Never commit** `.env` files
- Keep your OAuth credentials and service account keys secure
- Use environment variables for sensitive data
- Regularly rotate your API keys and credentials

## 🧪 Gmail Watch Setup

To enable Gmail push notifications:

1. Authenticate with Gmail (visit `/auth` endpoint)
2. The application will automatically set up a watch on your Gmail inbox
3. Notifications will be sent to your Pub/Sub topic

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🐛 Troubleshooting

### OAuth Error: redirect_uri_mismatch
- Ensure your redirect URI in Google Cloud Console matches exactly: `http://localhost:8000/oauth2callback`

### Pub/Sub Connection Issues
- Verify service account has Pub/Sub Admin role
- Check that `GOOGLE_APPLICATION_CREDENTIALS` path is correct
- Ensure Pub/Sub API is enabled in your GCP project

### CORS Errors
- Check that `FRONTEND_URL` in `.env` matches your frontend URL
- Verify CORS middleware configuration in `main.py`

## 📧 Support

For issues and questions, please open an issue on GitHub.
