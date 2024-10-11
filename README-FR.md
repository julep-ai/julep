<sup>English | [中文翻译](https://github.com/julep-ai/julep/blob/dev/README-CN.md) | [日本語翻訳](https://github.com/julep-ai/julep/blob/dev/README-JP.md)</sup><div align="center">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=API%20for%20AI%20agents%20and%20multi-step%20tasks&forks=1&name=1&owner=1&pattern=Solid&stargazers=1&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&theme=Auto" alt="julep" width="640" height="320" />
</div>
<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow"><strong>Explore Docs</strong></a>
  ·
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
  ·
  <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
  ·
  <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
</p>
<p align="center">
    <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License"></a>
</p>
[!NOTE]
👨‍💻 Here for the devfest.ai event? Join our [Discord](https://discord.com/invite/JTSBGRZrzj) and check out the details below.<details>
<summary><b>🌟 Contributors and DevFest.AI Participants</b> (Click to expand)</summary>
🌟 Appel aux contributeurs !Nous sommes ravis d'accueillir de nouveaux contributeurs au projet Julep ! Nous avons créé plusieurs « bons premiers numéros » pour vous aider à démarrer. Voici comment vous pouvez contribuer :Check out our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.Browse our [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to find a task that interests you.If you have any questions or need help, don't hesitate to reach out on our [Discord](https://discord.com/invite/JTSBGRZrzj) channel.Vos contributions, grandes ou petites, nous sont précieuses. Construisons ensemble quelque chose d'extraordinaire ! 🚀🎉 DevFest.AI Octobre 2024Des nouvelles passionnantes ! Nous participons au DevFest.AI tout au long du mois d'octobre 2024 ! 🗓️Contribuez à Julep pendant cet événement et obtenez une chance de gagner de superbes produits et cadeaux Julep ! 🎁Rejoignez les développeurs du monde entier en contribuant aux référentiels d'IA et en participant à des événements incroyables.Un grand merci à DevFest.AI pour l'organisation de cette fantastique initiative ![!TIP]
Ready to join the fun? **[Tweet that you are participating](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)** and let's get coding! 🖥️[!NOTE]
Get your API key [here](https://dashboard-dev.julep.ai).While we are in beta, you can also reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get rate limits lifted on your API key.![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)</details>
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<details>
<summary><h3>📖 Table of Contents</h3></summary>

- [Optional: Define the input schema for the task](#optional-define-the-input-schema-for-the-task)
- [Define the tools that the agent can use](#define-the-tools-that-the-agent-can-use)
- [Special variables:](#special-variables)
- [- inputs: for accessing the input to the task](#--inputs-for-accessing-the-input-to-the-task)
- [- outputs: for accessing the output of previous steps](#--outputs-for-accessing-the-output-of-previous-steps)
- [- _: for accessing the output of the previous step](#--_-for-accessing-the-output-of-the-previous-step)
- [Define the main workflow](#define-the-main-workflow)
- [Evaluate the search queries using a simple python expression](#evaluate-the-search-queries-using-a-simple-python-expression)
- [Run the web search in parallel for each query](#run-the-web-search-in-parallel-for-each-query)
- [Collect the results from the web search](#collect-the-results-from-the-web-search)
- [Summarize the results](#summarize-the-results)
- [Send the summary to Discord](#send-the-summary-to-discord)
- [🛠️ Add an image generation tool (DALL·E) to the agent](#-add-an-image-generation-tool-dall%C2%B7e-to-the-agent)
- [Create a task that takes an idea and creates a story and a 4-panel comic strip](#create-a-task-that-takes-an-idea-and-creates-a-story-and-a-4-panel-comic-strip)
- [Step 1: Generate a story and outline into 4 panels](#step-1-generate-a-story-and-outline-into-4-panels)
- [Step 2: Extract thedescriptions des panneaux et histoireevaluate:](#step-2-extract-thedescriptions-des-panneaux-et-histoireevaluate)
    - [Step 3: Execute the Task](#step-3-execute-the-task)

</details>
<!-- END doctoc generated TOC please keep comment here to allow auto update -->
IntroductionJulep est une plateforme permettant de créer des agents IA qui se souviennent des interactions passées et peuvent effectuer des tâches complexes. Elle offre une mémoire à long terme et gère des processus en plusieurs étapes.Julep permet la création de tâches en plusieurs étapes intégrant la prise de décision, les boucles, le traitement parallèle et l'intégration avec de nombreux outils et API externes.Alors que de nombreuses applications d’IA se limitent à des chaînes simples et linéaires d’invites et d’appels d’API avec une ramification minimale, Julep est conçu pour gérer des scénarios plus complexes.Il prend en charge :Des processus complexes en plusieurs étapesPrise de décision dynamiqueExécution parallèle[!TIP]
Imagine you want to build an AI agent that can do more than just answer simple questions—it needs to handle complex tasks, remember past interactions, and maybe even use other tools or APIs. That's where Julep comes in.Exemple rapideImaginez un agent d’IA de recherche capable d’effectuer les opérations suivantes :Prenez un sujet,Proposez 100 requêtes de recherche pour ce sujet,Effectuez ces recherches sur le Web en parallèle,Résumer les résultats,Envoyez le résumé sur DiscordIn Julep, this would be a single task under <b>80 lines of code</b> and run <b>fully managed</b> all on its own. All of the steps are executed on Julep's own servers and you don't need to lift a finger. Here's a working example:name: Research Agent

# Optional: Define the input schema for the task
input_schema:
  type: object
  properties:
    topic:
      type: string
      description: The main topic to research

# Define the tools that the agent can use
tools:
- name: web_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: "YOUR_BRAVE_API_KEY"

- name: discord_webhook
  type: api_call
  api_call:
    url: "YOUR_DISCORD_WEBHOOK_URL"
    method: POST
    headers:
      Content-Type: application/json

# Special variables:
# - inputs: for accessing the input to the task
# - outputs: for accessing the output of previous steps
# - _: for accessing the output of the previous step

# Define the main workflow
main:
- prompt:
    - role: system
      content: >-
        You are a research assistant.
        Generate 100 diverse search queries related to the topic:
        {{inputs[0].topic}}

        Write one query per line.
  unwrap: true

# Evaluate the search queries using a simple python expression
- evaluate:
    search_queries: "_.split('\n')"

# Run the web search in parallel for each query
- over: "_.search_queries"
  map:
    tool: web_search
    arguments:
      query: "_"
  parallelism: 100

# Collect the results from the web search
- evaluate:
    results: "'\n'.join([item.result for item in _])"

# Summarize the results
- prompt:
    - role: system
      content: >
        You are a research summarizer. Create a comprehensive summary of the following research results on the topic {{inputs[0].topic}}.
        The summary should be well-structured, informative, and highlight key findings and insights:
        {{_.results}}
  unwrap: true

# Send the summary to Discord
- tool: discord_webhook
  arguments:
    content: >
      **Research Summary for {{inputs[0].topic}}**

      {{_}}
[!TIP]
Julep is really useful when you want to build AI agents that can maintain context and state over long-term interactions. It's great for designing complex, multi-step workflows and integrating various tools and APIs directly into your agent's processes.Dans cet exemple, Julep gérera automatiquement les exécutions parallèles, réessayera les étapes ayant échoué, renverra les requêtes API et maintiendra les tâches en cours d'exécution de manière fiable jusqu'à leur achèvement.Caractéristiques principales🧠 **Persistent AI Agents**: Remember context and information over long-term interactions.💾 **Stateful Sessions**: Keep track of past interactions for personalized responses.🔄 **Multi-Step Tasks**: Build complex, multi-step processes with loops and decision-making.⏳ **Task Management**: Handle long-running tasks that can run indefinitely.🛠️ **Built-in Tools**: Use built-in tools and external APIs in your tasks.🔧 **Self-Healing**: Julep will automatically retry failed steps, resend messages, and generally keep your tasks running smoothly.📚 **RAG**: Use Julep's document store to build a system for retrieving et en utilisant vos propres données.Julep est idéal pour les applications qui nécessitent des cas d’utilisation de l’IA au-delà des simples modèles de réponse rapide.Pourquoi Julep vs. LangChain ?Différents cas d'utilisationConsidérez LangChain et Julep comme des outils avec des objectifs différents au sein de la pile de développement de l’IA.LangChain est idéal pour créer des séquences d'invites et gérer les interactions avec les modèles d'IA. Il dispose d'un vaste écosystème avec de nombreuses intégrations prédéfinies, ce qui le rend pratique si vous souhaitez mettre en place quelque chose rapidement. LangChain s'adapte bien aux cas d'utilisation simples qui impliquent une chaîne linéaire d'invites et d'appels d'API.Julep, en revanche, s'intéresse davantage à la création d'agents d'IA persistants capables de mémoriser des éléments au cours d'interactions à long terme. Il est particulièrement efficace lorsque vous avez besoin de tâches complexes impliquant plusieurs étapes, une prise de décision et une intégration avec divers outils ou API directement dans le processus de l'agent. Il est conçu dès le départ pour gérer les sessions persistantes et les tâches complexes.Utilisez Julep si vous imaginez créer un assistant IA complexe qui doit :Suivez les interactions des utilisateurs sur plusieurs jours ou semaines.Exécutez des tâches planifiées, comme l’envoi de résumés quotidiens ou la surveillance de sources de données.Prendre des décisions basées sur des interactions antérieures ou des données stockées.Interagir avec plusieurs services externes dans le cadre de sa tâche.Ensuite, Julep fournit l’infrastructure pour prendre en charge tout cela sans que vous ayez à le construire à partir de zéro.Différents facteurs de formeJulep is a **platform** that includes a language for describing tasks, a server for running those tasks, and an SDK for interacting with the platform. To build something with Julep, you write a description of the task in `YAML`, and then run the task in the cloud.Julep est conçu pour les tâches lourdes, en plusieurs étapes et de longue durée, et il n'y a aucune limite à la complexité de la tâche.LangChain is a **library** that includes a few tools and a framework for building linear chains of prompts and tools. To build something with LangChain, you typically write Python code that configures and runs the model chains you want to use.LangChain pourrait être suffisant et plus rapide à mettre en œuvre pour les cas d'utilisation simples impliquant une chaîne linéaire d'invites et d'appels d'API.En résuméUtilisez LangChain lorsque vous devez gérer les interactions des modèles d’IA et les séquences d’invite dans un contexte sans état ou à court terme.Choisissez Julep lorsque vous avez besoin d'un framework robuste pour les agents avec état avec des capacités de tâches avancées, des sessions persistantes et une gestion de tâches complexes.InstallationTo get started with Julep, install it using [npm](https://www.npmjs.com/package/@julep/sdk) or [pip](https://pypi.org/project/julep/):npm install @julep/sdk
oupip install julep
[!NOTE]
Get your API key [here](https://dashboard-dev.julep.ai).While we are in beta, you can also reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get rate limits lifted on your API key.[!TIP]
💻 Are you a _show me the code!™_ kind of person? We have created a ton of cookbooks for you to get started with. **Check out the [cookbooks](https://github.com/julep-ai/julep/tree/dev/cookbooks)** to browse through examples.💡 There's also lots of ideas that you can build on top of Julep. **Check out the [list of ideas](https://github.com/julep-ai/julep/tree/dev/cookbooks/IDEAS.md)** to get some inspiration.Démarrage rapide de Python 🐍Étape 1 : Créer un agentimport yaml
from julep import Julep # or AsyncJulep

client = Julep(api_key="your_julep_api_key")

agent = client.agents.create(
    name="Storytelling Agent",
    model="gpt-4o",
    about="You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
)

# 🛠️ Add an image generation tool (DALL·E) to the agent
client.agents.tools.create(
    agent_id=agent.id,
    name="image_generator",
    description="Use this tool to generate images based on descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "your_openai_api_key",
        },
    },
)
Étape 2 : Créer une tâche qui génère une histoire et une bande dessinéeDéfinissons une tâche en plusieurs étapes pour créer une histoire et générer une bande dessinée à panneaux basée sur une idée d'entrée :# 📋 Task
# Create a task that takes an idea and creates a story and a 4-panel comic strip
task_yaml = """
name: Story and Comic Creator
description: Create a story based on an idea and generate a 4-panel comic strip illustrating the story.

main:
  # Step 1: Generate a story and outline into 4 panels
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip.
          Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story.
    unwrap: true

  # Step 2: Extract thedescriptions des panneaux et histoireevaluate:
  story: _.split('1. ')[0].strip()
  panels: re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)Étape 3 : Générer des images pour chaque panneau à l'aide de l'outil de génération d'imagesforeach:
  in: _.panels
  do:
    tool: image_generator
    arguments:
      description: _Étape 4 : Générez un titre accrocheur pour l'histoirerapide:role: system
content: You are {{agent.name}}. {{agent.about}}role: user
content: >
  Based on the story below, generate a catchy title.Story: {{outputs[1].story}}
unwrap: trueÉtape 5 : Renvoyer l'histoire, les images générées et le titrereturn:
  title: outputs[3]
  story: outputs[1].story
  comic_panels: "[output.image.url for output in outputs[2]]"
"""task = client.tasks.create(
    agent_id=agent.id,
    **yaml.safe_load(task_yaml)
)
### Step 3: Execute the Task

```python
# 🚀 Execute the task with an input idea
execution = client.executions.create(
    task_id=task.id,
    input={"idea": "A cat who learns to fly"}
)

# 🎉 Watch as the story and comic panels are generated
for transition in client.executions.transitions.stream(execution_id=execution.id):
    print(transition)

# 📦 Once the execution is finished, retrieve the results
result = client.executions.get(execution_id=execution.id)
Étape 4 : Discutez avec l'agentDémarrez une session de chat interactive avec l'agent :session = client.sessions.create(agent_id=agent.id)

# 💬 Send messages to the agent
while (message := input("Enter a message: ")) != "quit":
    response = client.sessions.chat(
        session_id=session.id,
        message=message,
    )

    print(response)
[!TIP]
You can find the full python example [here](example.py).Démarrage rapide de Node.js 🟩Étape 1 : Créer un agentimport { Julep } from '@julep/sdk';
import yaml from 'js-yaml';

const client = new Julep({ apiKey: 'your_julep_api_key' });

async function createAgent() {
  const agent = await client.agents.create({
    name: "Storytelling Agent",
    model: "gpt-4",
    about: "You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
  });

  // 🛠️ Add an image generation tool (DALL·E) to the agent
  await client.agents.tools.create(agent.id, {
    name: "image_generator",
    description: "Use this tool to generate images based on descriptions.",
    integration: {
      provider: "dalle",
      method: "generate_image",
      setup: {
        api_key: "your_openai_api_key",
      },
    },
  });

  return agent;
}
Étape 2 : Créer une tâche qui génère une histoire et une bande dessinéeconst taskYaml = `
name: Story and Comic Creator
description: Create a story based on an idea and generate a 4-panel comic strip illustrating the story.

main:
  # Step 1: Generate a story and outline into 4 panels
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip.
          Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story.
    unwrap: true

  # Step 2: Extract the panel descriptions and story
  - evaluate:
      story: _.split('1. ')[0].trim()
      panels: _.match(/\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)/g)

  # Step 3: Generate images for each panel using the image generator tool
  - foreach:
      in: _.panels
      do:
        tool: image_generator
        arguments:
          description: _

  # Step 4: Generate a catchy title for the story
  - prompt:
      - role: system
        content: You are {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Based on the story below, generate a catchy title.

          Story: {{outputs[1].story}}
    unwrap: true

  # Step 5: Return the story, the generated images, and the title
  - return:
      title: outputs[3]
      story: outputs[1].story
      comic_panels: outputs[2].map(output => output.image.url)
`;

async function createTask(agent) {
  const task = await client.tasks.create(agent.id, yaml.load(taskYaml));
  return task;
}
Étape 3 : Exécuter la tâcheasync function executeTask(task) {
  const execution = await client.executions.create(task.id, {
    input: { idea: "A cat who learns to fly" }
  });

  // 🎉 Watch as the story and comic panels are generated
  for await (const transition of client.executions.transitions.stream(execution.id)) {
    console.log(transition);
  }

  // 📦 Once the execution is finished, retrieve the results
  const result = await client.executions.get(execution.id);
  return result;
}
Étape 4 : Discutez avec l'agentasync function chatWithAgent(agent) {
  const session = await client.sessions.create({ agent_id: agent.id });

  // 💬Send messages to the agent
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });const chat = async () => {
    rl.question("Enter a message (or 'quit' to exit): ", async (message) => {
      if (message.toLowerCase() === 'quit') {
        rl.close();
        return;
      }  const response = await client.sessions.chat(session.id, { message });
  console.log(response);
  chat();
});
};chat();
}// Run the example
async function runExample() {
  const agent = await createAgent();
  const task = await createTask(agent);
  const result = await executeTask(task);
  console.log("Task Result:", result);
  await chatWithAgent(agent);
}runExample().catch(console.error);
> [!TIP]
> You can find the full Node.js example [here](example.js).

## Components

Julep is made up of the following components:

- **Julep Platform**: The Julep platform is a cloud service that runs your workflows. It includes a language for describing workflows, a server for running those workflows, and an SDK for interacting with the platform.
- **Julep SDKs**: Julep SDKs are a set of libraries for building workflows. There are SDKs for Python and JavaScript, with more on the way.
- **Julep API**: The Julep API is a RESTful API that you can use to interact with the Julep platform.

### Mental Model

<div align="center">
  <img src="https://github.com/user-attachments/assets/38420b5d-9342-4c8d-bae9-b47c28ae45af" height="360" />
</div>

Think of Julep as a platform that combines both client-side and server-side components to help you build advanced AI agents. Here's how to visualize it:

1. **Your Application Code:**
   - You use the Julep SDK in your application to define agents, tasks, and workflows.
   - The SDK provides functions and classes that make it easy to set up and manage these components.

2. **Julep Backend Service:**
   - The SDK communicates with the Julep backend over the network.
   - The backend handles execution of tasks, maintains session state, stores documents, and orchestrates workflows.

3. **Integration with Tools and APIs:**
   - Within your workflows, you can integrate external tools and services.
   - The backend facilitates these integrations, so your agents can, for example, perform web searches, access databases, or call third-party APIs.

In simpler terms:
- Julep is a platform for building stateful AI agents.
- You use the SDK (like a toolkit) in your code to define what your agents do.
- The backend service (which you can think of as the engine) runs these definitions, manages state, and handles complexity.

## Concepts

Julep is built on several key technical components that work together to create powerful AI workflows:

```mermaid
graph TD
    User[User] ==> Session[Session]
    Session --> Agent[Agent]
    Agent --> Tasks[Tasks]
    Agent --> LLM[Large Language Model]
    Tasks --> Tools[Tools]
    Agent --> Documents[Documents]
    Documents --> VectorDB[Vector Database]
    Tasks --> Executions[Executions]

    classDef client fill:#9ff,stroke:#333,stroke-width:1px;
    class User client;

    classDef core fill:#f9f,stroke:#333,stroke-width:2px;
    class Agent,Tasks,Session core;
**Agents**: AI-powered entities backed by large language models (LLMs) that execute tasks and interact with users.**Users**: Entities that interact with agents through sessions.**Sessions**: Stateful interactions between agents and users, maintaining context across multiple exchanges.**Tasks**: Multi-step, programmatic workflows that agents can execute, including various types of steps like prompts, tool calls, and conditional logic.**Tools**: Integrations that extend an agent's capabilities, including user-defined functions, system tools, or third-party API integrations.**Documents**: Text or data objects associated with agents or users, vectorized and stored for semantic search and retrieval.**Executions**: Instances of tasks that have been initiated with specific inputs, with their own lifecycle and state machine.For a more detailed explanation of these concepts and their interactions, please refer to our [Concepts Documentation](https://github.com/julep-ai/julep/blob/dev/docs/julep-concepts.md).Comprendre les tâchesLes tâches sont au cœur du système de workflow de Julep. Elles vous permettent de définir des workflows IA complexes en plusieurs étapes que vos agents peuvent exécuter. Voici un bref aperçu des composants des tâches :**Name and Description**: Each task has a unique name and description for easy identification.**Main Steps**: The core of a task, defining the sequence of actions to be performed.**Tools**: Optional integrations that extend the capabilities of your agent during task execution.Types d'étapes du flux de travailLes tâches dans Julep peuvent inclure différents types d'étapes, ce qui vous permet de créer des flux de travail complexes et puissants. Voici un aperçu des types d'étapes disponibles, organisés par catégorie :Étapes courantes**Prompt**: Sendun message au modèle d'IA et recevoir une réponse.- prompt: "Analyze the following data: {{data}}"
**Tool Call**: Execute an integrated tool or API.- tool: web_search
  arguments:
    query: "Latest AI developments"
**Evaluate**: Perform calculations or manipulate data.- evaluate:
    average_score: "sum(scores) / len(scores)"
**Wait for Input**: Pause workflow until input is received.- wait_for_input:
    info:
      message: "Please provide additional information."
**Log**: Log a specified value or message.- log: "Processing completed for item {{item_id}}"
Étapes clés-valeurs**Get**: Retrieve a value from a key-value store.- get: "user_preference"
**Set**: Assign a value to a key in a key-value store.- set:
    user_preference: "dark_mode"
Étapes d'itération**Foreach**: Iterate over a collection and perform steps for each item.- foreach:
    in: "data_list"
    do:
      - log: "Processing item {{_}}"
**Map-Reduce**: Map over a collection and reduce the results.- map_reduce:
    over: "numbers"
    map:
      - evaluate:
          squared: "_ ** 2"
    reduce: "sum(results)"
**Parallel**: Run multiple steps in parallel.- parallel:
    - tool: web_search
      arguments:
        query: "AI news"
    - tool: weather_check
      arguments:
        location: "New York"
Étapes conditionnelles**If-Else**: Conditional execution of steps.- if: "score > 0.8"
  then:
    - log: "High score achieved"
  else:
    - log: "Score needs improvement"
**Switch**: Execute steps based on multiple conditions.- switch:
    - case: "category == 'A'"
      then:
        - log: "Category A processing"
    - case: "category == 'B'"
      then:
        - log: "Category B processing"
    - case: "_"  # Default case
      then:
        - log: "Unknown category"
Autre flux de contrôle**Sleep**: Pause the workflow for a specified duration.- sleep:
    seconds: 30
**Return**: Return a value from the workflow.- return:
    result: "Task completed successfully"
**Yield**: Run a subworkflow and await its completion.- yield:
    workflow: "data_processing_subflow"
    arguments:
      input_data: "{{raw_data}}"
**Error**: Handle errors by specifying an error message.- error: "Invalid input provided"
Chaque type d'étape remplit un objectif spécifique dans la création de workflows d'IA sophistiqués. Cette catégorisation permet de comprendre les différents flux de contrôle et opérations disponibles dans les tâches Julep.Fonctionnalités avancéesJulep propose une gamme de fonctionnalités avancées pour améliorer vos flux de travail d'IA :Ajout d'outils aux agentsÉtendez les capacités de votre agent en intégrant des outils et des API externes :client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="Search the web for information.",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {"api_key": "your_brave_api_key"},
    },
)
Gestion des sessions et des utilisateursJulep fournit une gestion de session robuste pour les interactions persistantes :session = client.sessions.create(
    agent_id=agent.id,
    user_id=user.id,
    context_overflow="adaptive"
)

# Continue conversation in the same session
response = client.sessions.chat(
    session_id=session.id,
    messages=[
      {
        "role": "user",
        "content": "Follow up on the previous conversation."
      }
    ]
)
Intégration et recherche de documentsGérez et recherchez facilement des documents pour vos agents :# Upload a document
document = client.agents.docs.create(
    title="AI advancements",
    content="AI is changing the world...",
    metadata={"category": "research_paper"}
)

# Search documents
results = client.agents.docs.search(
    text="AI advancements",
    metadata_filter={"category": "research_paper"}
)
For more advanced features and detailed usage, please refer to our [Advanced Features Documentation](https://docs.julep.ai/advanced-features).IntégrationsJulep prend en charge diverses intégrations qui étendent les capacités de vos agents IA. Voici une liste des intégrations disponibles et de leurs arguments pris en charge :Recherche courageusesetup:
  api_key: string  # The API key for Brave Search

arguments:
  query: string  # The search query for searching with Brave

output:
  result: string  # The result of the Brave Search
Base de navigateursetup:
  api_key: string       # The API key for BrowserBase
  project_id: string    # The project ID for BrowserBase
  session_id: string    # (Optional) The session ID for BrowserBasearguments:
  urls: list[string]    # The URLs for loading with BrowserBaseoutput:
  documents: list       # The documents loaded from the URLs
### Email

```yaml
setup:
  host: string      # The host of the email server
  port: integer     # The port of the email server
  user: string      # The username of the email server
  password: string  # The password of the email server

arguments:
  to: string        # The email address to send the email to
  from: string      # The email address to send the email from
  subject: string   # The subject of the email
  body: string      # The body of the email

output:
  success: boolean  # Whether the email was sent successfully
Araignéesetup:
  spider_api_key: string  # The API key for Spider

arguments:
  url: string             # The URL for which to fetch data
  mode: string            # The type of crawlers (default: "scrape")
  params: dict            # (Optional) The parameters for the Spider API

output:
  documents: list         # The documents returned from the spider
Météosetup:
  openweathermap_api_key: string  # The API key for OpenWeatherMap

arguments:
  location: string                # The location for which to fetch weather data

output:
  result: string                  # The weather data for the specified location
Wikipédiaarguments:
  query: string           # The search query string
  load_max_docs: integer  # Maximum number of documents to load (default: 2)

output:
  documents: list         # The documents returned from the Wikipedia search
These integrations can be used within your tasks to extend the capabilities of your AI agents. For more detailed information on how to use these integrations in your workflows, please refer to our [Integrations Documentation](https://docs.julep.ai/integrations).Référence SDK[Node.js SDK](https://github.com/julep-ai/node-sdk/blob/main/api.md)[Python SDK](https://github.com/julep-ai/python-sdk/blob/main/api.md)Référence APIExplorez notre documentation API complète pour en savoir plus sur les agents, les tâches et les exécutions :[Agents API](https://api.julep.ai/api/docs#tag/agents)[Tasks API](https://api.julep.ai/api/docs#tag/tasks)[Executions API](https://api.julep.ai/api/docs#tag/executions)->> Test <<-
A simple update to text the translation github action