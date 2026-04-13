# IBOA Agent Loop - Class Reference

**File:** `agent.py`  
**Purpose:** Autonomous monitoring loop that orchestrates LLM reasoning and tool execution

---

## Class: `IBOAAgent`

Runs every 60 seconds, calls LLM with tool definitions, executes requested tools, and sends recommendations to frontend.

### Instance Variables
```python
self.flight_id: str              # Flight being monitored (e.g., "DL447")
self.monitoring_interval: int    # Seconds between cycles (default: 60)
self.is_running: bool            # Agent running state
self.cycle_count: int            # Number of completed cycles
self.last_recommendation: str    # Most recent recommendation
self.connected_clients: set      # WebSocket connections to frontend
```

---

## Public Methods

### `async start()`
Starts the infinite monitoring loop. Calls `_monitor_cycle()` every 60 seconds. Continues even if individual cycles fail.

### `stop()`
Stops the monitoring loop gracefully after current cycle completes.

---

## Private Methods

### `async _monitor_cycle()`
Executes one complete monitoring cycle. Orchestrates the full flow from getting context to sending recommendations.

### `_get_flight_context() -> dict`
Queries flight metadata (departure time, gate, etc.) from database via MCP tool.

### `_build_initial_prompt(flight_context: dict) -> list`
Constructs system prompt and user prompt with flight context. Tells LLM its role and available tools.

### `async _run_llm_loop(initial_messages: list) -> str`
Core LLM interaction loop. Sends messages to LLM, parses response, executes tools if requested, feeds results back. Repeats until LLM produces final recommendation. Max 10 iterations to prevent infinite loops.

### `async _call_llm(messages: list) -> dict`
Sends messages to IBM Granite LLM via `llm_client.ask_llm()`. Returns raw LLM response.

### `_parse_llm_response(response: dict) -> dict`
Determines if LLM response contains tool calls or final recommendation. Returns `{"type": "tool_calls", ...}` or `{"type": "recommendation", ...}`.

### `async _execute_tools(tool_calls: list) -> list`
Executes multiple tools in parallel using `asyncio.gather()`. Returns list of all tool results.

### `async _execute_single_tool(tool_call: dict) -> dict`
Executes one tool with 3-retry logic. Returns tool result or error message if all retries fail.

### `async _handle_recommendation(recommendation: str)`
Logs recommendation to database, sends to frontend via WebSocket, updates agent memory.

### `async _log_recommendation(recommendation: str)`
Inserts recommendation into `agent_log` table for tracking and audit trail.

### `async _send_to_frontend(recommendation: str)`
Broadcasts recommendation to all connected WebSocket clients.

### `async _run_websocket_server()`
Starts WebSocket server on port 8765. Accepts frontend connections and maintains `connected_clients` set.