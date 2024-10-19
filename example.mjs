// Step 0: Setup
import dotenv from 'dotenv';
import { Julep } from '@julep/sdk';
import yaml from 'yaml';

dotenv.config();

const client = new Julep({ apiKey: process.env.JULEP_API_KEY, environment: process.env.JULEP_ENVIRONMENT || "production" });

// Step 1: Create an Agent
async function createAgent() {
  const agent = await client.agents.create({
    name: "Storytelling Agent",
    model: "claude-3.5-sonnet",
    about: "You are a creative storyteller that crafts engaging stories on a myriad of topics.",
  });
  return agent;
}

// Step 2: Create a Task that generates a story and comic strip
const taskYaml = `
name: Storyteller
description: Create a story based on an idea.

tools:
  - name: research_wikipedia
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
          Based on the idea '{{_.idea}}', generate a list of 5 plot ideas. Go crazy and be as creative as possible. Return your output as a list of long strings inside \`\`\`yaml tags at the end of your response.
    unwrap: true

  - evaluate:
      plot_ideas: load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())

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
          Return your output as a yaml list inside \`\`\`yaml tags at the end of your response.
    unwrap: true
    settings:
      model: gpt-4o-mini
      temperature: 0.7

  - evaluate:
      research_queries: load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())

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
          Then finally write the plot as a yaml object inside \`\`\`yaml tags at the end of your response. The yaml object should have the following structure:

          \`\`\`yaml
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
            - "<string>"\`\`\`

          Make sure the yaml is valid and the characters and scenes are not empty. Also take care of semicolons and other gotchas of writing yaml.
    unwrap: true

  - evaluate:
      plot: "load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())"
`;

async function createTask(agentId) {
  const task = await client.tasks.create(
    agentId,
    yaml.parse(taskYaml)
  );
  return task;
}

// Step 3: Execute the Task
async function executeTask(taskId) {
  const execution = await client.executions.create(taskId, {
    input: { idea: "A cat who learns to fly" }
  });

  // 🎉 Watch as the story and comic panels are generated
  while (true) {
    const result = await client.executions.get(execution.id);
    console.log(result.status, result.output);

    if (result.status === 'succeeded' || result.status === 'failed') {
      // 📦 Once the execution is finished, retrieve the results
      if (result.status === "succeeded") {
        console.log(result.output);
      } else {
        throw new Error(result.error);
      }
      break;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));
  }
}

// Main function to run the example
async function main() {
  try {
    const agent = await createAgent();
    const task = await createTask(agent.id);
    await executeTask(task.id);
  } catch (error) {
    console.error("An error occurred:", error);
  }
}

main().then(() => console.log("Done")).catch(console.error);
