# IBOA — Implementation Task Breakdown
**Team:** LeCoders | **Project:** Intelligent Boarding Orchestration Agent

---

## How to read this document

Each stage has a **blocker status** telling you what must be done before it can start.
Tasks marked `[ ]` are unchecked — check them off as your team completes them.
Owner suggestions are recommendations based on the parallel work analysis.

---

## Stage 1 — Database & Seed Data
**Blocker:** None — start immediately
**Owner:** Person 1
**Files:** `setup/seed_database.py`, `config.py` (DB connection string only)
**Done when:** Running `python setup/seed_database.py` creates all 7 tables and you can query real rows in a DB viewer

### Part 1A — Environment setup
- [ ] Install PostgreSQL locally
- [ ] Create database named `iboa_db`
- [ ] Add DB connection string to `config.py`
- [ ] Install Python dependencies: `psycopg2`, `python-dotenv`

### Part 1B — Create tables
- [ ] Create `flights` table
- [ ] Create `passengers` table
- [ ] Create `baggage` table
- [ ] Create `ground_crew` table
- [ ] Create `crew_manifest` table
- [ ] Create `connecting_flights` table
- [ ] Create `agent_log` table

### Part 1C — Seed demo flight DL447
- [ ] Insert flight DL447 (gate B12, departs 2:30 PM, Boeing 737, 160 seats)
- [ ] Insert ~20 passengers across 3 boarding groups with varied seat assignments
- [ ] Insert baggage rows for passengers with checked bags

### Part 1D — Seed the four scenarios
- [ ] **Scenario 1 — Bag pull risk:** Set Marcus Webb (seat 24B) with `gate_scanned = FALSE`, bags loaded
- [ ] **Scenario 2 — Connecting passengers:** Insert Priya Patel + 2 others with `connection_flight = DL203`; insert DL203 → DL447 in `connecting_flights` with `actual_arrival` 25 min late
- [ ] **Scenario 3 — Ground crew not ready:** Insert ground crew row with `catering_complete = FALSE`, all others TRUE
- [ ] **Scenario 4 — Missing crew:** Insert all 5 crew members with `checked_in = FALSE`

### Part 1E — Verify
- [ ] Open DB viewer (pgAdmin or TablePlus) and confirm all 7 tables exist with correct rows
- [ ] Manually run a test query: confirm Marcus Webb appears in a bag pull risk query
- [ ] Confirm Priya Patel's connection flight shows as late

---

## Stage 2 — MCP Server & Tool Definitions
**Blocker:** Stage 1 must be complete (needs a live database to query)
**Owner:** Person 2
**Files:** `mcp_server.py`
**Done when:** Each of the 8 tool functions can be called directly in Python and returns correct data

### Part 2A — Server setup
- [ ] Install `fastmcp` library
- [ ] Set up FastMCP server instance in `mcp_server.py`
- [ ] Connect MCP server to PostgreSQL using connection string from `config.py`

### Part 2B — Implement the 8 MCP tools
- [ ] `get_passenger_manifest()` — query all passengers for DL447, return name/seat/boarding group/gate scanned status
- [ ] `get_gate_scan_count()` — count passengers where `gate_scanned = TRUE`
- [ ] `get_tsa_clearance_count()` — count passengers where `tsa_cleared = TRUE`
- [ ] `get_unscanned_bag_passengers()` — join `passengers` + `baggage`, return passengers where bags loaded but `gate_scanned = FALSE`
- [ ] `get_ground_crew_status()` — return all four boolean flags for DL447 from `ground_crew`
- [ ] `get_crew_manifest()` — return all crew members and their `checked_in` status
- [ ] `get_connecting_passenger_eta()` — return inbound flight ETA, delay in minutes, and passenger count from `connecting_flights`
- [ ] `get_time_to_departure()` — calculate minutes remaining until `departure_time` using `NOW()`

### Part 2C — Verify each tool
- [ ] Call `get_unscanned_bag_passengers()` — confirm Marcus Webb is returned
- [ ] Call `get_connecting_passenger_eta()` — confirm DL203 shows as 25 min late
- [ ] Call `get_ground_crew_status()` — confirm `catering_complete = False`
- [ ] Call `get_crew_manifest()` — confirm all crew show `checked_in = False`
- [ ] Call `get_time_to_departure()` — confirm it returns a realistic number of minutes

---

## Stage 3 — watsonx LLM Client
**Blocker:** None — can run in parallel with Stage 2
**Owner:** Person 3
**Files:** `config.py`, `llm_client.py`
**Done when:** Calling `ask_llm()` with a test prompt returns a response from IBM Granite

### Part 3A — IBM watsonx setup
- [ ] Locate IBM Cloud API key from SkillsBuild hackathon account
- [ ] Locate watsonx project ID and endpoint URL from watsonx.ai Studio
- [ ] Add `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL` to `config.py`
- [ ] Set default `MODEL_ID = "ibm/granite-3-3-8b-instruct"` in `config.py`

### Part 3B — Build llm_client.py
- [ ] Install `ibm-watsonx-ai` SDK
- [ ] Write `ask_llm(prompt, tools=None)` function that:
  - Authenticates using API key
  - Sends prompt + tool definitions to the model
  - Returns the raw response (either a tool call request or a text response)
- [ ] Ensure nothing outside `llm_client.py` imports from the watsonx SDK directly

### Part 3C — Verify
- [ ] Call `ask_llm("What is the capital of France?")` — confirm a text response comes back
- [ ] Call `ask_llm()` with a simple tool definition — confirm the model returns a tool call request
- [ ] Confirm swapping `MODEL_ID` in `config.py` routes to a different model without changing any other file

---

## Stage 4 — Agent Loop
**Blocker:** Stages 2 and 3 must both be complete
**Owner:** Person 1 + Person 2 + Person 3 (collaborate)
**Files:** `agent.py`
**Done when:** The agent loop runs every 60 seconds, calls tools, and prints a plain-language recommendation to the terminal

### Part 4A — System prompt
- [ ] Write the system prompt that tells the LLM its role: gate agent situational awareness for flight DL447
- [ ] Define the output format: one plain-language recommendation, no bullet points, no dashboard
- [ ] Include context about what each tool returns so the LLM knows how to use them
- [ ] Test the system prompt manually in watsonx Studio before hardcoding it

### Part 4B — Tool call handling loop
- [ ] Build the monitoring loop that fires every 60 seconds
- [ ] On each loop iteration:
  - [ ] Send system prompt + all 8 tool definitions to `ask_llm()`
  - [ ] If LLM requests a tool call: call the corresponding MCP tool, return result to LLM
  - [ ] If LLM requests multiple tools: handle each call and feed all results back
  - [ ] Once LLM returns a final text response: treat it as the recommendation
- [ ] Handle the case where the LLM loops back for more tool calls (multi-step reasoning)

### Part 4C — Logging
- [ ] After each recommendation, write a new row to `agent_log` with `flight_id`, `timestamp`, and `recommendation`
- [ ] Print each recommendation to the terminal with a timestamp

### Part 4D — Verify
- [ ] Run the agent with the seeded database (no simulator yet)
- [ ] Confirm a recommendation appears in the terminal every 60 seconds
- [ ] Confirm the recommendation mentions the bag pull risk (Marcus Webb) and/or catering not complete
- [ ] Confirm a new row appears in `agent_log` after each cycle

---

## Stage 5 — Flight Simulator
**Blocker:** Stage 4 must be complete (need the agent running to see simulator effects)
**Owner:** Person 1 (or anyone who has bandwidth)
**Files:** `simulator/flight_sim.py`
**Done when:** Running the simulator in one terminal causes the agent recommendations in the other terminal to change over time

### Part 5A — Passenger boarding simulation
- [ ] Every 8–12 seconds, flip a random unscanned passenger's `gate_scanned` to TRUE (excluding Marcus Webb)
- [ ] Stop when all non-Webb passengers have scanned

### Part 5B — Crew check-in simulation
- [ ] Stagger crew check-ins — one crew member flips `checked_in = TRUE` every 90 seconds
- [ ] Ensure the captain (Sarah Okafor) checks in last, around T-15 minutes

### Part 5C — Ground crew resolution
- [ ] At T-20 minutes: flip `catering_complete = TRUE`

### Part 5D — Connecting flight ETA update
- [ ] Every 30 seconds, update `connecting_flights.actual_arrival` to tick 1 minute closer
- [ ] Stop updating once the inbound flight has "arrived" (actual_arrival passes NOW())
- [ ] After arrival: flip Priya Patel and the 2 other connecting passengers' `gate_scanned` to TRUE

### Part 5E — Add demo speed multiplier
- [ ] Add a `DEMO_SPEED` variable in `flight_sim.py` (default = 1.0)
- [ ] Setting `DEMO_SPEED = 3` makes the simulation run 3x faster for testing

### Part 5F — Verify
- [ ] Run simulator + agent loop together
- [ ] Confirm agent recommendation changes as crew check in
- [ ] Confirm agent escalates bag pull risk urgency as departure time approaches
- [ ] Confirm agent shifts to "clear for pushback" once catering completes and all (non-Webb) passengers are scanned

---

## Stage 6 — Frontend (Gate Agent Display)
**Blocker:** Stage 4 must be complete (needs a working agent to connect to)
**Owner:** All three — work concurrently with Stage 5
**Files:** `frontend/`
**Done when:** Opening the browser shows live-updating recommendations as the simulator runs

### Part 6A — Project setup
- [ ] Initialize React + TypeScript project with Tailwind CSS in `frontend/`
- [ ] Install WebSocket client library

### Part 6B — WebSocket connection
- [ ] Connect frontend to agent loop WebSocket endpoint
- [ ] Handle incoming recommendation messages
- [ ] Handle reconnection if the WebSocket drops

### Part 6C — Main display UI
- [ ] Display flight info header: flight number, gate, departure time, time remaining
- [ ] Display current recommendation in large, readable text (this is the primary element Diana sees)
- [ ] Display timestamp of last recommendation update
- [ ] Add a subtle status indicator showing the agent is active and monitoring

### Part 6D — Status panel
- [ ] Show a compact status row: passengers scanned / total, crew checked in / total, ground crew flags
- [ ] Color-code flags: green = all clear, amber = attention needed, red = action required
- [ ] Keep this panel secondary — recommendation text is the focus

### Part 6E — Agent loop WebSocket endpoint
- [ ] Add WebSocket server to `agent.py` that broadcasts each new recommendation to connected clients
- [ ] Test that the frontend receives and displays updates in real time

### Part 6F — Verify
- [ ] Open browser, confirm flight info displays correctly
- [ ] Run simulator — confirm recommendation updates in browser without page refresh
- [ ] Confirm the display is readable at a glance (gate agent should not have to squint or scroll)

---

## Stage 7 — Integration & Demo Polish
**Blocker:** All stages complete
**Owner:** Everyone
**Done when:** Full end-to-end demo runs cleanly from seed to pushback recommendation

### Part 7A — End-to-end run
- [ ] Seed the database: `python setup/seed_database.py`
- [ ] Start MCP server: `python mcp_server.py`
- [ ] Start agent loop: `python agent.py`
- [ ] Start simulator: `python simulator/flight_sim.py`
- [ ] Open frontend in browser
- [ ] Walk through the full demo timeline and note any broken behavior

### Part 7B — System prompt tuning
- [ ] Review 5–10 recommendation outputs — are they clear, specific, and actionable?
- [ ] Adjust system prompt wording if recommendations are too vague or too verbose
- [ ] Confirm the agent handles all four scenarios with an appropriate recommendation
- [ ] Confirm the agent says something sensible when everything is fine (not just silent)

### Part 7C — Edge case handling
- [ ] What happens if the database is empty? (add a graceful error message)
- [ ] What happens if watsonx API is slow or times out? (add a retry with a fallback message)
- [ ] What happens if the WebSocket drops? (frontend should show a "reconnecting" state)

### Part 7D — Demo script
- [ ] Write a short demo script: what to say at each stage of the simulation
- [ ] Identify the 3 best moments to highlight during the demo (e.g., bag pull escalation, captain check-in, pushback clearance)
- [ ] Do a full dry run and time it — aim for a demo that completes in under 5 minutes

### Part 7E — Final cleanup
- [ ] Remove debug print statements
- [ ] Add a `README.md` with setup and run instructions
- [ ] Confirm `config.py` has no hardcoded secrets (use `.env` file)
- [ ] Add `.env.example` file showing required environment variables

---

## Parallel work summary

| Stage | Can start when | Suggested owner |
|---|---|---|
| Stage 1 — Database | Immediately | Person 1 |
| Stage 2 — MCP server | Stage 1 done | Person 2 |
| Stage 3 — LLM client | Immediately (parallel with Stage 2) | Person 3 |
| Stage 4 — Agent loop | Stages 2 + 3 done | Everyone |
| Stage 5 — Simulator | Stage 4 done | Person 1 |
| Stage 6 — Frontend | Stage 4 done | Everyone (parallel with Stage 5) |
| Stage 7 — Integration | Stages 5 + 6 done | Everyone |