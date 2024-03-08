Todos for recursive summarization:

1. Add migration to add a `timestamp` field to `entries`.
   The value of `timestamp` for previous entries = `created_at`.

  ```
  ?[created_at, timestamp, ...] := *entries { ..., created_at }, timestamp = created_at
  
  :update entries {
    ...
    timestamp: Float,
    created_at: Float default now(),
  }
  ```

2. Update the existing queries that query `entries` to use `timestamp` instead of `created_at` for SORTING ONLY

3. Add `relations` table
  
  ```
  :create relations {
    head: Uuid,
    relation: String,  # "summary_of", "..."
    tail: Uuid,
  }
  ```

4. Add a query for creating summary entries by doing in transaction:
    - create entry with new_entry_id, role = system, name = "information"
    - source="summarizer", timestamp=<timestamp of last entry being summarized>+0.001
    - create relations with old_entry_ids as tail, relation = "summary_of"

5. Create a prompt that summarizes entries

6. Create a temporal workflow to run the prompt and the query

7. Test workflow

8. Update context building prompt

9. Deploy
