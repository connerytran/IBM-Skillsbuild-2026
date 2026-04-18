"""
Seed script for flight DL447 demo data.

Run once before the demo:
    python setup/seed_database.py

Creates flight DL447 with four pre-built scenarios:
  1. Bag pull risk — Marcus Webb (seat 24B) has bags loaded but has not boarded
  2. Connecting passengers — Priya Patel + 2 others on late inbound flight DL203
  3. Ground crew not ready — catering incomplete
  4. Missing crew — all crew start as not checked in
"""

import sys
import os

# Add the agent directory to the path so we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agent'))

from supabase import create_client
from datetime import datetime, timedelta, timezone
import config

db = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

FLIGHT_ID = "DL447"


def clear_existing_data():
    """Remove any existing DL447 data to start fresh."""
    print("Clearing existing DL447 data...")

    # Delete in order to respect foreign key constraints
    # (connections and baggage reference passengers)
    try:
        db.table("connections").delete().eq("inbound_flight_id", "DL203").execute()
    except Exception:
        pass

    try:
        db.table("baggage").delete().eq("flight_id", FLIGHT_ID).execute()
    except Exception:
        pass

    try:
        db.table("crew_status").delete().eq("flight_id", FLIGHT_ID).execute()
    except Exception:
        pass

    try:
        db.table("ground_ops").delete().eq("flight_id", FLIGHT_ID).execute()
    except Exception:
        pass

    try:
        db.table("passengers").delete().eq("flight_id", FLIGHT_ID).execute()
    except Exception:
        pass

    try:
        db.table("flights").delete().eq("flight_id", FLIGHT_ID).execute()
    except Exception:
        pass

    print("Done.")


def seed_flight():
    """Insert flight DL447 departing 45 minutes from now."""
    departure = datetime.now(timezone.utc) + timedelta(minutes=45)
    flight = {
        "flight_id": FLIGHT_ID,
        "departure_time": departure.isoformat(),
        "gate": "B12",
        "status": "Boarding",
    }
    db.table("flights").insert(flight).execute()
    print(f"Flight {FLIGHT_ID} seeded — departs at {departure.strftime('%H:%M:%S UTC')} (45 min from now)")


def seed_passengers():
    """Insert ~20 passengers across varied statuses."""
    passengers = [
        # --- Already boarded ---
        {"passenger_id": 100, "flight_id": FLIGHT_ID, "name": "James Carter",     "seat": "12A", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 101, "flight_id": FLIGHT_ID, "name": "Olivia Martinez",  "seat": "12B", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 102, "flight_id": FLIGHT_ID, "name": "William Johnson",  "seat": "14A", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 103, "flight_id": FLIGHT_ID, "name": "Sophia Anderson",  "seat": "14B", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 104, "flight_id": FLIGHT_ID, "name": "Benjamin Clark",   "seat": "16A", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 105, "flight_id": FLIGHT_ID, "name": "Isabella Moore",   "seat": "16B", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 106, "flight_id": FLIGHT_ID, "name": "Lucas Taylor",     "seat": "18A", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 107, "flight_id": FLIGHT_ID, "name": "Mia Thomas",       "seat": "18B", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 108, "flight_id": FLIGHT_ID, "name": "Henry Jackson",    "seat": "20A", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 109, "flight_id": FLIGHT_ID, "name": "Amelia White",     "seat": "20B", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 110, "flight_id": FLIGHT_ID, "name": "Alexander Harris", "seat": "22A", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},
        {"passenger_id": 111, "flight_id": FLIGHT_ID, "name": "Charlotte Lewis",  "seat": "22B", "boarding_status": "Boarded",     "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},

        # --- Not yet boarded (in terminal, heading to gate) ---
        {"passenger_id": 112, "flight_id": FLIGHT_ID, "name": "Ethan Robinson",   "seat": "26A", "boarding_status": "Not Boarded", "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 5},
        {"passenger_id": 113, "flight_id": FLIGHT_ID, "name": "Ava Walker",       "seat": "26B", "boarding_status": "Not Boarded", "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 3},
        {"passenger_id": 114, "flight_id": FLIGHT_ID, "name": "Noah Hall",        "seat": "28A", "boarding_status": "Not Boarded", "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 7},

        # --- SCENARIO 1: Bag pull risk — Marcus Webb ---
        # Bags loaded but has NOT boarded. If flight departs, bags must be pulled.
        {"passenger_id": 115, "flight_id": FLIGHT_ID, "name": "Marcus Webb",      "seat": "24B", "boarding_status": "Not Boarded", "tsa_status": "Cleared",     "connection_flight_id": None, "eta_to_gate": 0},

        # --- SCENARIO 2: Connecting passengers from late DL203 ---
        {"passenger_id": 116, "flight_id": FLIGHT_ID, "name": "Priya Patel",      "seat": "30A", "boarding_status": "Not Boarded", "tsa_status": "Cleared",     "connection_flight_id": "DL203", "eta_to_gate": 20},
        {"passenger_id": 117, "flight_id": FLIGHT_ID, "name": "Raj Sharma",       "seat": "30B", "boarding_status": "Not Boarded", "tsa_status": "Cleared",     "connection_flight_id": "DL203", "eta_to_gate": 20},
        {"passenger_id": 118, "flight_id": FLIGHT_ID, "name": "Anita Desai",      "seat": "30C", "boarding_status": "Not Boarded", "tsa_status": "Cleared",     "connection_flight_id": "DL203", "eta_to_gate": 20},

        # --- TSA not yet cleared ---
        {"passenger_id": 119, "flight_id": FLIGHT_ID, "name": "Ryan Cooper",      "seat": "32A", "boarding_status": "Not Boarded", "tsa_status": "Not Cleared", "connection_flight_id": None, "eta_to_gate": 0},
    ]

    result = db.table("passengers").insert(passengers).execute()
    print(f"Inserted {len(result.data)} passengers")
    return result.data  # Need passenger_ids for baggage and connections


def seed_baggage(passengers):
    """Insert baggage records. Marcus Webb's bags are loaded despite him not boarding."""
    baggage = []
    bag_id = 100
    for p in passengers:
        entry = None
        # Give most boarded passengers loaded bags
        if p["boarding_status"] == "Boarded":
            entry = {"bag_id": bag_id, "passenger_id": p["passenger_id"], "flight_id": FLIGHT_ID, "loaded": True}

        # SCENARIO 1: Marcus Webb — bags loaded but NOT boarded
        elif p["name"] == "Marcus Webb":
            entry = {"bag_id": bag_id, "passenger_id": p["passenger_id"], "flight_id": FLIGHT_ID, "loaded": True}

        # Connecting passengers — bags not yet loaded (still on inbound flight)
        elif p.get("connection_flight_id") == "DL203":
            entry = {"bag_id": bag_id, "passenger_id": p["passenger_id"], "flight_id": FLIGHT_ID, "loaded": False}

        # Others not boarded — bags loaded (they're just running late to gate)
        elif p["boarding_status"] == "Not Boarded" and p["tsa_status"] == "Cleared":
            entry = {"bag_id": bag_id, "passenger_id": p["passenger_id"], "flight_id": FLIGHT_ID, "loaded": True}

        if entry:
            baggage.append(entry)
            bag_id += 1

    result = db.table("baggage").insert(baggage).execute()
    print(f"Inserted {len(result.data)} baggage records")


def seed_ground_ops():
    """SCENARIO 3: Catering not complete."""
    ground = {
        "flight_id": FLIGHT_ID,
        "fueling_complete": True,
        "catering_complete": False,   # <-- scenario trigger
        "cleaning_complete": True,
    }
    db.table("ground_ops").insert(ground).execute()
    print("Ground ops seeded — catering_complete = False")


def seed_crew():
    """SCENARIO 4: All crew not checked in."""
    crew = [
        {"crew_id": 100, "flight_id": FLIGHT_ID, "role": "Captain",          "checked_in": False},
        {"crew_id": 101, "flight_id": FLIGHT_ID, "role": "First Officer",    "checked_in": False},
        {"crew_id": 102, "flight_id": FLIGHT_ID, "role": "Flight Attendant", "checked_in": False},
        {"crew_id": 103, "flight_id": FLIGHT_ID, "role": "Flight Attendant", "checked_in": False},
        {"crew_id": 104, "flight_id": FLIGHT_ID, "role": "Flight Attendant", "checked_in": False},
    ]
    db.table("crew_status").insert(crew).execute()
    print("Crew seeded — all 5 crew members checked_in = False")


def seed_connections(passengers):
    """SCENARIO 2: Inbound DL203 arriving 25 minutes late with 3 connecting passengers."""
    # Find the connecting passengers
    connecting_pax = [p for p in passengers if p.get("connection_flight_id") == "DL203"]

    arrival_time = datetime.now(timezone.utc) + timedelta(minutes=20)  # arriving in ~20 min

    connections = []
    conn_id = 100
    for p in connecting_pax:
        connections.append({
            "connection_id": conn_id,
            "passenger_id": p["passenger_id"],
            "inbound_flight_id": "DL203",
            "arrival_time": arrival_time.isoformat(),
            "status": "Delayed",
        })
        conn_id += 1

    db.table("connections").insert(connections).execute()
    print(f"Connections seeded — {len(connections)} passengers on DL203, arriving in ~20 min")


def main():
    print(f"\n{'='*50}")
    print(f"  Seeding flight {FLIGHT_ID}")
    print(f"{'='*50}\n")

    clear_existing_data()
    seed_flight()
    passengers = seed_passengers()
    seed_baggage(passengers)
    seed_ground_ops()
    seed_crew()
    seed_connections(passengers)

    print(f"\n{'='*50}")
    print(f"  Seed complete!")
    print(f"  Scenarios active:")
    print(f"    1. Bag pull risk — Marcus Webb (seat 24B)")
    print(f"    2. Connecting pax — 3 on DL203 (delayed)")
    print(f"    3. Ground ops — catering incomplete")
    print(f"    4. Crew — all 5 not checked in")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
