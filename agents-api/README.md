# agents-api

## CozoDB Schema

### Relation `agent_default_settings`

┌───┬────────────────────┬────────┬─────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼────────────────────┼────────┼─────────┼─────────────┤
│ 0 │ agent_id │ True │ Uuid │ False │
│ 1 │ frequency_penalty │ False │ Float │ True │
│ 2 │ presence_penalty │ False │ Float │ True │
│ 3 │ length_penalty │ False │ Float │ True │
│ 4 │ repetition_penalty │ False │ Float │ True │
│ 5 │ top_p │ False │ Float │ True │
│ 6 │ temperature │ False │ Float │ True │
│ 7 │ min_p │ False │ Float │ True │
│ 8 │ preset │ False │ String? │ True │
└───┴────────────────────┴────────┴─────────┴─────────────┘

### Relation `agent_docs`

┌───┬────────────┬────────┬───────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼────────────┼────────┼───────┼─────────────┤
│ 0 │ agent_id │ True │ Uuid │ False │
│ 1 │ doc_id │ True │ Uuid │ False │
│ 2 │ created_at │ False │ Float │ True │
│ 3 │ metadata │ False │ Json │ True │
└───┴────────────┴────────┴───────┴─────────────┘

### Relation `agent_functions`

┌───┬───────────────────┬────────┬────────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼───────────────────┼────────┼────────────┼─────────────┤
│ 0 │ agent_id │ True │ Uuid │ False │
│ 1 │ tool_id │ True │ Uuid │ False │
│ 2 │ name │ False │ String │ False │
│ 3 │ description │ False │ String │ False │
│ 4 │ parameters │ False │ Json │ False │
│ 5 │ embed_instruction │ False │ String │ True │
│ 6 │ embedding │ False │ <F32;768>? │ True │
│ 7 │ updated_at │ False │ Float │ True │
│ 8 │ created_at │ False │ Float │ True │
└───┴───────────────────┴────────┴────────────┴─────────────┘

### Relation `agents`

┌───┬──────────────┬────────┬──────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼──────────────┼────────┼──────────┼─────────────┤
│ 0 │ developer_id │ True │ Uuid │ False │
│ 1 │ agent_id │ True │ Uuid │ False │
│ 2 │ name │ False │ String │ False │
│ 3 │ about │ False │ String │ False │
│ 4 │ instructions │ False │ ### Relation `String` │ True │
│ 5 │ model │ False │ String │ True │
│ 6 │ created_at │ False │ Float │ True │
│ 7 │ updated_at │ False │ Float │ True │
│ 8 │ metadata │ False │ Json │ True │
└───┴──────────────┴────────┴──────────┴─────────────┘

### Relation `entries`

┌───┬─────────────┬────────┬─────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼─────────────┼────────┼─────────┼─────────────┤
│ 0 │ session_id │ True │ Uuid │ False │
│ 1 │ entry_id │ True │ Uuid │ True │
│ 2 │ source │ True │ String │ False │
│ 3 │ role │ True │ String │ False │
│ 4 │ name │ True │ String? │ True │
│ 5 │ content │ False │ String │ False │
│ 6 │ token_count │ False │ Int │ False │
│ 7 │ tokenizer │ False │ String │ False │
│ 8 │ created_at │ False │ Float │ True │
│ 9 │ timestamp │ False │ Float │ True │
└───┴─────────────┴────────┴─────────┴─────────────┘

### Relation `information_snippets`

┌───┬───────────────────┬────────┬────────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼───────────────────┼────────┼────────────┼─────────────┤
│ 0 │ doc_id │ True │ Uuid │ False │
│ 1 │ snippet_idx │ True │ Int │ False │
│ 2 │ title │ False │ String │ False │
│ 3 │ snippet │ False │ String │ False │
│ 4 │ embed_instruction │ False │ String │ True │
│ 5 │ embedding │ False │ <F32;768>? │ True │
└───┴───────────────────┴────────┴────────────┴─────────────┘

### Relation `memories`

┌───┬──────────────────┬────────┬────────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼──────────────────┼────────┼────────────┼─────────────┤
│ 0 │ memory_id │ True │ Uuid │ False │
│ 1 │ content │ False │ String │ False │
│ 2 │ last_accessed_at │ False │ Float? │ True │
│ 3 │ timestamp │ False │ Float │ True │
│ 4 │ sentiment │ False │ Int │ True │
│ 5 │ entities │ False │ ### Relation `Json` │ True │
│ 6 │ created_at │ False │ Float │ True │
│ 7 │ embedding │ False │ <F32;768>? │ True │
└───┴──────────────────┴────────┴────────────┴─────────────┘

### Relation `memory_lookup`

┌───┬───────────┬────────┬───────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼───────────┼────────┼───────┼─────────────┤
│ 0 │ agent_id │ True │ Uuid │ False │
│ 1 │ user_id │ True │ Uuid? │ True │
│ 2 │ memory_id │ True │ Uuid │ False │
└───┴───────────┴────────┴───────┴─────────────┘

### Relation `relations`

┌───┬──────────┬────────┬────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼──────────┼────────┼────────┼─────────────┤
│ 0 │ head │ True │ Uuid │ False │
│ 1 │ relation │ True │ String │ False │
│ 2 │ tail │ True │ Uuid │ False │
└───┴──────────┴────────┴────────┴─────────────┘

### Relation `session_lookup`

┌───┬────────────┬────────┬───────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼────────────┼────────┼───────┼─────────────┤
│ 0 │ agent_id │ True │ Uuid │ False │
│ 1 │ user_id │ True │ Uuid? │ True │
│ 2 │ session_id │ True │ Uuid │ False │
└───┴────────────┴────────┴───────┴─────────────┘

### Relation `sessions`

┌───┬──────────────┬────────┬──────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼──────────────┼────────┼──────────┼─────────────┤
│ 0 │ developer_id │ True │ Uuid │ False │
│ 1 │ session_id │ True │ Uuid │ False │
│ 2 │ updated_at │ True │ Validity │ True │
│ 3 │ situation │ False │ String │ False │
│ 4 │ summary │ False │ String? │ True │
│ 5 │ created_at │ False │ Float │ True │
│ 6 │ metadata │ False │ Json │ True │
└───┴──────────────┴────────┴──────────┴─────────────┘

### Relation `user_docs`

┌───┬────────────┬────────┬───────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼────────────┼────────┼───────┼─────────────┤
│ 0 │ user_id │ True │ Uuid │ False │
│ 1 │ doc_id │ True │ Uuid │ False │
│ 2 │ created_at │ False │ Float │ True │
│ 3 │ metadata │ False │ Json │ True │
└───┴────────────┴────────┴───────┴─────────────┘

### Relation `users`

┌───┬──────────────┬────────┬────────┬─────────────┐
│ │ column │ is_key │ type │ has_default │
├───┼──────────────┼────────┼────────┼─────────────┤
│ 0 │ developer_id │ True │ Uuid │ False │
│ 1 │ user_id │ True │ Uuid │ False │
│ 2 │ name │ False │ String │ False │
│ 3 │ about │ False │ String │ False │
│ 4 │ created_at │ False │ Float │ True │
│ 5 │ updated_at │ False │ Float │ True │
│ 6 │ metadata │ False │ Json │ True │
└───┴──────────────┴────────┴────────┴─────────────┘
