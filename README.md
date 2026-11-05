# ♻️ ReSource AI — Industrial Waste Exchange Platform

> **AI-Powered Industrial Circular Economy & Waste Upcycling Marketplace**  
> Connecting manufacturing suppliers that generate unused or scrap materials with enterprise buyers who repurpose them as secondary raw inputs.

---

## 🌟 Overview & Key Features

- **Multimodal AI Material Analysis**: When a material is uploaded, AI analyzes its chemical/physical composition, verifies whether it contains hazardous or regulated components, generates 3–5 viable circular reuse applications, suggests 3–5 candidate industries, and computes a 0–100 sustainability index.
- **Demo AI Fallback (Zero Config Required)**: If no Gemini API key is configured or an external network call fails, ReSource AI seamlessly switches to its built-in rule-based keyword & heuristic analyzer with automatic JSON repair. The entire application runs out of the box with zero setup!
- **Intelligent Multi-Factor Matching**: Computes a 0–100 compatibility score between buyer demand requests and supplier streams using material category, keyword overlap, target industries, volume parity, and geographic proximity, accompanied by a clear "Why this matches" explanation.
- **Threaded Real-Time Inquiries**: Direct buyer-to-supplier communication channel to negotiate technical specs, batch volume, pricing, and freight delivery with unread counters.
- **Role-Aware Dashboards**: Dedicated portals for Suppliers (stream listings, inquiries, buyer matches) and Buyers (demand requests, recommended listings, active conversations).
- **Circularity Impact Analytics**: Real-time estimations of total industrial landfill waste diverted (kg), avoided Scope 3 CO2 emissions (MT CO2e), and procurement cost savings, with real-world EPA equivalencies (cars off road, trees planted).
- **Safety & Regulatory Compliance**: Prominent hazard warnings for chemicals, spent acids, and regulated streams enforcing OSHA/REACH compliant handling and transportation manifests.
- **Pre-Seeded Real Data**: 21 realistic industrial streams across 10 categories, 8 buyer demand requests, and 2 ready-to-use corporate demo accounts.

---

## 🚀 Quick Start Guide (For Absolute Beginners)

### Method 1: The 1-Click Launch Script (Recommended)

#### On Windows:
Double-click `start.bat` (or open Command Prompt and run `start.bat`).  
The script will automatically:
1. Create `.env` from `.env.example` if not already present.
2. Initialize the Python virtual environment and install all dependencies.
3. Install frontend node packages if missing.
4. Launch the FastAPI backend on **http://localhost:8000** (with docs at **/docs**).
5. Launch the React Vite frontend on **http://localhost:3000**.
6. Automatically open your browser to the app!

#### On macOS or Linux:
Open Terminal in the `resource_ai` directory and run:
```bash
chmod +x start.sh
./start.sh
```

---

### Method 2: Manual Start (Step-by-Step)

#### Step 1: Start the Backend
Open a terminal in `resource_ai/backend`:
```bash
# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API and interactive documentation will be live at:
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health**: [http://localhost:8000/api](http://localhost:8000/api)

#### Step 2: Start the Frontend
Open a second terminal in `resource_ai/frontend`:
```bash
# Install node packages
npm install

# Start Vite development server
npm run dev
```
Open your browser and navigate to:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## 🔑 Demo Login Accounts

You can log in instantly using the **1-Click Demo Login** buttons on the login page:

| Role | Email | Password | Company Name | City |
| :--- | :--- | :--- | :--- | :--- |
| **Supplier** | `supplier@demo.com` | `password123` | Apex EcoMaterials Corp | Chicago, IL |
| **Buyer** | `buyer@demo.com` | `password123` | GreenForge Manufacturing Ltd | Detroit, MI |

You can also register a new account as either a **Supplier** or a **Buyer** directly through the registration form.

---

## 🤖 (Optional) Configuring Google Gemini API Key

The platform works **100% out of the box** without any API key using its built-in rule-based circular analyzer. If you want to enable live Google Gemini Multimodal AI:

1. Visit **[Google AI Studio](https://aistudio.google.com/)**.
2. Sign in with your Google Account and click **"Get API key"** -> **"Create API key"** (free tier available).
3. Open the `.env` file in the `resource_ai` folder.
4. Paste your key in `GEMINI_API_KEY`:
   ```ini
   GEMINI_API_KEY=AIzaSyYourActualGeminiKeyHere
   GEMINI_MODEL=gemini-2.5-flash
   ```
5. Restart your backend server. The app will now use live Gemini AI models and display a **"Gemini Live AI"** badge!

---

## 🧪 Running Automated Backend Tests

ReSource AI includes a complete automated test suite covering authentication, listing CRUD, AI analysis, schema repair, compatibility matching, inquiries, and file upload validations:

```bash
# Windows
cd backend
venv\Scripts\pytest tests -v

# Mac/Linux
cd backend
venv/bin/pytest tests -v
```

All 20 tests pass with zero errors.

---

## 🛠️ Architecture & Tech Stack

```
resource_ai/
├── backend/
│   ├── app/
│   │   ├── config.py             # App configuration & .env loader
│   │   ├── database.py           # SQLAlchemy SQLite connection
│   │   ├── models.py             # User, Listing, Request, Inquiry models
│   │   ├── schemas.py            # Pydantic validation schemas
│   │   ├── auth.py               # Pure-python PBKDF2 password hashing & JWT
│   │   ├── ai_service.py         # Gemini API + Fallback Rule-Based Analyzer
│   │   ├── matching_service.py   # Multi-attribute circular matching engine
│   │   ├── seed_data.py          # Auto-seeds 21 listings, 8 requests, 2 accounts
│   │   ├── main.py               # FastAPI application & lifespan setup
│   │   └── routers/              # Clean REST endpoints under /api
│   ├── tests/                    # 20 automated pytest test cases
│   ├── uploads/                  # Uploaded material photos storage
│   └── requirements.txt          # Pinned backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/           # Navbar, Footer, AIAnalysisCard, Cards, Modals
│   │   ├── context/              # AuthContext (JWT session state)
│   │   ├── pages/                # 10 application pages
│   │   ├── services/api.js       # Axios HTTP client with interceptors
│   │   ├── App.jsx               # React Router v6 setup
│   │   └── index.css             # Tailwind CSS styling
│   └── package.json              # Pinned frontend dependencies
├── start.bat                     # 1-Click Windows start launcher
├── start.sh                      # 1-Click Mac/Linux start launcher
└── README.md                     # Beginner documentation
```

---

## ❓ Troubleshooting & FAQs

### 1. Port 8000 or 3000 is already in use
- If another program is using port 8000, you can run uvicorn on another port (e.g. `python -m uvicorn app.main:app --port 8001`) and update `target` in `frontend/vite.config.js`.
- If port 3000 is in use, Vite will automatically suggest port 3001.

### 2. "Python is not recognized as an internal or external command" on Windows
- Use the `py` launcher, which is included with modern Python installations on Windows.
- Make sure "Add Python to PATH" was checked when installing Python.

### 3. Will the app crash if my Gemini API key expires or has no quota?
- **No.** ReSource AI is engineered with an automatic fallback mechanism. If any Gemini API call fails, times out, or returns invalid data, the system catches the error, validates and repairs the JSON schema, and uses the built-in rule-based circular analyzer with a "Demo AI Mode" badge.

---

## 📄 License
This project is open-source under the MIT License. Built for industrial sustainability and circular economy advancement.
