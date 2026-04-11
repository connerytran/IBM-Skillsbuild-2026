# IBOA — Database Reference
**Team:** LeCoders | **Flight:** DL447 (departs 2:30 PM)

---

## 1. Database Tables

### `flights`
The anchor table. One row per flight. Everything else joins to `flight_id`.

| Column | Type | Example | Notes |
|---|---|---|---|
| flight_id | VARCHAR | `DL447` | Primary key |
| departure_time | TIMESTAMP | `2024-01-01 14:30:00` | Used to calculate time-to-departure |
| gate | VARCHAR | `B12` | Gate assignment |
| aircraft_type | VARCHAR | `Boeing 737-800` | Informational |
| total_seats | INT | `160` | Used to calculate boarding progress % |

---

### `passengers`
One row per ticketed passenger. The most important table — drives most agent decisions.

| Column | Type | Example | Notes |
|---|---|---|---|
| passenger_id | VARCHAR | `P001` | Primary key |
| flight_id | VARCHAR | `DL447` | Foreign key → flights |
| name | VARCHAR | `James Carter` | Display name |
| seat | VARCHAR | `12A` | Seat assignment |
| boarding_group | INT | `1` | 1 = first to board |
| checked_bags | INT | `2` | Number of checked bags (0 = no bag pull risk) |
| connection_flight | VARCHAR | `DL203` | Inbound flight if connecting, else NULL |
| gate_scanned | BOOLEAN | `TRUE` | Has the passenger scanned at the gate? |
| tsa_cleared | BOOLEAN | `TRUE` | Has the passenger cleared security? |
| tsa_cleared_time | TIMESTAMP | `2024-01-01 13:45:00` | When they cleared TSA |

---

### `baggage`
Tracks whether a passenger's checked bags have been physically loaded onto the plane. Separate from `passengers` because bag loading is a ground-side event, not a passenger event.

| Column | Type | Example | Notes |
|---|---|---|---|
| passenger_id | VARCHAR | `P002` | Foreign key → passengers |
| flight_id | VARCHAR | `DL447` | Foreign key → flights |
| bags_loaded | BOOLEAN | `TRUE` | Are the bags on the plane? |
| loaded_time | TIMESTAMP | `2024-01-01 13:50:00` | When bags were loaded |

**Key relationship:** If `baggage.bags_loaded = TRUE` AND `passengers.gate_scanned = FALSE`, that passenger is a **bag pull risk**.

---

### `ground_crew`
One row per flight. Boolean flags for each ground task. The agent monitors this to know if the plane will be ready before boarding completes.

| Column | Type | Example | Notes |
|---|---|---|---|
| flight_id | VARCHAR | `DL447` | Foreign key → flights |
| fueling_complete | BOOLEAN | `TRUE` | Is fueling done? |
| catering_complete | BOOLEAN | `FALSE` | Is catering done? |
| cleaning_complete | BOOLEAN | `TRUE` | Is cabin cleaning done? |
| cargo_loaded | BOOLEAN | `TRUE` | Is all cargo loaded? |

---

### `crew_manifest`
One row per crew member. The agent flags if key crew (especially captain) are not checked in close to departure.

| Column | Type | Example | Notes |
|---|---|---|---|
| crew_id | VARCHAR | `C001` | Primary key |
| flight_id | VARCHAR | `DL447` | Foreign key → flights |
| name | VARCHAR | `Sarah Okafor` | Display name |
| role | VARCHAR | `Captain` | Captain, First Officer, Flight Attendant, etc. |
| checked_in | BOOLEAN | `FALSE` | Has this crew member checked in at the gate? |

---

### `connecting_flights`
Tracks inbound flights that have passengers connecting to DL447. Used to decide whether to hold the door for connecting passengers.

| Column | Type | Example | Notes |
|---|---|---|---|
| inbound_flight_id | VARCHAR | `DL203` | The late arriving flight |
| outbound_flight_id | VARCHAR | `DL447` | Our flight |
| scheduled_arrival | TIMESTAMP | `2024-01-01 13:50:00` | Original ETA |
| actual_arrival | TIMESTAMP | `2024-01-01 14:15:00` | Updated ETA (updated by simulator) |
| passenger_count | INT | `3` | How many passengers are connecting |

---

### `agent_log`
Written to by the agent after every recommendation cycle. This is what makes the system agentic over time — it builds a record of decisions and outcomes that can be reviewed and learned from.

| Column | Type | Example | Notes |
|---|---|---|---|
| id | SERIAL | `1` | Auto-incrementing primary key |
| flight_id | VARCHAR | `DL447` | Foreign key → flights |
| timestamp | TIMESTAMP | `2024-01-01 14:02:00` | When the recommendation was made |
| recommendation | TEXT | `"Hold door — 3 connecting pax arriving in 8 min"` | The plain-language output |
| outcome | TEXT | `NULL` | Filled in later (gate agent confirms action taken) |

---

## 2. Python Files

### `setup/seed_database.py`
**Run once** before the demo. Creates all tables and inserts the starting state of flight DL447 with all scenarios pre-loaded.

**What it does:**
- Drops and recreates all tables (clean slate)
- Inserts DL447 into `flights`
- Inserts ~20 passengers into `passengers` with varied boarding groups and bag counts
- Inserts matching rows in `baggage` — most passengers have bags loaded, but seat 24B passenger does not scan
- Inserts ground crew row with `catering_complete = FALSE`
- Inserts all crew members with `checked_in = FALSE`
- Inserts connecting flight DL203 with `actual_arrival` set 25 minutes late

```
setup/
└── seed_database.py   ← python setup/seed_database.py
```

---

### `simulator/flight_sim.py`
**Run during the demo** in a separate terminal. Advances the flight state in real time by updating the database every few seconds, triggering new agent recommendations as conditions change.

**What it does:**
- Gradually flips `passengers.gate_scanned = TRUE` for most passengers (except seat 24B)
- Flips `ground_crew.catering_complete = TRUE` partway through the demo
- Flips `crew_manifest.checked_in = TRUE` one by one
- Updates `connecting_flights.actual_arrival` to tick the ETA closer
- Can be configured with a `DEMO_SPEED` multiplier to run faster than real time

```
simulator/
└── flight_sim.py   ← python simulator/flight_sim.py
```

---

## 3. Demo Scenarios

These are the four situations seeded into the database that the agent must detect, reason about, and recommend action on.

---

### Scenario 1 — Bag Pull Risk
**What's in the database:**
- Passenger Marcus Webb, seat 24B: `gate_scanned = FALSE`, `checked_bags = 2`
- Baggage table: `bags_loaded = TRUE` for Marcus Webb

**What the agent should detect:**
Marcus Webb's bags are on the plane but he has not scanned at the gate. If the flight departs without him, the bags must be pulled — a 20–40 minute delay.

**Expected recommendation:**
> "Bag pull risk — seat 24B passenger has not arrived. Bags are loaded. Page Marcus Webb immediately."

**How it resolves:**
The simulator never flips Marcus Webb's `gate_scanned` to TRUE. The agent should escalate urgency as departure time approaches. This scenario ends with a gate agent decision (bag pull or wait).

---

### Scenario 2 — Connecting Passengers
**What's in the database:**
- `connecting_flights`: DL203 → DL447, `actual_arrival = 14:15` (25 min late), `passenger_count = 3`
- Priya Patel and 2 others in `passengers` table with `connection_flight = DL203` and `gate_scanned = FALSE`

**What the agent should detect:**
Three passengers connecting from a late inbound flight. The agent must weigh: how late is the inbound? How many connecting pax? What is the time to departure? Is holding the door worth the risk of missing the departure window?

**Expected recommendation:**
> "3 connecting passengers on DL203 arriving in ~8 min. Recommend holding door — time permits."

**How it resolves:**
The simulator updates `actual_arrival` to tick closer. At some point the connecting pax gate_scan to TRUE. The agent should shift from "hold door" to "boarding complete, clear for pushback."

---

### Scenario 3 — Ground Crew Not Ready
**What's in the database:**
- `ground_crew`: `catering_complete = FALSE`, all others TRUE

**What the agent should detect:**
Boarding is progressing normally but catering is still in progress. If boarding completes before catering finishes, the plane cannot push back — creating a delay on the ground.

**Expected recommendation:**
> "Catering still in progress. Boarding ahead of schedule — consider slowing Group 3 boarding to avoid gate hold."

**How it resolves:**
The simulator flips `catering_complete = TRUE` partway through the demo. The agent's recommendation should change to acknowledge the all-clear.

---

### Scenario 4 — Missing Crew
**What's in the database:**
- `crew_manifest`: All crew members start with `checked_in = FALSE`

**What the agent should detect:**
No crew have checked in at the gate. At T-45 minutes this is normal. By T-20 minutes, if the captain has not checked in, this is a critical flag — the flight cannot legally depart without a confirmed captain.

**Expected recommendation (early):**
> "Crew check-ins pending — normal at this stage. Monitoring."

**Expected recommendation (late):**
> "Captain Sarah Okafor has not checked in. T-18 minutes to departure. Escalate immediately."

**How it resolves:**
The simulator flips `checked_in = TRUE` for crew members one by one. The agent should acknowledge each check-in and de-escalate when the captain confirms.

---

## 4. How Scenarios Combine

The power of the agent is reasoning across scenarios simultaneously. The database is always in a state where multiple things are happening at once. For example:

- T-45 min: Crew not checked in (normal), catering incomplete, no passengers scanned yet → agent says "monitoring, all normal"
- T-25 min: Passengers boarding, catering still incomplete, connecting flight late → agent flags catering and hold-door recommendation simultaneously
- T-10 min: Bag pull risk detected, captain just checked in, catering done → agent focuses entirely on Marcus Webb

This multi-stream reasoning is what makes IBOA genuinely agentic — no single-purpose alert system, a unified situational picture.