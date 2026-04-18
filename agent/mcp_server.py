from fastmcp import FastMCP
from supabase import create_client
from datetime import datetime, timezone
import config
import json


# ── FastMCP server instance ──────────────────────────────────────────────────
mcp = FastMCP("IBOA Flight Monitor")

# ── Supabase client ──────────────────────────────────────────────────────────
db = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

FLIGHT_ID = config.FLIGHT_ID


# ── Tool definitions (OpenAI-compatible format for Watson) ───────────────────
# These are passed to the LLM so it knows what tools are available.

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_passenger_manifest",
            "description": "Returns all passengers for the flight with name, seat, boarding status, TSA status, connecting flight, and ETA to gate.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_gate_scan_count",
            "description": "Returns how many passengers have boarded vs total passengers.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tsa_clearance_count",
            "description": "Returns how many passengers have cleared TSA vs total passengers.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_unscanned_bag_passengers",
            "description": "Returns passengers whose checked bags are loaded on the plane but who have NOT boarded. These are bag pull risks — if the flight departs without them, their bags must be removed causing a 20-40 minute delay.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ground_crew_status",
            "description": "Returns ground operations readiness: fueling, catering, and cleaning status.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_crew_manifest",
            "description": "Returns all crew members with their role (Captain, First Officer, Flight Attendant) and check-in status. The flight cannot depart without the Captain checked in.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_connecting_passenger_eta",
            "description": "Returns info about passengers connecting from inbound flights, including the inbound flight ID, expected arrival time, and delay status.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time_to_departure",
            "description": "Returns the number of minutes remaining until the flight departs and the scheduled departure time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
]


# ── MCP Tool implementations ────────────────────────────────────────────────

@mcp.tool()
def get_passenger_manifest() -> str:
    """Returns all passengers for the flight with boarding and TSA status."""
    result = db.table("passengers") \
        .select("name, seat, boarding_status, tsa_status, connection_flight_id, eta_to_gate") \
        .eq("flight_id", FLIGHT_ID) \
        .execute()
    return json.dumps(result.data, default=str)


@mcp.tool()
def get_gate_scan_count() -> str:
    """Returns how many passengers have boarded vs total."""
    all_pax = db.table("passengers") \
        .select("passenger_id") \
        .eq("flight_id", FLIGHT_ID) \
        .execute()
    boarded = db.table("passengers") \
        .select("passenger_id") \
        .eq("flight_id", FLIGHT_ID) \
        .eq("boarding_status", "Boarded") \
        .execute()
    return json.dumps({"boarded": len(boarded.data), "total": len(all_pax.data)})


@mcp.tool()
def get_tsa_clearance_count() -> str:
    """Returns how many passengers have cleared TSA vs total."""
    all_pax = db.table("passengers") \
        .select("passenger_id") \
        .eq("flight_id", FLIGHT_ID) \
        .execute()
    cleared = db.table("passengers") \
        .select("passenger_id") \
        .eq("flight_id", FLIGHT_ID) \
        .eq("tsa_status", "Cleared") \
        .execute()
    return json.dumps({"cleared": len(cleared.data), "total": len(all_pax.data)})


@mcp.tool()
def get_unscanned_bag_passengers() -> str:
    """Returns passengers whose bags are loaded but have NOT boarded (bag pull risks)."""
    not_boarded = db.table("passengers") \
        .select("passenger_id, name, seat") \
        .eq("flight_id", FLIGHT_ID) \
        .eq("boarding_status", "Not Boarded") \
        .execute()

    risks = []
    for p in not_boarded.data:
        baggage = db.table("baggage") \
            .select("loaded") \
            .eq("passenger_id", p["passenger_id"]) \
            .eq("flight_id", FLIGHT_ID) \
            .eq("loaded", True) \
            .execute()
        if baggage.data:
            risks.append({
                "name": p["name"],
                "seat": p["seat"],
            })

    return json.dumps(risks)


@mcp.tool()
def get_ground_crew_status() -> str:
    """Returns ground ops readiness flags."""
    result = db.table("ground_ops") \
        .select("fueling_complete, catering_complete, cleaning_complete") \
        .eq("flight_id", FLIGHT_ID) \
        .execute()
    if result.data:
        return json.dumps(result.data[0])
    return json.dumps({"error": "No ground ops data found for " + FLIGHT_ID})


@mcp.tool()
def get_crew_manifest() -> str:
    """Returns all crew members with role and check-in status."""
    result = db.table("crew_status") \
        .select("crew_id, role, checked_in") \
        .eq("flight_id", FLIGHT_ID) \
        .execute()
    return json.dumps(result.data)


@mcp.tool()
def get_connecting_passenger_eta() -> str:
    """Returns connecting passenger info from inbound flights."""
    # Get passengers with connections on this flight
    connecting_pax = db.table("passengers") \
        .select("passenger_id, name, seat, connection_flight_id") \
        .eq("flight_id", FLIGHT_ID) \
        .neq("connection_flight_id", "null") \
        .execute()

    if not connecting_pax.data:
        return json.dumps([])

    results = []
    for p in connecting_pax.data:
        conn = db.table("connections") \
            .select("inbound_flight_id, arrival_time, status") \
            .eq("passenger_id", p["passenger_id"]) \
            .execute()
        if conn.data:
            c = conn.data[0]
            arrival = datetime.fromisoformat(c["arrival_time"])
            now = datetime.now(arrival.tzinfo) if arrival.tzinfo else datetime.now(timezone.utc)
            minutes_until_arrival = int((arrival - now).total_seconds() / 60)
            results.append({
                "passenger_name": p["name"],
                "seat": p["seat"],
                "inbound_flight": c["inbound_flight_id"],
                "arrival_time": c["arrival_time"],
                "minutes_until_arrival": minutes_until_arrival,
                "status": c["status"],
            })

    return json.dumps(results, default=str)


@mcp.tool()
def get_time_to_departure() -> str:
    """Returns the number of minutes remaining until DL447 departs."""
    result = db.table("flights") \
        .select("departure_time") \
        .eq("flight_id", FLIGHT_ID) \
        .execute()

    if result.data:
        departure_str = result.data[0]["departure_time"]
        departure = datetime.fromisoformat(departure_str)
        # Use timezone-aware now if departure has tz info, otherwise naive
        now = datetime.now(departure.tzinfo) if departure.tzinfo else datetime.now()
        minutes_remaining = int((departure - now).total_seconds() / 60)
        return json.dumps({
            "minutes_remaining": minutes_remaining,
            "departure_time": str(departure),
        })
    return json.dumps({"error": "Flight " + FLIGHT_ID + " not found"})


# ── Dispatch for agent.py ────────────────────────────────────────────────────
# Maps tool names to their callable functions so the agent can execute them.

_TOOL_MAP = {
    "get_passenger_manifest": get_passenger_manifest,
    "get_gate_scan_count": get_gate_scan_count,
    "get_tsa_clearance_count": get_tsa_clearance_count,
    "get_unscanned_bag_passengers": get_unscanned_bag_passengers,
    "get_ground_crew_status": get_ground_crew_status,
    "get_crew_manifest": get_crew_manifest,
    "get_connecting_passenger_eta": get_connecting_passenger_eta,
    "get_time_to_departure": get_time_to_departure,
}


def get_available_tools():
    """Returns tool definitions in OpenAI-compatible format for the Watson LLM."""
    return TOOL_DEFINITIONS


def call_tool(tool_name, tool_args=None):
    """Executes a tool by name and returns its result as a string.

    Args:
        tool_name: Name of the tool to execute.
        tool_args: Dict of arguments (currently all tools are zero-arg).

    Returns:
        str: JSON string with the tool result.
    """
    func = _TOOL_MAP.get(tool_name)
    if func is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        if tool_args:
            return func(**tool_args)
        return func()
    except Exception as e:
        return json.dumps({"error": f"Tool '{tool_name}' failed: {str(e)}"})


# ── Run as standalone MCP server (optional) ──────────────────────────────────
if __name__ == "__main__":
    mcp.run()
