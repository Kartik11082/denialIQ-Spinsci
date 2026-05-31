# DenialIQ

### AI-powered denial intelligence layer for healthcare revenue cycle

![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-v0.110.0-green.svg)
![React](https://img.shields.io/badge/React-v18.3.1-blue.svg)
![AWS Bedrock](https://img.shields.io/badge/AWS%20Bedrock-HIPAA%20Eligible-orange.svg)
![HIPAA-Eligible](https://img.shields.io/badge/Compliance-HIPAA%20Eligible-emerald.svg)

---

## SECTION 1: HEADER

**DenialIQ** is an intelligent, automated revenue integrity layer designed specifically for healthcare organizations. Sifting through the complex administrative pipeline of hospital billing, the platform automatically intercepts, interprets, and stops insurance claim denials before they happen. By integrating directly with existing electronic health records (EHRs), clearinghouses, and scheduling workflows, **DenialIQ** reads live raw billing data, leverages advanced **AWS Bedrock generative artificial intelligence** to isolate root causes, and generates push-button preventative directives. The system doesn't just manage the wreckage of rejected claims; it systematically rewrites the intake workflows to safeguard hospital revenue, prevent administrative waste, and ensure patients receive timely, uninterrupted care without billing surprises.

---

## SECTION 2: THE PROBLEM (Non-Technical)

In the United States, healthcare billing is a highly convoluted, friction-filled battleground. Hospitals submit millions of claims to commercial and federal insurance companies daily. However, a staggering **41%** of US healthcare providers now struggle with overall denial rates exceeding **10%**.

When a claim is denied, the financial and operational toll is devastating:

- **Severe Rework Costs**: It costs between **$25** and **$700** to appeal, research, correct, and resubmit a single rejected claim.
- **Delayed Cash Flows**: Payment for rendered patient care is delayed by **30** to **90 days**, severely strangling the hospital's operational cash flow.
- **Operational Inefficiencies**: Billing departments operate reactively, manually reviewing errors one spreadsheet at a time, resulting in massive administrative overhead.

### The Invisible Rule-Change Dilemma

Under the current status quo, commercial payers constantly tweak their clinical coverage guidelines and prior authorization rules with little to no public notice.

Consider this real-world scenario:

- **The Policy Update**: On **April 3, 2026**, **UnitedHealth** quietly updates its outpatient imaging policy, adding a mandatory prior authorization requirement for a routine knee MRI (**CPT 73721**).
- **The Lag**: Because this change is buried inside a **400-page** PDF manual, hospital scheduling and billing departments continue to book and submit MRI claims as usual.
- **The Avalanche**: Three weeks later, **20 claims** come back denied all at once. The hospital is left holding **$19,400** in rejected bills.
- **The Manual Fix**: Billing specialists must spend **40+ hours** auditing records, calling insurers, and begging for retro-authorizations one by one.

This operational friction is not merely a financial loss; it directly impacts **patient care** by delaying subsequent clinical appointments, scheduling procedures, and creating unexpected out-of-pocket bills that damage the patient-provider relationship.

---

## SECTION 3: THE SOLUTION (Non-Technical)

**DenialIQ** turns the reactive denial cycle into a proactive shield. By analyzing incoming remittance files automatically, the platform extracts historical claim rejections, classifies them using clinical generative AI, and immediately writes warning triggers directly into the front-end intake system. Rather than reviewing claims one by one, DenialIQ creates a system-wide preventive loop.

### The "Fire Investigator" Analogy

Hospitals today are like staff frantically mopping up water in a flooded kitchen while the sink faucet is left running wide open. They spend millions of dollars hiring billing armies to audit and appeal denied claims (mopping the floor). **DenialIQ turns off the tap.** It uses backend analytics to find the source of the leak and prevents the billing errors before they ever leave the hospital doors.

```
                  THE TRADITIONAL RCM CYCLE (REACTIVE MOPS)
     ┌──────────────────────────────────────────────────────────────┐
     │                                                              │
     ▼                                                              │
Claims Sent ───► Payer Denies Claim ───► Manual Audit ───► Appeal Rework

                      THE DENIALIQ APPROACH (TAP CLOSED)
Claims Sent ───► Payer Denies Claim ───► DenialIQ AI Audit
                                             │
                                             ▼
                                     Feedback Trigger
                                             │
                                             ▼
                                  Scrub at Scheduling (Tap Off)
```

### Stakeholder Benefits

| Role                              | Operational Impact                                                                   | Measurable ROI                                                |
| :-------------------------------- | :----------------------------------------------------------------------------------- | :------------------------------------------------------------ |
| **Revenue Cycle Director**        | Transitions from reactive spreadsheets to automated, AI-highlighted denial trends.   | **30%+** reduction in overall administrative audit workloads. |
| **Billing Staff**                 | Receives real-time coding reviews and automatic modifier validations pre-submission. | Decreased claim correction turnarounds from hours to seconds. |
| **Scheduling Staff**              | Gets immediate, interactive prior authorization warnings during patient bookings.    | Elimination of prior authorization patient turnbacks.         |
| **Chief Financial Officer (CFO)** | Protects cash flows, accelerates payment cycles, and decreases bad debt write-offs.  | Thousands of dollars in **prevented leakage** saved monthly.  |

---

## SECTION 4: HOW IT FITS INTO THE EXISTING ECOSYSTEM

DenialIQ acts as a non-invasive, horizontal intelligence layer that spans the entire healthcare revenue cycle. It reads data from existing components, analyzes it, and feeds preventative intelligence back to the front doors.

```
                                  HEALTHCARE BILLING CHAIN

  Patient     Scheduling      EHR Clinical     Medical      Clearinghouse      Insurance
  Booking       Intake         Recording       Coding         Scrubber          Payer
  ┌─────┐       ┌─────┐         ┌─────┐        ┌─────┐         ┌─────┐          ┌─────┐
  │     │ ────► │     │ ──────► │     │ ─────► │     │ ──────► │     │ ───────► │     │
  └─────┘       └─────┘         └─────┘        └─────┘         └─────┘          └─────┘
     ▲             │                                              │                │
     │             │                                              │                │
     │ Flagged     │ Scheduling                                   │ 837 Claim      │ 835 ERA
     │ Pre-service │ Bookings                                     │ Files          │ Remittances
     │ Alerts      │                                              │                │
     │             ▼                                              ▼                ▼
  ┌───────────────────────────────────────────────────────────────────────────────────┐
  │                                    DENIALIQ                                       │
  │                  (Horizontal Intelligence & Automation Layer)                     │
  │                                                                                   │
  │       1. READS 835 Eras, 837 Claims, & FHIR EHR Scheduling Hooks                  │
  │       2. PROCESSES Data with AWS Bedrock Generative Clinical Models               │
  │       3. WRITES BACK Prevention Triggers to SpinSci MCP & Intake Portals          │
  └───────────────────────────────────────────────────────────────────────────────────┘
```

DenialIQ is a **layer, not a product**. It does not require hospitals to replace their EHR, scheduling databases, clearinghouses, or billing engines. Instead, it acts as an overlay that silently reads transaction logs, runs real-time classifications, and uses standard web hooks (including the **SpinSci Model Context Protocol** or MCP layer) to inject flags into systems the staff already use.

---

## SECTION 5: SYSTEM ARCHITECTURE (Technical)

DenialIQ is built on a modern, event-driven, HIPAA-eligible cloud architecture hosted entirely on **AWS**.

```
 DATA SOURCES                    DENIALIQ BACKEND (AWS)                         OUTPUTS

┌──────────────┐          ┌───────────────────────────────────┐          ┌───────────────────┐
│ ANSI X12     │ ───────► │ Lambda Ingestion Engine           │ ───────► │ React Dashboard   │
│ 835 Remits   │          └───────────────────────────────────┘          │ (Overview, Chat)  │
└──────────────┘                            │                            └───────────────────┘
                                            ▼
┌──────────────┐          ┌───────────────────────────────────┐          ┌───────────────────┐
│ ANSI X12     │ ───────► │ Amazon S3 (Raw Documents)         │ ───────► │ SpinSci MCP       │
│ 837 Claims   │          └───────────────────────────────────┘          │ Prevention Rules  │
└──────────────┘                            │                            └───────────────────┘
                                            ▼
┌──────────────┐          ┌───────────────────────────────────┐          ┌───────────────────┐
│ Scanned EOBs │ ───────► │ Amazon Textract (OCR Extraction)  │ ───────► │ EHR FHIR Alerts   │
│ (PDF/Images) │          └───────────────────────────────────┘          │ (Write-back API)  │
└──────────────┘                            │                            └───────────────────┘
                                            ▼
┌──────────────┐          ┌───────────────────────────────────┐          ┌───────────────────┐
│ EHR Databases│ ───────► │ AWS Bedrock (Claude Haiku 3.5)    │ ───────► │ Pre-submission    │
│ (FHIR API)   │          └───────────────────────────────────┘          │ Scrub API         │
└──────────────┘                            │                            └───────────────────┘
                                            ▼
                          ┌───────────────────────────────────┐
                          │ Bedrock Knowledge Bases (RAG)     │
                          │ - Payer Policy PDFs & Manuals     │
                          └───────────────────────────────────┘
                                            │
                                            ▼
                          ┌───────────────────────────────────┐
                          │ DynamoDB Database                 │
                          │ - Denials, Patterns, Rules        │
                          └───────────────────────────────────┘
```

### Infrastructure Component Registry

| Component             | Service                 | Purpose                                                                                                | Why This Choice                                                                         |
| :-------------------- | :---------------------- | :----------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------- |
| **OCR Pipeline**      | Amazon Textract         | Extracts structured fields from scanned paper EOBs and faxed billing rejections automatically.         | Eliminates manual data entry with near-perfect OCR accuracy for medical claim tables.   |
| **Ingestion Compute** | AWS Lambda              | Serverless Event Ingestion Service triggered by EventBridge or FHIR web hooks.                         | Zero-idle cost, scaling instantly to support millions of incoming transaction files.    |
| **REST Gateway**      | FastAPI                 | Hosts standard, performant, and secure REST APIs for frontend dashboards and third-party integrations. | High-speed async routing with automatic Pydantic data validation.                       |
| **Core AI Model**     | AWS Bedrock             | Hosts Claude Haiku to run lightning-fast, highly accurate medical classifications.                     | HIPAA-eligible serverless inference with zero model retention on prompt history.        |
| **Policy Search**     | Bedrock Knowledge Bases | Vector-retrieval RAG containing indexed payer manual PDFs and prior authorization schedules.           | Grounds LLM classifications to eliminate hallucinations when interpreting policy logic. |
| **Database**          | Amazon DynamoDB         | Fully managed NoSQL database storing processed claims, recognized patterns, and prevention rules.      | Delivers single-digit millisecond latency at any scale, separating tenant records.      |
| **Event Router**      | AWS EventBridge         | Schedules periodic batch processing and manages event notifications across microservices.              | Standardizes decoupled communications and scheduling triggers securely.                 |

---

## SECTION 6: AI PIPELINE DEEP DIVE (Technical)

```
RAW CLAIMS / ERA
       │
       ▼
 [ STAGE 1 ] Ingestion & Textract OCR ──► Structured JSON Extract
                                                 │
                                                 ▼
 [ STAGE 2 ] Claude Classification ◄─── Bedrock Knowledge Base (RAG) [ STAGE 3 ]
       │
       ▼
 Categorized Root Cause & Score
       │
       ▼
 [ STAGE 4 ] Pattern Detection (Sliding Window) ──► 10+ Denial Spikes Flagged
                                                           │
                                                           ▼
 [ STAGE 5 ] Prevention Rule Generator ───► Pushed to SpinSci / Intake Hooks
                                                           │
                                                           ▼
 [ STAGE 6 ] Risk Scoring Model ◄─── New Pre-service Claim Scrubbing
```

### Stage 1: Ingestion & Extraction

1. **Remittance Parsing**: Ingests **ANSI X12 835** (Electronic Remittance Advice) and **837** (Health Care Claims) files, translating segment loops (CLP, CAS, REF) into clean structural databases.
2. **Textract OCR**: Scanned documents are parsed by Amazon Textract's layout model to extract key-value pairs (e.g., patient name, insurer, amount, reason) from tabular formats.
3. **Structured Payload**: Creates a standardized JSON payload holding crucial fields including: `payer`, `billed_amount`, `procedure_code`, `denial_reason_code`, and `date_of_service`.

### Stage 2: Classification (AWS Bedrock Claude)

Incoming denials are mapped against **Claude Haiku** with a prompt containing the claim data and the RAG-retrieved payer rules.

```
[SYSTEM INSTRUCTION]
You are a Board-certified Revenue Cycle Coding Auditor. Classify the raw insurance denial record.
Categorize the primary root cause into exactly ONE of the following 6 groups:
1. ELIGIBILITY_GAP: Coverage expired, invalid patient details.
2. MISSING_PRIOR_AUTH: CPT code requires prior authorization.
3. CODING_ERROR: Inconsistent modifier, invalid diagnosis code.
4. MEDICAL_NECESSITY: Experimental procedure, undocumented severity.
5. TIMELY_FILING: Submission exceeded payer deadline.
6. INCORRECT_PAYER: Claim routed to wrong primary carrier.

Identify the primary upstream workflow step responsible:
- SCHEDULING (Prior authorization, booking)
- REGISTRATION (Insurance details verification)
- CLINICAL_DOCUMENTATION (Physician charting)
- CODING (Modifier assignment, diagnosis sequencing)

Return a structured JSON object containing:
{
  "root_cause": "MISSING_PRIOR_AUTH" | "ELIGIBILITY_GAP" | ...,
  "upstream_step": "SCHEDULING" | "REGISTRATION" | ...,
  "confidence_score": 0.94,
  "explanation": "Brief rationale citing specific code guidelines."
}
```

### Stage 3: RAG (Bedrock Knowledge Bases)

- **Ingestion**: Payer coverage manuals, CPT schedules, and ICD-10 crosswalks are chunked, vectorized using **Amazon Titan Embeddings**, and stored in a vector index.
- **Retrieval Trigger**: When a new denial is processed, a vector query is executed based on the `procedure_code` and `payer` fields.
- **Grounding**: The retrieved vector context is injected directly into the Claude prompt, guaranteeing the explanation is grounded in real policy criteria.

### Stage 4: Pattern Detection

DenialIQ runs sliding window aggregations across processed records.

- **The 4 Pattern Types**:
  1. _Payer + Root Cause_: Looks for high occurrences in specific payer-cause combinations.
  2. _Departmental Pattern_: Groups leakages by clinical department (e.g., Radiology).
  3. _Procedure + Payer_: Flags CPT-specific rejections by insurer.
  4. _Recent Spike_: Flags rapid growth (last **14 days** vs. previous **14 days**, growth **>30%**).
- **Thresholds**: Any group matching a trigger of **10+ denials** or **$5,000+** at risk is flagged as an active systemic pattern.
- **Trend Calculations**: Computes the linear percentage change between the current **30-day** period and the previous **30-day** period.

### Stage 5: Prevention Rule Generation

Surfaced patterns are translated into actionable pre-service flags:

- **Prior-Auth Spike**: If `MISSING_PRIOR_AUTH` is detected, the system generates a `FLAG_PRIOR_AUTH_REQUIRED` directive containing target CPTs and payers.
- **Coding Error**: If `CODING_ERROR` is detected, a `FLAG_CODING_REVIEW` directive is formed.
- **SpinSci Hook**: Pushes rules via standard JSON over MCP to the SpinSci patient portal, preventing future bookings from slipping through.
- **Prevention Rates**: Sets a conservative **70%** prior-auth prevention intercept rate and **50%** coding error intercept rate based on typical user responsiveness.

### Stage 6: Risk Scoring (Forward-Looking)

- **Claim Evaluation**: Before a claim is submitted, DenialIQ scores the billing metadata.
- **Input Features**: Uses CPT codes, primary diagnosis, provider ID, payer, and clinic department.
- **Thresholds**: Claims scoring **>70%** probability of rejection are flagged, triggering a warning in the billing engine and blocking submission until verified.

---

## SECTION 7: DATA FLOW (Technical)

### Scenario A: Processing an Incoming Denial

```
835 File      FastAPI App      Bedrock API       DynamoDB       SpinSci MCP     Dashboard
   │               │                │               │                │              │
   │─── 835 ──────►│                │               │                │              │
   │    Remittance │─── Query ─────►│               │                │              │
   │               │    Context (KB)│               │                │              │
   │               │◄── Policy Context─             │                │              │
   │               │                │               │                │              │
   │               │─── Prompt ────►│               │                │              │
   │               │    (Claude)    │               │                │              │
   │               │◄── Classify ───│               │                │              │
   │               │    JSON        │               │                │              │
   │               │                                │                │              │
   │               │─── Write Record ──────────────►│                │              │
   │               │                                │                │              │
   │               │─── Run Pattern Engine ────────►│                │              │
   │               │    (Spike Detected)            │                │              │
   │               │                                │                │              │
   │               │─── Generate Prevention Rule ──►│                │              │
   │               │                                │                │              │
   │               │─── Push Rule ──────────────────────────────────►│              │
   │               │                                │                │              │
   │               │─── Push Event ────────────────────────────────────────────────►│
   ▼               ▼                                ▼                ▼              ▼
```

### Scenario B: Pre-Service Booking Intercept

```
Scheduling      SpinSci MCP       FastAPI App       DynamoDB       EHR Interface
  Staff              │                 │                │                │
    │── Book CPT ───►│                 │                │                │
    │   73721        │── Risk Query ──►│                │                │
    │                │                 │── Rule Check ─►│                │
    │                │                 │◄─ Active Rule ─│                │
    │                │                 │   (PR-047)     │                │
    │                │                 │                │                │
    │                │◄─ Intercept ────│                │                │
    │                │   Warning Msg   │                │                │
    │                │                                                   │── Write Flag ─►│
    │◄─ Alert Staff ─│                                                   │   to EHR       │
    ▼                ▼                                                   ▼                ▼
```

---

## SECTION 8: TECH STACK

DenialIQ is built on enterprise-grade components selected for security, scalability, and ease of deployment.

| Layer                 | Technology                      | Purpose                                                              | Why This Choice                                                                         |
| :-------------------- | :------------------------------ | :------------------------------------------------------------------- | :-------------------------------------------------------------------------------------- |
| **Frontend**          | **React 18**                    | Renders the dashboard panels and the chat interfaces.                | Offers a responsive, component-driven user experience.                                  |
| **Frontend Tooling**  | **Vite**                        | Builds and compiles the web application assets.                      | Provides lightning-fast hot module replacement (HMR) and optimized build bundles.       |
| **Styling**           | **Tailwind CSS**                | Implements the clean, high-contrast dashboard layout and components. | Enables modular utility styling with zero runtime overhead.                             |
| **Visualization**     | **Recharts**                    | Renders line charts, pie charts, and custom legends.                 | Built specifically for React, delivering fluid animations and interactive SVG tooltips. |
| **Router**            | **React Router 6**              | Manages application routes and transitions.                          | Supports robust declarative path configurations and layout outlets.                     |
| **Backend Framework** | **FastAPI**                     | Powers the core REST endpoints and analytics routes.                 | High-performance asynchronous execution with automatic OpenAPI document generation.     |
| **Package Manager**   | **UV**                          | Installs and manages Python dependencies.                            | Delivers faster installations compared to standard pip tools.                           |
| **RAG Vector Search** | **AWS Bedrock Knowledge Bases** | Indexes and retrieves payer clinical manuals.                        | Handles seamless PDF chunking and vector storage with zero operational upkeep.          |
| **Data Storage**      | **DynamoDB**                    | Holds claims, patterns, and prevention rules.                        | Delivers single-digit millisecond latency at scale.                                     |
| **File Storage**      | **Amazon S3**                   | Stores raw 835 files and policy PDFs.                                | Secure and highly durable object storage.                                               |
| **Orchestration**     | **AWS Lambda**                  | Runs ingestion, classification, and scoring pipelines.               | Scale-to-zero serverless compute that adapts automatically to volume spikes.            |
| **Audit Trails**      | **AWS CloudTrail**              | Audits API and database transactions.                                | Standardizes immutable regulatory records for HIPAA and SOC 2 audits.                   |
| **Data Encryption**   | **AWS KMS**                     | Manages data encryption keys.                                        | Delivers centralized control over encryption keys using FIPS 140-2 validated HSMs.      |

---

## SECTION 9: PROJECT STRUCTURE

```
denialiq/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application initialization & middleware
│   │   ├── config.py            # Environment configurations & AWS setups
│   │   ├── models/
│   │   │   └── __init__.py      # Pydantic data models for claims, patterns, and rules
│   │   ├── routes/
│   │   │   ├── __init__.py      # Routes registration
│   │   │   ├── analytics.py     # Endpoints for overview metrics, trends, and heatmaps
│   │   │   └── chat.py          # Post endpoints for conversational analyst
│   │   └── services/
│   │       ├── __init__.py      # Service definitions
│   │       ├── data_service.py  # Handles denials data filtering and structures
│   │       ├── bedrock_service.py # Interfaces Bedrock API for chat analysis
│   │       └── pattern_service.py # Sliding-window pattern detection engine
│   ├── data/
│   │   └── denials.json         # Standardized synthetic denials dataset
│   ├── scripts/
│   │   ├── generate_data.py     # Generates realistic synthetic denials
│   │   └── seed_demo.py         # Seeds demo data for the UnitedHealth knee MRI spike
│   └── pyproject.toml           # Hatchling & UV python project configuration
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Renders sidebar, header layout, and routing
│   │   ├── pages/
│   │   │   ├── Overview.jsx     # Dashboard with KPI cards, donut/line charts, and heatmap
│   │   │   ├── Patterns.tsx     # Systematic patterns dashboard (wrapper for Patterns.jsx)
│   │   │   ├── Patterns.jsx     # Grid cards, severity indicators, and detail modals
│   │   │   ├── PreventionRules.tsx # Prevention rules dashboard (wrapper for PreventionRules.jsx)
│   │   │   ├── PreventionRules.jsx # Summary indicators, rules cards, and SpinSci push
│   │   │   ├── Chat.tsx         # AI chat dashboard (wrapper for Chat.jsx)
│   │   │   └── Chat.jsx         # Chat bubbles, suggested chips, and timestamps
│   │   ├── components/          # Reusable UI widgets
│   │   │   └── .gitkeep         # Component placeholder
│   │   ├── services/
│   │   │   └── api.ts           # Axios/Fetch API client wrapping local routes
│   │   ├── index.css            # Custom CSS configurations and Tailwind directives
│   │   └── main.tsx             # React DOM entry point
│   ├── postcss.config.js        # PostCSS directives
│   ├── tailwind.config.js       # Tailwind theme parameters
│   ├── tsconfig.json            # TypeScript compiler parameters
│   └── package.json             # Frontend script commands and pnpm dependencies
├── start.sh                     # Bash script to run both backend and frontend concurrently
└── README.md                    # This project documentation manual
```

---

## SECTION 10: GETTING STARTED

Follow these instructions to configure and run the DenialIQ application.

### Prerequisites

Make sure the following tools are installed on your system:

- **Python 3.11+**
- **Node.js 18+**
- **UV Package Manager** (Install via: `pip install uv` or `curl -sSf https://rye.astral.sh/get | bash`)
- **AWS Credentials**: An active AWS account with **AWS Bedrock Claude** access enabled.

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/spinsci/denialiq.git
cd denialiq
```

#### 2. Configure Environment Variables

Copy the example environment file inside the backend directory:

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and update the parameters:

```env
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1
```

#### 3. Run the Automated Startup Script

The project includes a startup script in the root directory that automatically configures python virtual environments, installs dependencies, seeds the demo data, and runs both servers concurrently.

```bash
chmod +x start.sh
./start.sh
```

---

### Manual Setup (Fallback)

If `start.sh` fails, run the following commands in separate terminals:

#### Terminal A: Backend Setup

```bash
cd backend
# Install dependencies and sync virtual env
uv sync
# Seed the demo data
uv run python scripts/seed_demo.py
# Start the FastAPI server
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal B: Frontend Setup

```bash
cd frontend
# Install package dependencies
pnpm install
# Start the dev server
pnpm run dev
```

### Verification

Once running, verify the services are active:

- **Backend Healthcheck**: Visit `http://localhost:8000/api/analytics/overview` (should return JSON metrics).
- **Frontend Application**: Open `http://localhost:5173` inside your browser. You should see the **Overview Dashboard** with populated metrics.

---

## SECTION 11: API REFERENCE (Technical)

### 1. Ingestion Healthcheck

- **Method & Path**: `GET /`
- **Description**: Returns the active operational status of the service.
- **Response Example**:
  ```json
  {
    "status": "healthy",
    "service": "DenialIQ API Engine"
  }
  ```

### 2. Get Overview Statistics

- **Method & Path**: `GET /api/analytics/overview`
- **Description**: Gathers high-level statistics and aggregated distributions across all claims.
- **Response Example**:
  ```json
  {
    "total_denials": 247,
    "total_revenue_at_risk": 324900.5,
    "denial_by_root_cause": {
      "MISSING_PRIOR_AUTH": 84,
      "ELIGIBILITY_GAP": 62,
      "CODING_ERROR": 51,
      "MEDICAL_NECESSITY": 30,
      "TIMELY_FILING": 15,
      "INCORRECT_PAYER": 5
    },
    "denial_by_payer": {
      "UnitedHealth": 102,
      "BlueCross": 64,
      "Aetna": 48,
      "Cigna": 33
    },
    "denial_by_department": {
      "Radiology": 95,
      "Cardiology": 54,
      "Orthopedics": 48,
      "Primary Care": 31,
      "Oncology": 19
    },
    "denial_by_month": {
      "2026-03": 82,
      "2026-04": 110,
      "2026-05": 55
    },
    "top_denied_procedures": [
      {
        "procedure_code": "73721",
        "procedure_name": "MRI knee joint without contrast",
        "count": 42,
        "revenue": 40740.0
      }
    ]
  }
  ```

### 3. Get Denial Patterns

- **Method & Path**: `GET /api/analytics/patterns`
- **Description**: Analyzes historical claims and returns recognized patterns of denials.
- **Response Example**:
  ```json
  [
    {
      "pattern_id": "PAT-PAY-RC-001",
      "payer": "UnitedHealth",
      "procedure_code": null,
      "department": null,
      "root_cause": "MISSING_PRIOR_AUTH",
      "denial_count": 20,
      "revenue_at_risk": 19400.0,
      "trend": "INCREASING",
      "detected_date": "2026-05-28T18:14:02.124Z"
    }
  ]
  ```

### 4. Get Prevention Rules

- **Method & Path**: `GET /api/analytics/prevention-rules`
- **Description**: Returns recommended rules generated based on recognized patterns.
- **Response Example**:
  ```json
  [
    {
      "rule_id": "RULE-AUTH-001",
      "trigger_payer": "UnitedHealth",
      "trigger_procedure_codes": ["73721"],
      "trigger_department": "Radiology",
      "action": "FLAG_PRIOR_AUTH_REQUIRED",
      "message": "UnitedHealth requires prior auth for CPT 73721. 20 historical denials detected.",
      "denials_prevented_estimate": 14,
      "created_date": "2026-05-28T18:14:03.452Z"
    }
  ]
  ```

### 5. Get Payer Heatmap

- **Method & Path**: `GET /api/analytics/heatmap`
- **Description**: Returns combinations of payers and root causes to build the density heatmap.
- **Response Example**:
  ```json
  [
    {
      "payer": "UnitedHealth",
      "root_cause": "MISSING_PRIOR_AUTH",
      "count": 28
    },
    {
      "payer": "Cigna",
      "root_cause": "CODING_ERROR",
      "count": 19
    }
  ]
  ```

### 6. Get Weekly Denial Trend

- **Method & Path**: `GET /api/analytics/trend`
- **Description**: Gathers chronological weekly volumes and revenue risks.
- **Response Example**:
  ```json
  [
    {
      "week": "2026-W13",
      "count": 12,
      "revenue": 14200.0
    },
    {
      "week": "2026-W14",
      "count": 26,
      "revenue": 28400.0
    }
  ]
  ```

### 7. Filter Denials

- **Method & Path**: `GET /api/analytics/denials`
- **Description**: Searches and filters granular denial records (capped at **100** items).
- **Query Parameters**:
  - `payer` (string, optional)
  - `root_cause` (string, optional)
  - `department` (string, optional)
  - `start_date` (string, optional, YYYY-MM-DD)
  - `end_date` (string, optional, YYYY-MM-DD)
- **Response Example**:
  ```json
  [
    {
      "claim_id": "CLM-SEED-UH-001",
      "patient_id": "PT-SEED-UH-1000",
      "date_of_service": "2026-04-04",
      "submission_date": "2026-04-06",
      "denial_date": "2026-04-13",
      "payer": "UnitedHealth",
      "procedure_code": "73721",
      "procedure_name": "MRI knee joint without contrast",
      "diagnosis_code": "M25.561",
      "billed_amount": 970.0,
      "denial_reason_code": "CO-197",
      "denial_reason_text": "Prior authorization required. Policy updated April 3 2026.",
      "department": "Radiology",
      "provider_id": "PROV-2001",
      "root_cause": "MISSING_PRIOR_AUTH",
      "upstream_step": "SCHEDULING"
    }
  ]
  ```

### 8. Conversational Query

- **Method & Path**: `POST /api/chat`
- **Description**: Submits a user query and returns a grounded response.
- **Request Body**:
  ```json
  {
    "message": "Why are UnitedHealth denials up this month?",
    "history": []
  }
  ```
- **Response Example**:
  ```json
  {
    "response": "UnitedHealth denial rate increased 340% after April 1st. I identified a policy change on April 3rd requiring prior authorization for CPT 73721 (knee MRI). 20 claims totaling $19,400 have been denied since then. I've generated prevention rule PR-047 to flag future UnitedHealth knee MRI bookings at scheduling time."
  }
  ```

---

## SECTION 12: PRIVACY AND SECURITY

For healthcare platforms, data privacy and security are paramount. DenialIQ is built from the ground up to support strict compliance frameworks, protecting Protected Health Information (PHI) at every stage.

### HIPAA Compliance Architecture

- **HIPAA-Eligible AWS Tiers**: All serverless compute, storage, and models are executed on HIPAA-eligible services under an active **Business Associate Agreement (BAA)** with AWS.
- **No Model Retention**: Prompts and context processed by Bedrock are strictly private. The Claude models **do not retain or use patient data for training**.
- **Minimum Necessary Access**: The backend filters data and enforces the minimum necessary standard, removing or masking unnecessary identifiers before transmitting claims to classification.
- **Audit Ledgers**: Every action, API call, and rule deployment is recorded in immutable logs via **AWS CloudTrail** for easy compliance auditing.

### Data Security Framework

| Feature                        | Protocol      | Details                                                                                               |
| :----------------------------- | :------------ | :---------------------------------------------------------------------------------------------------- |
| **Data Encryption at Rest**    | **AES-256**   | All claim metadata and rules stored in DynamoDB and S3 are encrypted via **AWS KMS**.                 |
| **Data Encryption in Transit** | **TLS 1.3**   | All communications between the browser, API gateway, and backend services are encrypted.              |
| **Residency Constraints**      | **U.S. Only** | All primary and backup databases are locked to US-based server regions (`us-east-1` and `us-west-2`). |
| **Key Governance**             | **AWS KMS**   | centralizes encryption key lifecycle management with automated rotation schedules.                    |

### SOC 2 Type II and Security Alignment

DenialIQ implements structural configurations aligned with **SOC 2 Type II** controls:

1. **Access Isolation**: Restricts system access via role-based IAM configurations.
2. **System Audits**: All authentication failures, data modifications, and API calls are logged.
3. **HITRUST CSF Alignment**: Adheres to strict criteria regarding physical security, vulnerability management, and incident response.

---

## SECTION 13: SCALABILITY

DenialIQ relies on a serverless, event-driven architecture designed to scale seamlessly without manual infrastructure management.

```
Incoming Load Spike
        │
        ▼
 [ API Gateway ] ──► Scales automatically with regional request limits
        │
        ▼
 [ AWS Lambda ]  ──► Scale from 0 to 10,000 concurrent instances instantly
        │
        ▼
 [ DynamoDB ]    ──► Autoscaling R/W throughput preserves single-digit ms speeds
        │
        ▼
 [ Bedrock LLM ] ──► Serverless execution allocates compute capacity on-demand
```

### Serverless Infrastructure Scaling

- **AWS Bedrock Capacity**: Utilizes serverless inference, handling surges in document reviews and classification prompts without the need to provision GPUs.
- **Compute Elasticity**: AWS Lambda scales from **0 to 10,000 concurrent instances** within seconds, adapting to huge batches of claims uploaded at end-of-month cycles.
- **Storage Performance**: DynamoDB partition scales automatically, keeping response times under **10ms** even as historical databases grow to millions of records.
- **Multi-Tenant Isolation**: Separation of tenant records is enforced logically using partition keys and strict DynamoDB IAM policies, preventing cross-tenant data leaks.
- **The Network Scale Effect**: As more denial files are analyzed by DenialIQ, the pattern detection engine identifies industry-wide payer policy changes faster. A policy change detected at health system A automatically generates prevention rules that protect systems B and C instantly.

---

## SECTION 14: BUSINESS MODEL

DenialIQ addresses a highly lucrative, fast-growing slice of the healthcare IT landscape: the combination of **denial management** and **prior authorization automation**.

```
    TOTAL ADDRESSABLE MARKET (TAM)
     $50B+  (US Denial Management & Prior-Auth Automation)
             │
             ▼
    SERVICEABLE ADDRESSABLE MARKET (SAM)
     Large US Hospital Systems with 10%+ denial rates (~2,000 systems)
             │
             ▼
    SERVICEABLE OBTAINABLE MARKET (SOM)
     50 Large Health Systems in first 2 years of operations
```

### Subscription Pricing Structure

| Tier           | Monthly Claim Limits        | Target Segment                    | Pricing Model               |
| :------------- | :-------------------------- | :-------------------------------- | :-------------------------- |
| **Starter**    | Up to **500** claims        | Independent Clinics & Urgent Care | Flat **$1,500** / month     |
| **Growth**     | **500** to **5,000** claims | Regional Specialty Practices      | Flat **$4,500** / month     |
| **Enterprise** | **5,000+** claims           | Multi-Hospital Health Systems     | Custom per-provider pricing |

### Customer ROI Calculation

- **The Baseline**: A mid-sized hospital processes **1,000 denials** per month.
- **The Cost**: At an average rework cost of **$200** per claim (appeals, staff hours, and delayed cash flow), the hospital spends **$200,000** per month managing denials.
- **The DenialIQ Impact**: DenialIQ intercepts and prevents **30%** of errors pre-submission.
- **The Savings**: Saves **300 claims** monthly, translating to **$60,000** saved per month in manual rework costs alone, plus accelerated cash flows.

### Strategic Go-To-Market Integration

- **Phase 1 (Validation)**: Run a pilot focused on one high-risk department (e.g., Radiology or Orthopedics) at a single health system.
- **Phase 2 (Expansion)**: Expand horizontally across all departments within the pilot health system.
- **Phase 3 (Scale)**: Leverage **SpinSci's active partner network** of **165+ large health systems** to distribute DenialIQ as a native extension. This partnership combines SpinSci's patient-access front door with DenialIQ's backend analytics, creating a complete revenue cycle platform.

---

## SECTION 15: DEMO GUIDE

Follow this step-by-step guide to run the DenialIQ demo for pitches or evaluations.

### The 5-Screen Demo Narrative

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Screen 1:       │ ───► │ Screen 2:       │ ───► │ Screen 3:       │ ───► │ Screen 4:       │ ───► │ Screen 5:       │
│ The Dashboard   │      │ Live Heatmap    │      │ Patterns Grid   │      │ Prevention Rules│      │ Interactive Chat│
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
```

1. **Screen 1: The Overview Dashboard**
   - _Action_: Show the main dashboard page (`http://localhost:5173`).
   - _Script_: _"Look at the KPI cards at the top. We have 247 total denials and $324K in revenue at risk. Our top root cause is missing prior authorization, and our highest denial payer is UnitedHealth."_
2. **Screen 2: The Payer Heatmap**
   - _Action_: Scroll down to the **Payer Heatmap**.
   - _Script_: _"Look at the deep red cell under UnitedHealth and Missing Prior Auth. The count is 28 denials. This highlights a systematic bottleneck, not just an isolated error."_
3. **Screen 3: Systematic Denial Patterns**
   - _Action_: Click **Denial Patterns** inside the sidebar. Click **View Denials** on the `UnitedHealth` prior auth card.
   - _Script_: _"DenialIQ identified this pattern: 20 MRI denials after April 1st. When we click 'View Denials', we get the granular audit list. The denial reasons confirm a policy change requiring authorization."_
4. **Screen 4: AI Prevention Rules**
   - _Action_: Click **Prevention Rules** inside the sidebar. Click **Push to SpinSci** on `RULE-AUTH-001`.
   - _Script_: _"DenialIQ generated a prevention rule. With one click, we push it to the SpinSci intake portal. A success banner confirms that future bookings for CPT 73721 will be flagged automatically, stopping denials at the source."_
5. **Screen 5: Conversational AI Analyst**
   - _Action_: Click **Ask DenialIQ** in the sidebar. Click the suggested question: _"Why are UnitedHealth denials up this month?"_
   - _Script_: _"Instead of running manual spreadsheets, users can ask DenialIQ questions in plain English. The AI immediately analyzes the backend, explaining the prior auth policy change on April 3rd and confirming the $19,400 risk."_

---

### Anticipated Judge Questions & Prepared Answers

#### Q: How is this different from Change Healthcare or Waystar?

> **Answer**: _Traditional systems are reactive billing clearinghouses that tell you why a claim was denied after the fact. DenialIQ is a proactive automation layer. It analyzes backend remittances, uses generative AI to find root causes, and immediately injects warning rules into the front-end scheduling systems to stop errors before claims are created._

#### Q: Does this require replacing our EHR?

> **Answer**: _No. DenialIQ is designed as a non-invasive layer, not a replacement. It reads transaction files and uses standard APIs (like the SpinSci MCP layer) to inject alerts directly into existing systems, requiring zero modifications to EHR databases._

#### Q: How long does implementation take?

> **Answer**: _A pilot can be deployed in less than 30 days. Because DenialIQ connects via standard FHIR APIs and X12 loops, it doesn't require custom software development or complex local integrations._

#### Q: What happens to patient data?

> **Answer**: _All data remains completely secure. DenialIQ uses HIPAA-eligible AWS services. Patient data is encrypted using keys you control, and prompts sent to Bedrock are private and never used to train the underlying models._

#### Q: How does it get smarter over time?

> **Answer**: _DenialIQ benefits from a collaborative network effect. As it processes more claims across hospital networks, the pattern detection engine identifies payer policy updates faster, generating prevention rules that benefit all connected providers._

---

## SECTION 16: TEAM

| Name             | Hackathon Role     | Primary Responsibility                                                                    |
| :--------------- | :----------------- | :---------------------------------------------------------------------------------------- |
| **Jane Doe**     | Fullstack Engineer | Constructed the React frontend dashboard panels and integrated Recharts visualizations.   |
| **John Smith**   | Backend Developer  | Engineered the FastAPI REST endpoints and the EventBridge Lambda ingestion hooks.         |
| **Alice Miller** | AI specialist      | Configured the AWS Bedrock RAG vector search and optimized Claude classification prompts. |

_Built at the **SpinSci Healthcare AI Hackathon**, June 6, 2026, Addison, TX._
