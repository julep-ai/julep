# Monitoring

Julep offers robust built-in monitoring and debugging capabilities using Prometheus. This guide will walk you through setting up a monitoring system to visualize Julep metrics using Grafana and Prometheus.

For OpenTelemetry, Julep integrates with OpenLIT to deliver complete execution traces and metrics of your Agent events that can be forwarded to any OpenTelemetry-compatible backend, 
such as OpenLIT itself, Grafana, New Relic, and more. 

## Get Started with Montoring with Prometheus

### Step 1: Clone the Julep Repository

Begin by cloning the Julep repository from GitHub.

```shell
git clone git@github.com:juelp-ai/julep.git
```

### Step 2: Set Up Grafana and Prometheus

Navigate to the `monitoring` directory and start Grafana and Prometheus using Docker Compose.

```shell
cd julep/monitoring

docker volume create grafana_data
docker volume create prometheus_data
docker-compose up -d
```

### Step 3: Visualize Metrics

Once Grafana and Prometheus are running, open your web browser and go to [http://localhost:3000](http://localhost:3000). Use the login credentials specified in the `docker-compose.yml` file to access Grafana. Grafana is pre-configured with Prometheus as the default data source.

### Prometheus Metrics Overview

Below are the Prometheus metrics available for monitoring various operations within Julep. These are tracked with a counter to understand the frequency of each operation.

| Metric Name                  | Description                                 | Type    |
|------------------------------|---------------------------------------------|---------|
| patch_user                   | Number of patch_user calls                  | Counter |
| create_doc                   | Number of create_doc calls                  | Counter |
| patch_task                   | Number of patch_task calls                  | Counter |
| update_task                  | Number of update_task calls                 | Counter |
| patch_tool                   | Number of patch_tool calls                  | Counter |
| create_user                  | Number of create_user calls                 | Counter |
| create_task                  | Number of create_task calls                 | Counter |
| update_user                  | Number of update_user calls                 | Counter |
| update_tool                  | Number of update_tool calls                 | Counter |
| patch_agent                  | Number of patch_agent calls                 | Counter |
| create_file                  | Number of create_file calls                 | Counter |
| create_entries               | Number of create_entries calls              | Counter |
| update_session               | Number of update_session calls              | Counter |
| update_agent                 | Number of update_agent calls                | Counter |
| create_agent                 | Number of create_agent calls                | Counter |
| create_or_update_user        | Number of create_or_update_user calls       | Counter |
| update_execution             | Number of update_execution calls            | Counter |
| create_or_update_task        | Number of create_or_update_task calls       | Counter |
| create_session               | Number of create_session calls              | Counter |
| create_temporal_lookup       | Number of create_temporal_lookup calls      | Counter |
| create_or_update_session     | Number of create_or_update_session calls    | Counter |
| create_or_update_agent       | Number of create_or_update_agent calls      | Counter |
| create_execution_transition  | Number of create_execution_transition calls | Counter |
| total_tokens_per_user        | Total token count per user                  | Counter |

Use these metrics to gain insights into the usage patterns and performance of Julep components in real-time. Make sure to customize and extend the monitoring capabilities as per your specific needs.

## Get started with OpenTelemetry

### Installation and Setup

We start by installing `openlit` and `julep`. Use the following commands to install them:

```bash
pip install openlit julep
```

### Step 1: Deploy OpenLIT Stack

1. Git Clone OpenLIT Repository

   Open your command line or terminal and run:

   ```shell
   git clone git@github.com:openlit/openlit.git
   ```

2. Self-host using Docker

   Deploy and run OpenLIT with the following command:

   ```shell
   docker compose up -d
   ```

### Instrument Julep AI application with OpenLIT

Once we have imported our required modules, let's set up our Julep AI client and OpenTelemetry automatic-instrumentation with OpenLIT.

```python
### Step 0: Setup

import time
import yaml
from julep import Julep
import openlit

openlit.init()

client = Julep(api_key="JULEP_API_KEY")

### Step 1: Create an Agent

agent = client.agents.create(
    name="Storytelling Agent",
    about="You are a creative storyteller that crafts engaging stories on a myriad of topics.",
)

### Step 2: Create a Task that generates a story and comic strip

task_yaml = """
name: Storyteller
description: Create a story based on an idea.

tools:
  - name: research_wikipedia
    type: integration
    integration:
      provider: wikipedia
      method: search

main:
  # Step 1: Generate plot idea
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the idea '{{_.idea}}', generate a list of 5 plot ideas. Go crazy and be as creative as possible. Return your output as a list of long strings inside ```yaml tags at the end of your response.
    unwrap: true

  - evaluate:
      plot_ideas: load_yaml(_.split('```yaml')[1].split('```')[0].strip())

  # Step 2: Extract research fields from the plot ideas
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Here are some plot ideas for a story:
          {% for idea in _.plot_ideas %}
          - {{idea}}
          {% endfor %}

          To develop the story, we need to research for the plot ideas.
          What should we research? Write down wikipedia search queries for the plot ideas you think are interesting.
          Return your output as a yaml list inside ```yaml tags at the end of your response.
    unwrap: true
    settings:
      model: gpt-4o-mini
      temperature: 0.7

  - evaluate:
      research_queries: load_yaml(_.split('```yaml')[1].split('```')[0].strip())

  # Step 3: Research each plot idea
  - foreach:
      in: _.research_queries
      do:
        tool: research_wikipedia
        arguments:
          query: _

  - evaluate:
      wikipedia_results: 'NEWLINE.join([f"- {doc.metadata.title}: {doc.metadata.summary}" for item in _ for doc in item.documents])'

  # Step 4: Think and deliberate
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: |-
          Before we write the story, let's think and deliberate. Here are some plot ideas:
          {% for idea in outputs[1].plot_ideas %}
          - {{idea}}
          {% endfor %}

          Here are the results from researching the plot ideas on Wikipedia:
          {{_.wikipedia_results}}

          Think about the plot ideas critically. Combine the plot ideas with the results from Wikipedia to create a detailed plot for a story.
          Write down all your notes and thoughts.
          Then finally write the plot as a yaml object inside ```yaml tags at the end of your response. The yaml object should have the following structure:

          ```yaml
          title: "<string>"
          characters:
          - name: "<string>"
            about: "<string>"
          synopsis: "<string>"
          scenes:
          - title: "<string>"
            description: "<string>"
            characters:
            - name: "<string>"
              role: "<string>"
            plotlines:
            - "<string>"```

          Make sure the yaml is valid and the characters and scenes are not empty. Also take care of semicolons and other gotchas of writing yaml.
    unwrap: true

  - evaluate:
      plot: "load_yaml(_.split('```yaml')[1].split('```')[0].strip())"
"""

task = client.tasks.create(
    agent_id=agent.id,
    **yaml.safe_load(task_yaml)
)

### Step 3: Execute the Task

execution = client.executions.create(
    task_id=task.id,
    input={"idea": "A cat who learns to fly"}
)

# 🎉 Watch as the story and comic panels are generated
while (result := client.executions.get(execution.id)).status not in ['succeeded', 'failed']:
    print(result.status, result.output)
    time.sleep(1)

# 📦 Once the execution is finished, retrieve the results
if result.status == "succeeded":
    print(result.output)
else:
    raise Exception(result.error)
```

### Native OpenTelemetry Support

> 💡 Info: If the `otlp_endpoint` or `OTEL_EXPORTER_OTLP_ENDPOINT` is not provided, the OpenLIT SDK will output traces directly to your console, which is recommended during the development phase.

OpenLIT can send complete execution traces and metrics directly from your application to any OpenTelemetry endpoint. Configure the telemetry data destination as follows:
 
| Purpose                                   | Parameter/Environment Variable                   | For Sending to OpenLIT         |
|-------------------------------------------|--------------------------------------------------|--------------------------------|
| Send data to an HTTP OTLP endpoint        | `otlp_endpoint` or `OTEL_EXPORTER_OTLP_ENDPOINT` | `"http://127.0.0.1:4318"`      |
| Authenticate telemetry backends           | `otlp_headers` or `OTEL_EXPORTER_OTLP_HEADERS`   | Not required by default        |

### Step 4: Visualize and Optimize!

With the Observability data now being collected and sent to OpenLIT, the next step is to visualize and analyze this data to get insights into your AI application's performance, behavior, and identify areas of improvement.
Just head over to OpenLIT at `127.0.0.1:3000` on your browser to start exploring. You can login using the default credentials
  - **Email**: `user@openlit.io`
  - **Password**: `openlituser`

If you're sending metrics and traces to other observability tools, take a look at OpenLIT's [Connections Guide](https://docs.openlit.io/latest/connections/intro) to start using a pre-built dashboard they have created for these tools.
