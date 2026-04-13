# 📈 MarketMind — AI-Powered Stock Intelligence Platform

> Real-time stock analysis with ML predictions, technical indicators, and LLM-driven trading recommendations.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react)
![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🧠 What is MarketMind?

MarketMind is an advanced real-time stock intelligence platform that combines traditional financial data with AI-driven sentiment analysis and machine learning. It provides a comprehensive dashboard to monitor market trends, analyze technical indicators, and receive AI-powered trading recommendations.

---

## 🏗️ Architecture

MarketMind is built as a **decoupled full-stack application** — a high-performance Python backend paired with a reactive React frontend.

```
┌─────────────────────────────────────────────────┐
│               React Frontend (Vite)              │
│   TanStack Query · Recharts · Tailwind CSS       │
└────────────────────┬────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────┐
│             FastAPI Backend                      │
│  yfinance · scikit-learn · Groq (Llama 3.3 70B) │
│  Technical Analysis (RSI, MACD, Bollinger Bands) │
└─────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|--------|-------------|
| 🤖 **AI Trading Analyst** | Groq Llama 3.3 70B generates Buy/Sell/Hold recommendations with reasoning |
| 📊 **Technical Indicators** | RSI (14), MACD, and Bollinger Bands computed in real-time |
| 🔮 **ML Price Predictions** | scikit-learn models predict 1-day, 7-day, and 30-day price targets |
| 💬 **Social Sentiment** | Tracks Reddit mentions and Buzz scores for retail investor interest |
| 🔍 **Smart Ticker Resolution** | Type "Apple" → AI resolves to AAPL automatically |
| 🏥 **Health Diagnostics** | Built-in checks for Finnhub, Alpha Vantage, and Groq service status |
| 📱 **Responsive UI** | Seamless experience across desktop and mobile |

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** + **Uvicorn** + **Pydantic**
- **yfinance** — real-time market data
- **scikit-learn** — ML price predictions
- **Groq SDK** (Llama 3.3 70B) — AI analyst
- **ta** — Technical Analysis library
- **Pandas**, **NumPy** — data processing

### Frontend
- **React 19** + **Vite**
- **Tailwind CSS** — styling
- **TanStack Query** — data fetching & sync
- **Recharts** — interactive financial charts
- **react-window** — optimized list rendering

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- API Keys: Groq, Finnhub, Alpha Vantage

---

### 1. Clone the Repository

```bash
git clone https://github.com/nikhilesh/marketmind.git
cd marketmind
```

---

### 2. Backend Setup (FastAPI)

```bash
# Navigate to backend directory
cd marketmind

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
source venv/bin/activate           # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `marketmind/` directory:

```env
GROQ_API_KEY=your_groq_api_key
FINNHUB_API_KEY=your_finnhub_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
```

Start the backend server:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Backend will be running at: `http://127.0.0.1:8000`

---

### 3. Frontend Setup (React + Vite)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

Frontend will be running at: `http://localhost:5173`

---

## 📁 Project Structure

```
marketmind/
├── marketmind/              # FastAPI Backend
│   ├── main.py              # Entry point & API routes
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # API keys (not committed)
├── frontend/                # React Frontend
│   ├── src/
│   │   ├── components/      # UI components
│   │   └── App.jsx          # Root component
│   ├── package.json
│   └── .env                 # Frontend env vars
└── README.md
```

---

## 🔑 API Keys Required

| Service | Purpose | Get it here |
|---------|---------|-------------|
| [Groq](https://console.groq.com) | LLM AI Analysis | console.groq.com |
| [Finnhub](https://finnhub.io) | Market News & Sentiment | finnhub.io |
| [Alpha Vantage](https://www.alphavantage.co) | Stock Price Data | alphavantage.co |

> All three have **free tiers** — no credit card required.

---

## 👤 Author

**Nikhilesh Padhan**
- 🌐 [nikhil.dev](https://nikhil.dev)
- 💼 [LinkedIn](https://linkedin.com/in/nikhilesh)
- 🐙 [GitHub](https://github.com/nikhilesh)

---

## 📄 License

This project is licensed under the MIT License.

---

> Built with ❤️ by Nikhilesh Padhan — *"Data holds the answers to problems most people haven't thought to ask yet."*
