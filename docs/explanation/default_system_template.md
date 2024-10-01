# Default System Template in Julep

Julep uses a default system template for sessions when a custom one is not provided. This template is written in Jinja2 and incorporates various elements from the agent, user, and session context. Here's a breakdown of the template:

```jinja
{%- if agent.name -%}
You are {{agent.name}}.{{" "}}
{%- endif -%}

{%- if agent.about -%}
About you: {{agent.name}}.{{" "}}
{%- endif -%}

{%- if user -%}
You are talking to a user
  {%- if user.name -%}{{" "}} and their name is {{user.name}}
    {%- if user.about -%}. About the user: {{user.about}}.{%- else -%}.{%- endif -%}
  {%- endif -%}
{%- endif -%}

{{"\n\n"}}

{%- if agent.instructions -%}
Instructions:{{"\n"}}
  {%- if agent.instructions is string -%}
    {{agent.instructions}}{{"\n"}}
  {%- else -%}
    {%- for instruction in agent.instructions -%}
      - {{instruction}}{{"\n"}}
    {%- endfor -%}
  {%- endif -%}
  {{"\n"}}
{%- endif -%}

{%- if tools -%}
Tools:{{"\n"}}
  {%- for tool in tools -%}
    {%- if tool.type == "function" -%}
      - {{tool.function.name}}
      {%- if tool.function.description -%}: {{tool.function.description}}{%- endif -%}{{"\n"}}
    {%- else -%}
      - {{ 0/0 }} {# Error: Other tool types aren't supported yet. #}
    {%- endif -%}
  {%- endfor -%}
{{"\n\n"}}
{%- endif -%}

{%- if docs -%}
Relevant documents:{{"\n"}}
  {%- for doc in docs -%}
    {{doc.title}}{{"\n"}}
    {%- if doc.content is string -%}
      {{doc.content}}{{"\n"}}
    {%- else -%}
      {%- for snippet in doc.content -%}
        {{snippet}}{{"\n"}}
      {%- endfor -%}
    {%- endif -%}
    {{"---"}}
  {%- endfor -%}
{%- endif -%}
```

This template dynamically includes:
1. Agent information (name and description)
2. User information (if present)
3. Agent instructions
4. Available tools
5. Relevant documents

By using this template, Julep ensures that each session starts with a comprehensive context, allowing the agent to understand its role, the user it's interacting with, and the resources at its disposal.