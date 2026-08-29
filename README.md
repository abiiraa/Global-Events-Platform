# 🏟️ Global Event Platform

**Imagine millions of fans rushing to buy tickets to the biggest sporting event of the year.** Servers crash, queues freeze, and fans leave angry. 

*Not here.*

The **Global Event Platform** is a production-grade, event-driven ticketing system built entirely on AWS Serverless and DynamoDB. It is engineered from the ground up to handle extreme concurrency, ensure absolute fairness, and deliver a seamless fan journey — from the very first queue position to the final halftime whistle.

**Built exclusively by [Abira Aamir](https://github.com/abiiraa).**

![Stack](https://img.shields.io/badge/React-19-blue?style=flat-square) ![Stack](https://img.shields.io/badge/AWS_Lambda-Python_3.14-orange?style=flat-square) ![Stack](https://img.shields.io/badge/DynamoDB-Single_Table-yellow?style=flat-square) ![Stack](https://img.shields.io/badge/SAM-Serverless-green?style=flat-square)

---

## 📑 Table of Contents

- [The Fan Journey (Overview)](#-the-fan-journey-overview)
- [How It Works (Architecture)](#-how-it-works-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Clone & Setup](#-clone--setup)
- [Deploying the Backend (AWS)](#-deploying-the-backend-aws)
- [Running the Frontend Locally](#-running-the-frontend-locally)
- [Deploying the Frontend (Vercel)](#-deploying-the-frontend-vercel)
- [Environment Variables](#-environment-variables)
- [Running Tests](#-running-tests)
- [Admin Portal](#-admin-portal)
- [Project Structure](#-project-structure)
- [Key Design Decisions](#-key-design-decisions)
- [Inspiration](#-inspiration)

---

## 🎢 The Fan Journey (Overview)

The platform is broken down into four massive, highly-scalable modules. 

| What happens? | Module | Status |
|---|---|---|
| **1. The Queue** | **Virtual Waiting Room:** Fairly queues fans and controls admission into the ticket purchasing flow. | ✅ Live — 11 Lambdas · 150 tests |
| **2. The Purchase** | **Fair Seat Purchase:** Holds and sells every seat *exactly once* under massive concurrent demand. | ✅ Live — 9 Lambdas · 44 tests |
| **3. The Match** | **Stadium Concessions:** Ingests and routes high-volume halftime food orders to the closest stands. | ✅ Live — 8 Lambdas · Full test suite |
| **4. The Glory** | **Infinite Leaderboard:** High-write leaderboards tracking fan engagement with instant rank reads. | ✅ Live — 8 Lambdas · Full test suite |

---

## 🏗️ How It Works (Architecture)

Every action in the system is event-driven. Modules never talk directly to each other; instead, they broadcast events to an Amazon EventBridge bus. 

```text
Fan joins queue
  → Waiting room assigns a fair position (FIFO)
  → Admission controller promotes capacity-sized batches
  → Purchase session created (time-limited)
  → Seat held atomically via DynamoDB conditional write
  → Payment confirms the seat as sold
  → Waiting room frees admission capacity
  → EventBridge fans out to downstream modules!
```

*Every single module owns its own DynamoDB table. There are no cross-module joins, ensuring perfect isolation and independent scaling.*

---

## 💻 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19 · Vite 8 · TypeScript 6 · Tailwind CSS v4 |
| **Auth** | AWS Cognito (`aws-amplify`) |
| **Backend** | Python 3.14 · AWS Lambda · AWS SAM (nested stacks) |
| **Database** | Amazon DynamoDB (one single-table design per module) |
| **Events** | Amazon EventBridge (custom bus) |
| **API** | Amazon API Gateway (REST) |
| **Observability** | AWS Lambda Powertools (structured logging, tracing) |
| **Hosting** | Vercel (Frontend) · AWS SAM (Backend) |

---

## 🛠️ Prerequisites

Make sure the following are installed before you start:

- Node.js 20+
- Python 3.14+
- AWS CLI v2
- AWS SAM CLI (latest)
- Git

You also need an **AWS account** with programmatic access configured.

---

## 🚀 Clone & Setup

```bash
git clone https://github.com/your-username/global-event-platform.git
cd global-event-platform
```

---

## ☁️ Deploying the Backend (AWS)

### 1. Configure AWS credentials

```bash
aws configure
# Enter: Access Key ID, Secret Access Key, region (us-east-1), output format (json)
```

### 2. Create a deployment S3 bucket (one-time)

SAM needs an S3 bucket to upload Lambda packages. Create one with a unique name:

```bash
aws s3 mb s3://gsep-platform-deployments-<your-aws-account-id> --region us-east-1
```

Then update `backend/samconfig.toml` — change the `s3_bucket` line to match:

```toml
s3_bucket = "gsep-platform-deployments-<your-aws-account-id>"
```

### 3. Set up the Python virtual environment

```bash
cd backend
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 4. Build and deploy

```bash
# Still inside backend/
sam build
sam deploy
```

SAM will show a changeset and ask for confirmation before deploying. Type `y`.
*(First time only: if `samconfig.toml` doesn't exist yet, run `sam deploy --guided` instead).*

### 5. Grab the API URLs

After deploy completes, SAM prints the stack outputs. Copy the four API Gateway URLs — you'll need them for the frontend `.env`.

---

## 💻 Running the Frontend Locally

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values (using the API URLs from your backend deployment):

```env
VITE_API_BASE_URL=https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod
VITE_SEAT_PURCHASE_API_URL=https://yyyyyyyyyy.execute-api.us-east-1.amazonaws.com/Prod
VITE_CONCESSIONS_API_URL=https://zzzzzzzzzz.execute-api.us-east-1.amazonaws.com/Prod
VITE_LEADERBOARD_API_URL=https://wwwwwwwwww.execute-api.us-east-1.amazonaws.com/Prod
VITE_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
VITE_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxx
VITE_ADMIN_EMAIL=admin@gsep.com          # must match AdminEmail in samconfig.toml
VITE_ADMIN_PASSWORD=admin123!            # must match AdminPassword in samconfig.toml
VITE_USE_REAL_API=true
```

*(Tip: Set `VITE_USE_REAL_API=false` to run entirely in localStorage mock mode with no AWS needed!)*

### 3. Start the dev server

```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173).

---

## 🌐 Deploying the Frontend (Vercel)

The easiest way is via the **Vercel GitHub integration**:

1. Push your repo to GitHub
2. Go to [vercel.com](https://vercel.com) → **Add New Project** → import your repo
3. Set **Root Directory** to `frontend`
4. Under **Environment Variables**, add all 9 variables listed above!
5. Click **Deploy**

Every `git push` to `main` triggers a new deployment automatically.

---

## 🔑 Environment Variables

### Frontend (`frontend/.env`)

These variables connect your frontend to your AWS backend. **Crucially, `VITE_ADMIN_EMAIL` and `VITE_ADMIN_PASSWORD` must exactly match the values deployed in your backend `samconfig.toml`**, otherwise the admin portal will return HTTP 403 errors!

### Backend (`backend/samconfig.toml`)

The `parameter_overrides` line controls credentials injected into Lambda env vars at deploy time:
```toml
parameter_overrides = "StageName=\"Prod\" AdminEmail=\"admin@gsep.com\" AdminPassword=\"admin123!\" AdminApiKey=\"replace-with-real-key\""
```
*(Run `sam build && sam deploy` if you change these).*

---

## 🧪 Running Tests

The platform includes extensive testing across all modules.

```bash
# Waiting Room (150 unit tests)
cd backend/modules/waiting-room
pytest tests/unit/ -v

# Seat Purchase (44 unit tests)
cd backend/modules/seat-purchase
pytest tests/unit/ -v

# Concessions
cd backend/modules/concessions
pytest tests/ -v

# Leaderboard
cd backend/modules/leaderboard
pytest tests/ -v
```

---

## 👑 Admin Portal

Manage events through the built-in admin portal at `/admin`.
- Creates events directly in DynamoDB via `POST /event` — visible to all users immediately.
- The header shows `⚡ Live API` or `💾 Local` so you always know which mode is active.

---

## 📁 Project Structure

```text
global-event-platform/
├── backend/
│   ├── template.yaml                    # Root SAM stack + EventBridge bus
│   ├── samconfig.toml                   # SAM deploy config
│   └── modules/
│       ├── waiting-room/                # Module 1 (11 Lambdas, 150 tests)
│       ├── seat-purchase/               # Module 2 (9 Lambdas, 44 tests)
│       ├── concessions/                 # Module 3 (8 Lambdas, full test suite)
│       └── leaderboard/                 # Module 4 (8 Lambdas, full test suite)
├── frontend/
│   ├── src/
│   │   ├── pages/                       # 11 pages (Landing, Dashboard, Admin, etc.)
│   │   ├── context/AuthContext.tsx      # AWS Cognito integration
│   │   └── router.tsx                   # React Router
├── docs/                                # Architecture & ADRs
└── README.md
```

---

## 🧠 Key Design Decisions

- **One table per module:** Each bounded context has its own DynamoDB table — independent scaling, independent access patterns, no cross-module joins.
- **Conditional writes for correctness:** Every state-changing operation (hold a seat, admit a fan, consume a token) uses `ConditionExpression`. Concurrent requests are safe by construction, not by locks.
- **EventBridge for cross-module communication:** Modules never call each other directly. Swapping or scaling any module doesn't affect the others.
- **FIFO admission fairness:** Queue positions are stamped at join time. The admission controller always promotes the lowest-position fans first.
- **Idempotent Lambda handlers:** Every handler is safe to retry. DynamoDB conditional writes turn a duplicate execution into a no-op rather than a data corruption.

---

## 💡 Inspiration

This platform was originally inspired by [@Afffan16](https://github.com/Afffan16)'s submission to the **[Virtual Waiting Room Challenge](https://github.com/Afffan16/football-virtual-waiting-room)** from the **DynamoDB Series** run by **John Terhune**. That original football-platform concept demonstrated how DynamoDB's conditional writes and single-table design could fairly manage millions of concurrent fans entering a virtual queue.

This repository takes that foundational concept and scales it out into a comprehensive, multi-module global ticketing system. 
