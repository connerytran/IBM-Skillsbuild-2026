# Plug and Play LLM Design Guide

## Goal

Design the system so that swapping the underlying LLM requires changing
as little code as possible — ideally one line in a config file. The MCP
server should never need to change regardless of which model is used.

---

## Why This Works

MCP is a protocol. Your MCP server speaks MCP. Any LLM client that also
speaks MCP can connect to it. The server does not know or care which model
is calling it. This means the MCP server is naturally portable — the plug
and play design just makes sure the rest of your code follows the same
principle.

---

## File Structure

```
iboa-agent/
│
├── config.py          ← change MODEL_ID here to swap models
├── llm_client.py      ← wraps the SDK, exposes one standard function
├── agent.py           ← calls llm_client only, never touches SDK directly
├── mcp_server.py      ← completely unaware of which LLM is being used
└── database/          ← completely unaware of which LLM is being used
```

---

## The Four Files and Their Roles

### config.py
Holds all model settings and credentials in one place. This is the only
file that should ever change when swapping models. Nothing else in the
project hardcodes a model name or API key.

```python
MODEL_ID           = "ibm/granite-3-3-8b-instruct"
WATSONX_API_KEY    = "your-api-key-here"
WATSONX_URL        = "https://us-south.ml.cloud.ibm.com"
WATSONX_PROJECT_ID = "your-project-id-here"
FLIGHT_ID          = "DL447"
MONITOR_INTERVAL_SECONDS = 60
```

To swap models, change MODEL_ID to any supported model. That is the
only change required.

---

### llm_client.py
The only file that imports from the watsonx SDK. It reads from config
and exposes a single standard function — something like `ask_llm()` —
that the rest of the project calls. The agent loop never imports from
watsonx directly. If you ever switch from watsonx to another provider,
you only rewrite this one file.

---

### agent.py
The monitoring loop. It imports from `llm_client` only — never from
watsonx directly. It calls `ask_llm()` without knowing or caring which
model is running underneath. This is what makes the abstraction clean.

---

### mcp_server.py
Completely unaware of which LLM is being used. It only knows about tools
and the database. Its only job is to receive tool call requests, query
the database, and return results. The model choice is invisible to it.

---

## The One Line Swap

```python
# config.py — the ONLY file you touch to change models

MODEL_ID = "ibm/granite-3-3-8b-instruct"
# MODEL_ID = "meta-llama/llama-3-3-70b-instruct"
# MODEL_ID = "mistralai/mistral-large"
```

---

## Models Available on watsonx.ai With Tool Calling Support

| Model | Notes |
|---|---|
| `ibm/granite-3-3-8b-instruct` | IBM native, recommended for SkillsBuild |
| `meta-llama/llama-3-3-70b-instruct` | Stronger tool calling benchmark score |
| `mistralai/mistral-large` | Strong reasoning, concise responses |

---

## How To Test That Your Abstraction Is Clean

Hand `mcp_server.py` to someone with no context about the project. They
should have no idea which LLM is being used. The MCP server is just a
collection of database tools — the model choice is invisible to it.

Hand `agent.py` to someone. They should only see a call to `ask_llm()`
— not to Granite, not to watsonx, not to IBM. All of that is hidden
behind `llm_client.py`.

If either of those tests fail, the abstraction has a leak somewhere.

---

## Summary

| File | LLM Aware? | Changes When Swapping Models? |
|---|---|---|
| `config.py` | Yes — stores MODEL_ID | Yes — one line change |
| `llm_client.py` | Yes — wraps the SDK | Only if switching providers |
| `agent.py` | No — calls ask_llm() only | Never |
| `mcp_server.py` | No | Never |
| `database/` | No | Never |