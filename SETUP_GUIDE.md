# 🚀 FinFind Complete Setup Guide

A step-by-step guide to get FinFind running on your local machine.

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Get API Keys](#-get-api-keys)
3. [Project Setup](#-project-setup)
4. [Configuration](#-configuration)
5. [Running the Project](#-running-the-project)
6. [Verify Everything Works](#-verify-everything-works)
7. [Troubleshooting](#-troubleshooting)

---

## 📦 Prerequisites

### Required Software

| Software | Version | Download Link | Check Command |
|----------|---------|---------------|---------------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) | `python --version` |
| **Node.js** | 20+ | [nodejs.org](https://nodejs.org/) | `node --version` |
| **npm** | 10+ | Comes with Node.js | `npm --version` |
| **Git** | Any | [git-scm.com](https://git-scm.com/) | `git --version` |

### Optional (for Docker setup)

| Software | Version | Download Link |
|----------|---------|---------------|
| **Docker** | 24+ | [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Docker Compose** | 2+ | Included with Docker Desktop |

### Verify Prerequisites

Open a terminal/PowerShell and run:

```powershell
# Check Python
python --version
# Should show: Python 3.11.x or higher

# Check Node.js
node --version
# Should show: v20.x.x or higher

# Check npm
npm --version
# Should show: 10.x.x or higher
```

---

## 🔑 Get API Keys

You need **2 API keys** to run FinFind:

### 1. Groq API Key (Required - for AI/LLM)

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Click **"API Keys"** in the sidebar
4. Click **"Create API Key"**
5. Copy your API key (starts with `gsk_...`)

> ⚠️ **FREE TIER**: Groq offers generous free usage - perfect for development!

### 2. Qdrant Cloud API Key (Required - for Vector Database)

1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Sign up or log in
3. Create a **Free Cluster**:
   - Click **"Create Cluster"**
   - Choose **"Free"** tier
   - Select a region close to you
   - Click **"Create"**
4. Wait for cluster to be ready (~1-2 minutes)
5. Copy your **Cluster URL** (looks like `https://abc123-xyz.us-east-1.aws.cloud.qdrant.io`)
6. Go to **"API Keys"** → **"Create"**
7. Copy your API key

> ⚠️ **FREE TIER**: 1GB storage, perfect for development and demos!

---

## 📂 Project Setup

### Step 1: Clone the Repository

```powershell
# Clone the project
git clone https://github.com/your-team/finfind.git

# Navigate to project folder
cd finfind
```

Or if you already have the project, just navigate to it:
```powershell
cd "c:\Users\Makrembz\OneDrive\Desktop\Vectors in Orbit\FinFind"
```

### Step 2: Backend Setup

```powershell
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate

# If using Command Prompt instead:
# venv\Scripts\activate.bat

# Install Python dependencies
pip install -r requirements.txt
```

> ⏱️ **Note**: First install may take 5-10 minutes (downloads ML models)

### Step 3: Frontend Setup

```powershell
# Open a NEW terminal/PowerShell window
# Navigate to Frontend folder
cd "c:\Users\Makrembz\OneDrive\Desktop\Vectors in Orbit\FinFind\Frontend"

# Install Node.js dependencies
npm install
```

> ⏱️ **Note**: First install may take 2-3 minutes

---

## ⚙️ Configuration

### Step 1: Create Environment File

In the project root folder, copy the example env file:

```powershell
# Navigate to project root
cd "c:\Users\Makrembz\OneDrive\Desktop\Vectors in Orbit\FinFind"

# Copy example to .env
copy .env.example .env
```

### Step 2: Edit .env File

Open `.env` in VS Code or any text editor:

```powershell
code .env
```

### Step 3: Add Your API Keys

Find and replace these values with YOUR actual keys:

```env
# ═══════════════════════════════════════════════════════════════
# QDRANT CLOUD CONFIGURATION (REQUIRED)
# ═══════════════════════════════════════════════════════════════

# Your Qdrant Cluster URL (from Qdrant Cloud dashboard)
QDRANT_URL=https://your-cluster-id.us-east-1.aws.cloud.qdrant.io

# Your Qdrant API Key
QDRANT_API_KEY=your_actual_qdrant_api_key_here

# ═══════════════════════════════════════════════════════════════
# GROQ API CONFIGURATION (REQUIRED)
# ═══════════════════════════════════════════════════════════════

# Your Groq API Key (starts with gsk_)
GROQ_API_KEY=gsk_your_actual_groq_api_key_here

# Model (recommended: llama-3.3-70b-versatile)
GROQ_MODEL=llama-3.3-70b-versatile
```

### Example with Real Format (use YOUR keys):

```env
QDRANT_URL=https://abc123-xyz789.us-east-1.aws.cloud.qdrant.io
QDRANT_API_KEY=aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789
GROQ_API_KEY=gsk_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789abcdef
GROQ_MODEL=llama-3.3-70b-versatile
```

### Step 4: Save the .env File

Press `Ctrl+S` to save.

---

## ▶️ Running the Project

### Option A: Run Manually (Recommended for Development)

You'll need **2 terminal windows** open:

#### Terminal 1: Backend

```powershell
# Navigate to backend
cd "c:\Users\Makrembz\OneDrive\Desktop\Vectors in Orbit\FinFind\backend"

# Activate virtual environment
.\venv\Scripts\Activate

# Run the backend server
python run.py --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
```

#### Terminal 2: Frontend

```powershell
# Navigate to Frontend
cd "c:\Users\Makrembz\OneDrive\Desktop\Vectors in Orbit\FinFind\Frontend"

# Run the development server
npm run dev
```

You should see:
```
▲ Next.js 16.x.x
- Local:        http://localhost:3000
- Ready in Xs
```

### Option B: Run with Docker (Alternative)

```powershell
# Navigate to project root
cd "c:\Users\Makrembz\OneDrive\Desktop\Vectors in Orbit\FinFind"

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

---

## ✅ Verify Everything Works

### 1. Check Backend Health

Open your browser and go to:
```
http://localhost:8000/health
```

You should see:
```json
{"status": "healthy", "service": "finfind-api"}
```

### 2. Check API Documentation

Open your browser and go to:
```
http://localhost:8000/docs
```

You should see the Swagger UI with all API endpoints.

### 3. Open Frontend

Open your browser and go to:
```
http://localhost:3000
```

You should see the FinFind application!

### 4. Test a Search (Optional)

1. In the frontend, try searching: `"laptop for students"`
2. Check backend terminal for logs
3. Results should appear based on your Qdrant data

---

## 🔧 Quick Reference Commands

### Starting the Project

| Component | Command | URL |
|-----------|---------|-----|
| Backend | `python run.py --reload` | http://localhost:8000 |
| Frontend | `npm run dev` | http://localhost:3000 |
| Docker (all) | `docker-compose up -d` | Both ports |

### Stopping the Project

| Method | Command |
|--------|---------|
| Manual | Press `Ctrl+C` in each terminal |
| Docker | `docker-compose down` |

### Useful URLs

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Frontend Application |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | API Documentation (Swagger) |
| http://localhost:8000/health | Health Check |

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Python not found" or Wrong Version

```powershell
# Check if Python 3.11+ is installed
python --version

# If not installed, download from python.org
# Make sure to check "Add to PATH" during installation
```

#### 2. "npm not found"

```powershell
# Check Node.js installation
node --version

# If not installed, download from nodejs.org
# Restart terminal after installation
```

#### 3. "GROQ_API_KEY not set" Error

```
Make sure:
1. .env file exists in project root
2. GROQ_API_KEY has a value (not empty)
3. No quotes around the API key
4. Restart the backend after editing .env
```

#### 4. "Cannot connect to Qdrant" Error

```
Make sure:
1. QDRANT_URL is correct (check Qdrant Cloud dashboard)
2. QDRANT_API_KEY is correct
3. Your cluster is running (not paused)
4. No firewall blocking the connection
```

#### 5. Port Already in Use

```powershell
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or use a different port
python run.py --port 8001
```

#### 6. Module Not Found Error

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 7. Frontend Build Errors

```powershell
# Delete node_modules and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

---

## 📁 Project Structure Overview

```
FinFind/
├── .env                    # YOUR API KEYS (create this!)
├── .env.example            # Template for .env
├── backend/                # Python/FastAPI backend
│   ├── venv/              # Python virtual environment (created by you)
│   ├── requirements.txt   # Python dependencies
│   ├── run.py             # Entry point: python run.py
│   └── app/               # Application code
│       ├── api/           # API routes
│       ├── agents/        # AI agents
│       └── config.py      # Configuration
├── Frontend/              # Next.js frontend
│   ├── node_modules/      # JS dependencies (created by npm install)
│   ├── package.json       # JS dependencies list
│   └── src/               # React components
└── docker-compose.yml     # Docker configuration
```

---

## 🎯 Next Steps

Once everything is running:

1. **Load Demo Data**: Run `python demo/demo_data.py` to export demo data
2. **Explore the API**: Check http://localhost:8000/docs
3. **Try the Demo Scenarios**: See [demo/DEMO_SCRIPTS.md](demo/DEMO_SCRIPTS.md)
4. **Read the Documentation**: See [docs/](docs/) folder

---

## ❓ Need Help?

- Check [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for technical details
- Check [docs/API.md](docs/API.md) for API reference
- Open an issue on GitHub if you're stuck

---

**Happy coding! 🚀**
