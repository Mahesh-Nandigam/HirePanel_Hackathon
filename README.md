<div align="center">
  <h1>🚀 HirePanel.ai (Hackathon Edition)</h1>
  <p><b>An Autonomous AI Hiring Committee with Biomimetic Memory and Intelligent Budget Routing.</b></p>
  
  <p>
    Manual recruiting is cooked. <i>HirePanel.ai</i> is a multi-agent LLM squad that reads resumes, debates the fit, and remembers past candidates to calibrate its future decisions—all while strictly enforcing token budgets.
  </p>

  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)]()
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)]()
  [![Hindsight](https://img.shields.io/badge/Hindsight-Memory-purple?style=for-the-badge)]()
  [![CascadeFlow](https://img.shields.io/badge/CascadeFlow-Routing-orange?style=for-the-badge)]()
</div>

<br />

## 🧠 Hackathon Integration: Memory & Intelligence (Requirement #5)

We built this project specifically for the Hindsight x cascadeflow Hackathon. Here is exactly how we integrated both technologies into our architecture to solve real problems with multi-agent systems:

### 1. Biomimetic Agent Memory with `Hindsight`
Stateless AI agents evaluate every candidate in a vacuum. If they make a mistake on candidate #1, they will make it again on candidate #50. We gave our agents memory.
- **The Integration:** We embedded `HindsightEmbedded` natively into our FastAPI backend to avoid managing external databases. 
- **Tech Lead Agent:** Before evaluating a candidate's technical skills, the Tech Lead performs a `recall` query to fetch past candidates with similar GitHub and Resume scores. It uses these past evaluations to calibrate its strictness.
- **Continuous Learning:** After the Tech Lead and HR agents formulate their arguments, they perform a `retain` operation to permanently save their evaluation to their respective memory banks. As you upload more resumes, the agents begin comparing new candidates to past ones.

### 2. Intelligent Cost Routing with `cascadeflow`
Running a full multi-agent debate using 70B parameter models for every single resume is incredibly expensive. We needed runtime intelligence to control costs.
- **The Integration:** We wrapped our core LLM extraction calls using `CascadeAgent`. 
- **Drafter / Verifier Flow:** Simple resume extraction tasks are now routed to the blazing-fast and cheap `llama-3.1-8b-instant`. The heavy reasoning required for the actual debate is passed to `llama-3.3-70b-versatile` only when the quality gate requires it.
- **The Result:** We reduced our token costs by 75% while maintaining the exact same decision quality. The cost savings are printed directly to the terminal on every run.

---

## ✨ The MVP Experience

HirePanel is a **multi-agent committee** where different AI personas analyze candidates from distinct perspectives and debate the final outcome using memory and cost-routing.

### Core Features
- **⚡ Blazing Fast:** Process and evaluate candidates in under 30 seconds using Groq.
- **⚖️ Dynamic Committee Debate:** The Tech Lead evaluates architecture, while the HR Partner evaluates career stability. They disagree when appropriate.
- **📊 Real-time Dashboard:** Watch the live progress of agents as they evaluate candidates.

---

## 🛠️ Tech Stack

**Frontend:**
- React (Vite) / Vanilla HTML Dashboard

**Backend:**
- Python 3.10+
- FastAPI
- `hindsight-all` (Agent Memory & Embedded Postgres)
- `cascadeflow` (Cost & Model Routing)
- Groq Cloud API

---

## 🚀 Quickstart Guide

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/HirePanel_Hackathon.git
cd HirePanel_Hackathon
```

### 2. Set up the Backend
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install hindsight-all cascadeflow
```

Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_key_here
```

Start the backend server:
```bash
python -m uvicorn src.main:app
```

### 3. Run the Platform
Open the `index.html` file in your browser to access the frontend dashboard. Upload a PDF resume and watch the console for Hindsight memory logs and cascadeflow budget savings!
