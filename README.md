# Voice-Enabled Logistics Assistant

> **KIT Hackathon – 14 March 2026**
> Kalaignar Karunanidhi Institute of Technology

A hands-free shipment tracking and task management assistant for drivers and warehouse workers.  
Workers speak natural-language commands ("What's the status of shipment SHP001?", "Mark order picked", "What's my next stop?") and the assistant reads back answers or performs actions in the background — no manual device interaction required.

---

## Features

| Capability | Description |
|---|---|
| **Shipment tracking** | Track by ID, tracking number, customer name, or route — includes ETA and special instructions |
| **Voice commands** | Natural language intent recognition for logistics vocabulary (pick, deliver, exception, next stop, …) |
| **Task management** | Voice-driven pick/putaway lists, loading sequences, next-stop navigation |
| **Exception logging** | "Package damaged" / "Customer not available" — creates an exception task and updates shipment status |
| **Delay notifications** | Trigger consignee notifications hands-free |
| **JWT authentication** | Role-based access for drivers, warehouse workers, dispatchers, and admins |
| **Audit log** | Every voice-initiated action is recorded with user, timestamp, and details |
| **NLU model training** | HuggingFace training pipeline to fine-tune BERT on logistics intents |

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the API server

```bash
uvicorn app.main:app --reload --port 8000
```

Open the interactive docs at **http://localhost:8000/docs**

### 3. Authenticate

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "driver1", "password": "driver123"}'
```

Seed users:

| Username | Password | Role |
|---|---|---|
| `driver1` | `driver123` | Driver |
| `driver2` | `driver456` | Driver |
| `warehouse1` | `warehouse123` | Warehouse |
| `dispatcher1` | `dispatch123` | Dispatcher |
| `admin` | `admin123` | Admin |

### 4. Send a voice command

```bash
TOKEN="<paste token here>"

curl -X POST http://localhost:8000/voice/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "What is the status of shipment SHP001?", "user_id": "DRV001"}'
```

Example response:
```json
{
  "intent": "track_shipment",
  "entities": {"shipment_id": "SHP001"},
  "spoken_response": "Shipment TRK-2026-001 for Acme Corp is currently in transit at Salem Checkpoint. Estimated delivery: 07:00 AM.",
  "action_taken": null,
  "data": { ... }
}
```

---

## Supported Voice Commands

| Command | Intent |
|---|---|
| "What is the status of shipment SHP001?" | `track_shipment` |
| "Track order TRK-2026-002" | `track_shipment` |
| "What's my next stop?" | `next_stop` |
| "Where do I go next?" | `next_stop` |
| "List my tasks" | `list_tasks` |
| "What should I do next?" | `list_tasks` |
| "Mark shipment SHP003 as picked" | `mark_picked` |
| "Mark order SHP001 as delivered" | `mark_delivered` |
| "Package is damaged for shipment SHP002" | `log_exception` |
| "Customer not available" | `log_exception` |
| "Send delay notification to customer" | `send_notification` |
| "Notify consignee" | `send_notification` |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Get JWT token |
| `GET` | `/shipments/` | List shipments |
| `GET` | `/shipments/{id}` | Get shipment by ID or tracking number |
| `GET` | `/shipments/search` | Search by customer or tracking number |
| `GET` | `/shipments/next-stop` | Next pending stop for authenticated driver |
| `PATCH` | `/shipments/{id}/status` | Update shipment status |
| `GET` | `/tasks/` | List tasks for authenticated worker |
| `GET` | `/tasks/next` | Get highest-priority pending task |
| `PATCH` | `/tasks/{id}/status` | Update task status |
| `POST` | `/voice/command` | **Process voice command** |
| `GET` | `/voice/audit-log` | Retrieve audit log |

---

## Running Tests

```bash
pytest
```

All 60 tests should pass.

---

## NLU Model Training (HuggingFace)

The rule-based NLU engine works out of the box. For production, fine-tune a transformer model:

```bash
# Save the training dataset only
python training/train_nlu_model.py --save-data-only

# Fine-tune (requires GPU recommended)
python training/train_nlu_model.py \
  --model distilbert-base-uncased \
  --output output/logistics-nlu-model \
  --epochs 5
```

### Recommended HuggingFace Dataset

**`CLINC/clinc_oos`** — a large intent-classification benchmark (150 intents, 23,700 utterances).  
Used for bootstrapping; supplemented with the synthetic logistics utterances in `training/train_nlu_model.py`.

```python
from datasets import load_dataset
ds = load_dataset("CLINC/clinc_oos", "plus")
```

The trained model is saved to `output/logistics-nlu-model` and can be pushed to the Hub:

```python
from huggingface_hub import notebook_login
notebook_login()
trainer.push_to_hub("your-username/logistics-nlu-model")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           Mobile / Wearable / In-cab Unit           │
│  (speech-to-text → text command → TTS response)    │
└───────────────────────┬─────────────────────────────┘
                        │ HTTPS + JWT
┌───────────────────────▼─────────────────────────────┐
│           Voice-Enabled Logistics API               │
│  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │  NLU Engine  │  │  Shipment  │  │   Task     │  │
│  │ (intent +    │  │  Service   │  │  Service   │  │
│  │  entities)   │  └─────┬──────┘  └─────┬──────┘  │
│  └──────┬───────┘        │               │         │
│         └────────────────┴───────────────┘         │
│                          │                         │
│              ┌───────────▼──────────┐              │
│              │  Auth + Audit Log    │              │
│              └──────────────────────┘              │
└─────────────────────────────────────────────────────┘
                          │
              ┌───────────▼──────────┐
              │  TMS / WMS / Tracking│
              │  (pluggable via API) │
              └──────────────────────┘
```

---

## Project Structure

```
KIT/
├── app/
│   ├── main.py                  # FastAPI application
│   ├── models/
│   │   ├── schemas.py           # Pydantic data models
│   │   └── store.py             # In-memory data store with seed data
│   ├── routers/
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── shipments.py         # Shipment tracking endpoints
│   │   ├── tasks.py             # Task management endpoints
│   │   └── voice.py             # Voice command endpoint
│   ├── services/
│   │   ├── auth_service.py      # JWT auth logic
│   │   ├── shipment_service.py  # Shipment CRUD + queries
│   │   └── task_service.py      # Task CRUD + workflow
│   └── voice/
│       ├── nlu_engine.py        # Intent classification + entity extraction
│       └── processor.py         # Voice command orchestrator
├── training/
│   └── train_nlu_model.py       # HuggingFace fine-tuning pipeline
├── tests/
│   ├── test_api.py              # API integration tests
│   ├── test_nlu_engine.py       # NLU unit tests
│   ├── test_services.py         # Service unit tests
│   └── test_training_data.py    # Dataset builder tests
├── requirements.txt
└── pytest.ini
```
