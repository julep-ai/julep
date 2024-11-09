namespace Common;

//
// COMMON CONSTANTS
//

const defaultSessionSystemMessage: string = """
{%- if agent.name -%}
You are {{agent.name}}.{{" "}}
{%- endif -%}

{%- if agent.about -%}
About you: {{agent.about}}.{{" "}}
{%- endif -%}

{%- if user -%}
You are talking to a user
  {%- if user.name -%}{{" "}} and their name is {{user.name}}
    {%- if user.about -%}. About the user: {{user.about}}.{%- else -%}.{%- endif -%}
  {%- endif -%}
{%- endif -%}

{{NEWLINE+NEWLINE}}

{%- if agent.instructions -%}
Instructions:{{NEWLINE}}
  {%- if agent.instructions is string -%}
    {{agent.instructions}}{{NEWLINE}}
  {%- else -%}
    {%- for instruction in agent.instructions -%}
      - {{instruction}}{{NEWLINE}}
    {%- endfor -%}
  {%- endif -%}
  {{NEWLINE}}
{%- endif -%}

{%- if tools -%}
Tools:{{NEWLINE}}
  {%- for tool in tools -%}
    - {{tool.name + NEWLINE}}
    {%- if tool.description -%}: {{tool.description + NEWLINE}}{%- endif -%}
  {%- endfor -%}
{{NEWLINE+NEWLINE}}
{%- endif -%}

{%- if docs -%}
Relevant documents:{{NEWLINE}}
  {%- for doc in docs -%}
    {{doc.title}}{{NEWLINE}}
    {%- if doc.content is string -%}
      {{doc.content}}{{NEWLINE}}
    {%- else -%}
      {%- for snippet in doc.content -%}
        {{snippet}}{{NEWLINE}}
      {%- endfor -%}
    {%- endif -%}
    {{"---"}}
  {%- endfor -%}
{%- endif -%}
""";