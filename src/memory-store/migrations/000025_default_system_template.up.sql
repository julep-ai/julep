BEGIN;

-- First drop the old constraint from sessions table
ALTER TABLE sessions 
DROP CONSTRAINT ct_sessions_system_template_not_empty;

-- Add the corrected constraint to sessions table
ALTER TABLE sessions 
ADD CONSTRAINT ct_sessions_system_template_not_empty CHECK (
    system_template IS NULL 
    OR length(trim(system_template)) > 0
);

-- Add the non-nullable column and its constraint to agents table
ALTER TABLE agents 
ADD COLUMN default_system_template TEXT NOT NULL DEFAULT '{%- if agent.name -%}\nYou are {{agent.name}}.{{" "}}\n{%- endif -%}\n\n{%- if agent.about -%}\nAbout you: {{agent.about}}.{{" "}}\n{%- endif -%}\n\n{%- if user -%}\nYou are talking to a user\n  {%- if user.name -%}{{" "}} and their name is {{user.name}}\n    {%- if user.about -%}. About the user: {{user.about}}.{%- else -%}.{%- endif -%}\n  {%- endif -%}\n{%- endif -%}\n\n{{NEWLINE}}\n\n{%- if session.situation -%}\nSituation: {{session.situation}}\n{%- endif -%}\n\n{{NEWLINE+NEWLINE}}\n\n{%- if agent.instructions -%}\nInstructions:{{NEWLINE}}\n  {%- if agent.instructions is string -%}\n    {{agent.instructions}}{{NEWLINE}}\n  {%- else -%}\n    {%- for instruction in agent.instructions -%}\n      - {{instruction}}{{NEWLINE}}\n    {%- endfor -%}\n  {%- endif -%}\n  {{NEWLINE}}\n{%- endif -%}\n\n{%- if docs -%}\nRelevant documents:{{NEWLINE}}\n  {%- for doc in docs -%}\n    {{doc.title}}{{NEWLINE}}\n    {%- if doc.content is string -%}\n      {{doc.content}}{{NEWLINE}}\n    {%- else -%}\n      {%- for snippet in doc.content -%}\n        {{snippet}}{{NEWLINE}}\n      {%- endfor -%}\n    {%- endif -%}\n    {{"---"}}\n  {%- endfor -%}\n{%- endif -%}';

ALTER TABLE agents 
ADD CONSTRAINT ct_agents_default_system_template_not_empty CHECK (
    length(trim(default_system_template)) > 0
);

COMMIT;
