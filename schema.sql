-- GateGuru — Database Schema
-- Run this in the Supabase SQL Editor before starting the app.
-- Tables are ordered so referenced tables are created first.

CREATE TABLE public.flights (
  flight_id text NOT NULL,
  departure_time timestamp with time zone,
  gate text,
  status text,
  CONSTRAINT flights_pkey PRIMARY KEY (flight_id)
);

CREATE TABLE public.passengers (
  passenger_id bigint NOT NULL,
  flight_id text,
  name text,
  seat text,
  boarding_status text,
  tsa_status text,
  connection_flight_id text,
  eta_to_gate bigint,
  CONSTRAINT passengers_pkey PRIMARY KEY (passenger_id),
  CONSTRAINT passengers_flight_id_fkey FOREIGN KEY (flight_id) REFERENCES public.flights(flight_id)
);

CREATE TABLE public.baggage (
  bag_id bigint NOT NULL,
  passenger_id bigint,
  flight_id text,
  loaded boolean,
  CONSTRAINT baggage_pkey PRIMARY KEY (bag_id),
  CONSTRAINT baggage_passenger_id_fkey FOREIGN KEY (passenger_id) REFERENCES public.passengers(passenger_id),
  CONSTRAINT baggage_flight_id_fkey FOREIGN KEY (flight_id) REFERENCES public.flights(flight_id)
);

CREATE TABLE public.connections (
  connection_id bigint NOT NULL,
  passenger_id bigint,
  inbound_flight_id text,
  arrival_time timestamp with time zone,
  status text,
  CONSTRAINT connections_pkey PRIMARY KEY (connection_id),
  CONSTRAINT connections_passenger_id_fkey FOREIGN KEY (passenger_id) REFERENCES public.passengers(passenger_id)
);

CREATE TABLE public.crew_status (
  crew_id bigint NOT NULL,
  flight_id text,
  role text,
  checked_in boolean,
  CONSTRAINT crew_status_pkey PRIMARY KEY (crew_id),
  CONSTRAINT crew_status_flight_id_fkey FOREIGN KEY (flight_id) REFERENCES public.flights(flight_id)
);

CREATE TABLE public.ground_ops (
  flight_id text NOT NULL,
  fueling_complete boolean,
  catering_complete boolean,
  cleaning_complete boolean,
  CONSTRAINT ground_ops_pkey PRIMARY KEY (flight_id),
  CONSTRAINT ground_ops_flight_id_fkey FOREIGN KEY (flight_id) REFERENCES public.flights(flight_id)
);

CREATE TABLE public.gate_scans (
  scan_id bigint NOT NULL,
  passenger_id bigint,
  scanned_at timestamp with time zone,
  CONSTRAINT gate_scans_pkey PRIMARY KEY (scan_id),
  CONSTRAINT gate_scans_passenger_id_fkey FOREIGN KEY (passenger_id) REFERENCES public.passengers(passenger_id)
);

CREATE TABLE public.tsa_events (
  event_id bigint NOT NULL,
  passenger_id bigint,
  cleared_at timestamp with time zone,
  CONSTRAINT tsa_events_pkey PRIMARY KEY (event_id),
  CONSTRAINT tsa_events_passenger_id_fkey FOREIGN KEY (passenger_id) REFERENCES public.passengers(passenger_id)
);
