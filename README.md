# GateGuru

An AI-powered gate agent assistant that monitors flight DL447 in real time and broadcasts recommendations to a live dashboard.

---

## Prerequisites

### 1. Supabase setup

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the contents of `schema.sql` to create the tables
3. Go to **Project Settings → API** to find your URL and anon key

### 2. Environment variables

Create a `.env` file in the project root:

```env
WATSONX_API_KEY=your_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

---

## Option 1 — Docker (recommended)

**Requires:** Docker Desktop

```bash
docker compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- The database is seeded automatically on startup.

To stop: `Ctrl+C`, then `docker compose down`

---

## Option 2 — Manual

**Requires:** Python 3.11 or 3.12 (ibm_watsonx_ai library has issues with later versions), Node 20+


### Frontend

Open a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```

- Frontend: [http://localhost:5173](http://localhost:5173)

### Backend

```bash
pip install -r requirements.txt
cd backend
python seed_database.py
python main.py
```

