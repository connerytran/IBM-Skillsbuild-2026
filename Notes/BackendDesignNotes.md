# IBOA — Backend Design
**Team:** LeCoders | **Last updated:** April 2026

---

## Overview

The backend is split into four files with strict separation of responsibility.
No file does more than one job. No file knows more than it needs to.

```
iboa-agent/
├── config.py              ← all settings and credentials
├── llm_client.py          ← only file that touches the watsonx SDK
├── agent.py               ← monitoring loop and reasoning orchestration
├── mcp_server.py          ← tools and database queries
├── setup/
│   └── seed_database.py   ← run once to create and populate the DB
└── simulator/
    └── flight_sim.py      ← updates DB in real time during the demo
```

---

## File Responsibilities

### `config.py`
**Job:** Hold all settings in one place. Nothing else hardcodes credentials or model names.

| Setting | Purpose |
|---|---|
| `MODEL_ID` | Which LLM to use — change this to swap models |
| `WATSONX_API_KEY` | Loaded from `.env` — never hardcoded |
| `WATSONX_PROJECT_ID` | Loaded from `.env` — never hardcoded |
| `WATSONX_URL` | Regional endpoint for IBM Cloud |
| `FLIGHT_ID` | The demo flight (`DL447`) |
| `MONITOR_INTERVAL_SECONDS` | How often the agent loop fires (60s) |

**Rule:** `config.py` is the only file that changes when swapping models or environments.

---

### `llm_client.py`
**Job:** Be the single point of contact with the watsonx SDK. Expose one function to the rest of the project.

**Functions:**

`ask_llm(messages, tools)` — sends a conversation to the LLM and returns one of two things:
- `{"type": "tool_call", "tool": "...", "args": {...}}` — model wants to call a tool
- `{"type": "text", "content": "..."}` — model produced a final recommendation

**Rules:**
- The only file that imports from `ibm_watsonx_ai`
- If you ever switch from watsonx to another provider, only this file changes
- `agent.py` never knows which model is running — it just calls `ask_llm()`

**Why `ask_llm()` takes `tools` as a parameter:**
Tools are defined and owned by `mcp_server.py`. The agent loop fetches them at runtime and passes them in. This means `llm_client.py` has zero knowledge of what tools exist — it just forwards them to the model.

---

### `agent.py`
**Job:** Run the monitoring loop. Orchestrate the reasoning cycle every 60 seconds.

**What it does each cycle:**
1. Fetches the current tool list from `mcp_server.get_available_tools()`
2. Builds the messages list (system prompt + any accumulated tool results)
3. Calls `ask_llm(messages, tools)`
4. If the response is a tool call — executes it via the MCP server, appends the result, calls `ask_llm()` again
5. If the response is text — logs it to `agent_log` and broadcasts it over WebSocket
6. Sleeps until the next 60-second interval

**Rules:**
- Never imports from `ibm_watsonx_ai` directly — only calls `ask_llm()`
- Never defines tools — always fetches them from the MCP server
- Never queries the database directly — always goes through MCP tools

**Why the agent fetches tools from the MCP server instead of defining them itself:**
Separation of responsibility. The MCP server owns the tools. If a new tool is added to the MCP server, the agent loop gets it automatically with no changes required.

---

### `mcp_server.py`
**Job:** Own the tools. Define them, execute them, and expose them.

**Two responsibilities:**

1. `get_available_tools()` — returns the full list of tool schemas so the agent loop can pass them to the LLM

2. Tool execution functions — each one runs a focused SQL query against PostgreSQL and returns clean data

| Tool | What it returns |
|---|---|
| `get_passenger_manifest()` | All ticketed passengers and their status |
| `get_gate_scan_count()` | How many passengers have scanned at the gate |
| `get_tsa_clearance_count()` | How many passengers have cleared security |
| `get_unscanned_bag_passengers()` | Passengers with loaded bags not yet at gate (bag pull risk) |
| `get_ground_crew_status()` | Fueling, catering, cleaning, cargo status |
| `get_crew_manifest()` | Which crew members have checked in |
| `get_connecting_passenger_eta()` | Inbound connecting flight status and delay |
| `get_time_to_departure()` | Minutes remaining until pushback |

**Rules:**
- No knowledge of which LLM is being used
- No knowledge of what the agent loop does with tool results
- Only talks to PostgreSQL — never to watsonx

---

### `setup/seed_database.py`
**Job:** Create all database tables and populate them with the demo flight and scenarios.

**Run once** before the demo: `python setup/seed_database.py`

Creates the 7 tables and seeds flight DL447 with four pre-built scenarios:
- Bag pull risk — Marcus Webb (seat 24B) has bags loaded but will not scan
- Connecting passengers — Priya Patel connecting from late flight DL203
- Ground crew not ready — catering starts as incomplete
- Missing crew — all crew start as not checked in

---

### `simulator/flight_sim.py`
**Job:** Advance the flight state in real time during the demo.

**Run during the demo** in a separate terminal alongside `agent.py`.

- Gradually flips passengers to `gate_scanned = TRUE` (except Marcus Webb)
- Flips crew to `checked_in = TRUE` one by one
- Flips `catering_complete = TRUE` partway through
- Ticks the connecting flight ETA closer every 30 seconds
- Supports a `DEMO_SPEED` multiplier to run faster during testing

---

## How the files talk to each other

```
agent.py
  → asks mcp_server: "what tools do you have?"
  → asks llm_client: "given these messages and tools, what should I do?"
  → if tool call: asks mcp_server: "execute this tool"
  → if text: logs to DB, broadcasts to frontend

llm_client.py
  → talks to watsonx API only
  → returns structured result to agent.py

mcp_server.py
  → talks to PostgreSQL only
  → returns data to agent.py
```

No file skips a layer. `agent.py` never talks to PostgreSQL directly. `llm_client.py` never talks to PostgreSQL. `mcp_server.py` never talks to watsonx.

---

## Separation of responsibility summary

| File | Knows about LLM? | Knows about DB? | Changes if model swaps? | Changes if DB schema changes? |
|---|---|---|---|---|
| `config.py` | Yes — MODEL_ID | No | One line | No |
| `llm_client.py` | Yes — wraps SDK | No | Only if provider changes | No |
| `agent.py` | No | No | Never | Never |
| `mcp_server.py` | No | Yes | Never | Yes |
| `seed_database.py` | No | Yes | Never | Yes |

---

## Environment setup

Credentials live in a `.env` file — **never committed to GitHub.**

```
WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://us-south.ml.cloud.ibm.com
DB_CONNECTION_STRING=
```

Copy `.env.example`, rename it to `.env`, and fill in your values.

---

## Models available on your watsonx environment

| Model ID | Notes |
|---|---|
| `meta-llama/llama-3-3-70b-instruct` | Current default — best reasoning and tool calling |
| `meta-llama/llama-3-2-11b-vision-instruct` | Faster, lighter, weaker reasoning |
| `mistral-large-2512` | Strong reasoning — verify it is not on the excluded list |