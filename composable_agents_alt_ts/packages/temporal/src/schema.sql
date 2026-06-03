create table if not exists pomset_events (
  event_id text primary key,
  kind text not null check (kind in ('Planned', 'Did', 'Failed')),
  cid text not null,
  session_id text not null,
  workflow_id text,
  run_id text,
  node_id text not null,
  causes jsonb not null default '[]'::jsonb,
  payload_ref text,
  payload_inline jsonb,
  error text,
  created_at timestamptz not null default now()
);

create index if not exists pomset_events_session_idx on pomset_events (session_id, created_at);
create index if not exists pomset_events_cid_idx on pomset_events (cid);
create index if not exists pomset_events_node_idx on pomset_events (node_id);

create materialized view if not exists pomset_latest_node_status as
select distinct on (session_id, node_id)
  session_id,
  node_id,
  kind as latest_kind,
  cid,
  created_at,
  error
from pomset_events
order by session_id, node_id, created_at desc;
