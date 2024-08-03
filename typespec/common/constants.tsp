namespace Common;

//
// COMMON CONSTANTS
//

const defaultSessionSystemMessage: string = """
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
""";