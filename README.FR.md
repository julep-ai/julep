<!--
****************
** Directives **
****************

**Approche choisie :**

Le **Guide de démarrage rapide axé sur le README** est l'option la plus prometteuse pour optimiser le temps avant le premier workflow. Cela permet aux développeurs d'acquérir rapidement une expérience pratique, ce qui est essentiel pour l'engagement et la compréhension.

**Remarques :**

*   **Exemples de code :** Assurez-vous que tous les extraits de code soient faciles à comprendre et prêts à être copiés-collés.
*   **Simplicité :** Gardez les explications concises afin de rester concentré sur le démarrage rapide.
*   **Liens :** Incluez des hyperliens vers des sections détaillées de la documentation pour les utilisateurs qui souhaitent approfondir.
*   **Visuels :** Pensez à ajouter des diagrammes ou des images pour illustrer les concepts si possible.
*   **Ton :** Maintenez un ton encourageant et utile tout au long du README.
-->

<sup>[English](README.md) | [中文翻译](/README-CN.md)</sup>

<div align="center">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=API%20for%20building%20multi-step%20agent%20workflows.&font=Raleway&forks=1&name=1&owner=1&pattern=Solid&stargazers=1&theme=Light" alt="julep" width="640" height="320"/>
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
    <a href="https://www.npmjs.com/package/@julep/sdk">
        <img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version">
    </a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep">
        <img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version">
    </a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai">
        <img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version">
    </a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/">
        <img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License">
    </a>
</p>

*****

## 🌟 Call for Contributors!

We're excited to welcome new contributors to the Julep project! We've created several "good first issues" to help you get started. Here's how you can contribute:

1. Check out our [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute.
2. Browse our [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) to find a task that interests you.
3. If you have any questions or need help, don't hesitate to reach out on our [Discord](https://discord.com/invite/JTSBGRZrzj) channel.

Your contributions, big or small, are valuable to us. Let's build something amazing together! 🚀

### 🎉 DevFest.AI October 2024

Exciting news! We're participating in DevFest.AI throughout October 2024! 🗓️

- Contribute to Julep during this event and get a chance to win awesome Julep merch and swag! 🎁
- Join developers from around the world in contributing to AI repositories and participating in amazing events.
- A big thank you to DevFest.AI for organizing this fantastic initiative!

> [!TIP]
> Ready to join the fun? **[Tweet to start participating](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)** and let's get coding! 🖥️

![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)


*****

## 🎉🚀 **Exciting News: Julep 1.0 Alpha Release!** 🚀🎉

We're thrilled to announce the **alpha** release of <u>Julep 1.0</u>! 🥳

🌟 **What's New:**
- Enhanced workflow capabilities
- Improved agent persistence
- Tons of in-built tool integrations (like dalle, google search, sendgrid, etc.)
- Streamlined API

🧪 Try it out and help shape the future of AI workflows!

> [!NOTE]
> While we are in beta, you can reach out on [Discord](https://discord.com/invite/JTSBGRZrzj) to get your API key.

> [!TIP]
> 🐛 Found a bug? Have a suggestion? We'd love to hear from you!
>   Join our [Discord](https://discord.com/invite/JTSBGRZrzj) or open an [issue](https://github.com/julep-ai/julep/issues).

Stay tuned for more updates as we approach our stable release! 📢

*****

## Introduction

Julep is an open-source platform for creating persistent AI agents with customizable workflows. It provides tools to develop, manage, and deploy AI-driven applications, focusing on flexibility and ease of use.

With Julep, you can:
- Quickly develop AI agents that retain context and state across interactions
- Design and execute sophisticated workflows tailored to your AI agents
- Seamlessly integrate various tools and APIs into your AI workflows
- Effortlessly manage persistent sessions and user interactions

Whether you're developing a chatbot, automating tasks, or building a complex AI assistant, Julep provides the flexibility and features you need to turn your ideas into reality swiftly and efficiently.

<!-- TODO: Add a screencast -->

<details>
<summary>Here's a quick python example:</summary>

<!-- TODO: Add a gif that shows the execution of the task in the README -->

<pre><code class="language-python">
from julep import Julep, AsyncJulep

# 🔑 Initialize the Julep client
#     Or alternatively, use AsyncJulep for async operations
client = Julep(api_key="your_api_key")

##################
## 🤖 Agent 🤖 ##
##################

# Create a research agent
agent = client.agents.create(
    name="Research Agent",
    model="claude-3.5-sonnet",
    about="You are a research agent designed to handle research inquiries.",
)

# 🔍 Add a web search tool to the agent
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",  # Should be python valid variable name
    description="Use this tool to research inquiries.",
    integration={
        "provider": "brave",
        "method": "search",
        "setup": {
            "api_key": "your_brave_api_key",
        },
    },
)

#################
## 💬 Chat 💬 ##
#################

# Start an interactive chat session with the agent
session = client.sessions.create(
    agent_id=agent.id,
    context_overflow="adaptive",  # 🧠 Julep will dynamically compute the context window if needed
)

# 🔄 Chat loop
while (user_input := input("You: ")) != "exit":
    response = client.sessions.chat(
        session_id=session.id,
        message=user_input,
    )

    print("Agent: ", response.choices[0].message.content)


#################
## 📋 Task 📋 ##
#################

# Create a recurring research task for the agent
task = client.tasks.create(
    agent_id=agent.id,
    name="Research Task",
    description="Research the given topic every 24 hours.",
    #
    # 🛠️ Task specific tools
    tools=[
        {
            "name": "send_email",
            "description": "Send an email to the user with the results.",
            "api_call": {
                "method": "post",
                "url": "https://api.sendgrid.com/v3/mail/send",
                "headers": {"Authorization": "Bearer YOUR_SENDGRID_API_KEY"},
            },
        }
    ],
    #
    # 🔢 Task main steps
    main=[
        #
        # Step 1: Research the topic
        {
            # `_` (underscore) variable refers to the previous step's output
            # Here, it points to the topic input from the user
            "prompt": "Look up topic '{{_.topic}}' and summarize the results.",
            "tools": [{"ref": {"name": "web_search"}}],  # 🔍 Use the web search tool from the agent
            "unwrap": True,
        },
        #
        # Step 2: Send email with research results
        {
            "tool": "send_email",
            "arguments": {
                "subject": "Research Results",
                "body": "'Here are the research results for today: ' + _.content",
                "to": "inputs[0].email",  # Reference the email from the user's input
            },
        },
        #
        # Step 3: Wait for 24 hours before repeating
        {"sleep": "24 * 60 * 60"},
    ],
)

# 🚀 Start the recurring task
client.executions.create(task_id=task.id, input={"topic": "Python"})

# 🔁 This will run the task every 24 hours,
#    research for the topic "Python", and
#    send the results to the user's email
</code></pre>
</details>

## Features

Julep simplifies the process of building persistent AI agents with customizable workflows. Key features include:

- **Persistent AI Agents**: Create and manage AI agents that maintain context across interactions.
- **Customizable Workflows**: Design complex, multi-step AI workflows using Tasks.
- **Tool Integration**: Seamlessly integrate various tools and APIs into your AI workflows.
- **Document Management**: Efficiently manage and search through documents for your agents.
- **Session Management**: Handle persistent sessions for continuous interactions.
- **Flexible Execution**: Support for parallel processing, conditional logic, and error handling in workflows.

## Installation

To get started with Julep, install it using [npm](https://www.npmjs.com/package/@julep/sdk) or [pip](https://pypi.org/project/julep/):

```bash
npm install @julep/sdk
```

gold

```bash
pip install julep
```

> [!TIP]
> ~~Obtenez votre clé API [ici](https://app.julep.ai/api-keys).~~  
>  
> Pendant que nous sommes en version bêta, vous pouvez nous contacter sur [Discord](https://discord.com/invite/JTSBGRZrzj) pour obtenir votre clé API.

## Guide de démarrage rapide

### Étape 1 : Importez Julep

Tout d'abord, importez le SDK Julep dans votre projet :

```javascript
const Julep = require('@julep/sdk');
```

gold

```python
from julep import AsyncJulep
```

### Étape 2 : Initialiser l'Agent

Créez un nouvel agent avec des paramètres de base :

```javascript
const julep = new Julep({ apiKey: 'your-api-key' });

const agent = await julep.agents.create({
  name: 'ResearchAssistant',
  model: 'gpt-4-turbo',
  about: "You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
});
```

gold

```python
client = AsyncJulep(api_key="your_api_key")

agent = await client.agents.create(
    name="Storytelling Agent",
    model="gpt-4-turbo",
    about="You are a creative storytelling agent that can craft engaging stories and generate comic panels based on ideas.",
)
```

### Étape 3 : Discutez avec l'agent

Démarrez une session de chat interactive avec l'agent :

```javascript
const session = await julep.sessions.create({
  agentId: agent.id,
}); 

// Send messages to the agent
const response = await julep.sessions.chat({
  sessionId: session.id,
  message: 'Hello, can you tell me a story?',
});

console.log(response);
```

gold

```python
session = await client.sessions.create(agent_id=agent.id)

# Send messages to the agent
response = await client.sessions.chat(
    session_id=session.id,
    message="Hello, can you tell me a story?",
)

print(response)
```

### Étape 4 : Créer une tâche en plusieurs étapes

Définissons une tâche en plusieurs étapes pour créer une histoire et générer une bande dessinée en panneaux basée sur une idée d'entrée :


```python
# 🛠️ Add an image generation tool (DALL·E) to the agent
await client.agents.tools.create(
    agent_id=agent.id,
    name="image_generator",
    description="Use this tool to generate images based on descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "your_dalle_api_key",
        },
    },
)

# 📋 Task
# Create a task that takes an idea and creates a story and a 4-panel comic strip
task = await client.tasks.create(
    agent_id=agent.id,
    name="Story and Comic Creator",
    description="Create a story based on an idea and generate a 4-panel comic strip illustrating the story.",
    main=[
        # Step 1: Generate a story and outline into 4 panels
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "You are {{agent.name}}. {{agent.about}}"
                },
                {
                    "role": "user",
                    "content": (
                        "Based on the idea '{{_.idea}}', write a short story suitable for a 4-panel comic strip. "
                        "Provide the story and a numbered list of 4 brief descriptions for each panel illustrating key moments in the story."
                    ),
                },
            ],
            "unwrap": True,
        },
        # Step 2: Extract the panel descriptions and story
        {
            "evaluate": {
                "story": "_.split('1. ')[0].strip()",
                "panels": "re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)",
            }
        },
        # Step 3: Generate images for each panel using the image generator tool
        {
            "foreach": {
                "in": "_.panels",
                "do": {
                    "tool": "image_generator",
                    "arguments": {
                        "description": "_",
                    },
                },
            },
        },
        # Step 4: Generate a catchy title for the story
        {
            "prompt": [
                {
                    "role": "system",
                    "content": "You are {{agent.name}}. {{agent.about}}"
                },
                {
                    "role": "user",
                    "content": "Based on the story below, generate a catchy title.\n\nStory: {{outputs[1].story}}",
                },
            ],
            "unwrap": True,
        },
        # Step 5: Return the story, the generated images, and the title
        {
            "return": {
                "title": "outputs[3]",
                "story": "outputs[1].story",
                "comic_panels": "[output.image.url for output in outputs[2]]",
            }
        },
    ],
)
```

> [!ASTUCE]
> La version node.js de ceci est similaire.

### Étape 5 : Exécuter la tâche

```python
# 🚀 Execute the task with an input idea
execution = await client.executions.create(
    task_id=task.id,
    input={"idea": "A cat who learns to fly"}
)

# 🎉 Watch as the story and comic panels are generated
await client.executions.stream(execution_id=execution.id)
```

Cet exemple démontre comment créer un agent avec un outil personnalisé, définir une tâche complexe avec plusieurs étapes et l'exécuter pour générer une sortie créative.

<!-- TODO: Ajouter un gif qui montre l'exécution de la tâche dans le README -->

> [!ASTUCE]
> Vous pouvez trouver un autre exemple en node.js [ici](example.ts) ou un exemple en python [ici](example.py).

## Concepts

Julep est construit sur plusieurs composants techniques clés qui travaillent ensemble pour créer des flux de travail AI puissants :

### Agents
Des entités alimentées par l'IA soutenues par de grands modèles de langage (LLMs) qui exécutent des tâches et interagissent avec les utilisateurs. Les agents sont les unités fonctionnelles de base de Julep.

```mermaid
graph TD
    Agent[Agent] --> LLM[Large Language Model]
    Agent --> Tasks[Tasks]
    Agent --> Users[Users]
    Tasks --> Tools[Tools]
```

### Utilisateurs
Entités qui interagissent avec des agents. Les utilisateurs peuvent être associés à des sessions et avoir leurs propres métadonnées, permettant des interactions personnalisées.

```mermaid
graph LR
    User[User] --> Sessions[Sessions]
    Sessions --> Agents[Agents]
    Sessions --> Metadata[Metadata]
```

### Sessions
Interactions avec état entre agents et utilisateurs. Les sessions maintiennent le contexte à travers plusieurs échanges et peuvent être configurées pour différents comportements, y compris la gestion du contexte et le traitement des débordements.

```mermaid
graph LR
    Sessions[Sessions] --> Agents[Agents]
    Sessions --> Users[Users]
    Sessions --> ContextManagement[Context Management]
    Sessions --> OverflowHandling[Overflow Handling]
```

### Tâches
Flux de travail programmatique à plusieurs étapes que les agents peuvent exécuter. Les tâches définissent des opérations complexes et peuvent inclure divers types d'étapes, telles que des invites, des appels d'outils et une logique conditionnelle.

```mermaid
graph TD
    Tasks[Tasks] --> Steps[Workflow Steps]
    Steps --> Prompt[Prompt]
    Steps --> ToolCalls[Tool Calls]
    Steps --> ConditionalLogic[Conditional Logic]
```
### Outils
Intégrations qui étendent les capacités d'un agent. Les outils peuvent être des fonctions définies par l'utilisateur, des outils système ou des intégrations d'API tierces. Ils permettent aux agents d'effectuer des actions au-delà de la génération de texte.

```mermaid
graph LR
    Tools[Tools] --> UserDefinedFunctions[User-Defined Functions]
    Tools --> SystemTools[System Tools]
    Tools --> ThirdPartyAPIs[Third-Party APIs]
```

### Documents
Objets texte ou données qui peuvent être associés à des agents ou à des utilisateurs. Les documents sont vectorisés et stockés dans une base de données vectorielle, permettant une recherche et une récupération sémantiques lors des interactions avec les agents.

```mermaid
graph LR
    Documents[Documents] --> VectorDatabase[Vector Database]
    Documents --> SemanticSearch[Semantic Search]
    Documents --> AgentsOrUsers[Agents or Users]
```

### Exécutions
Instances de tâches qui ont été initiées avec des entrées spécifiques. Les exécutions ont leur propre cycle de vie et machine d'état, permettant la surveillance, la gestion et la reprise de processus de longue durée.

```mermaid
graph LR
    Executions[Executions] --> Tasks[Tasks]
    Executions --> Lifecycle[Lifecycle]
    Executions --> Monitoring[Monitoring]
    Executions --> Management[Management]
    Executions --> Resumption[Resumption]
```

Pour une explication plus détaillée de ces concepts et de leurs interactions, veuillez vous référer à notre [Documentation sur les Concepts](https://github.com/julep-ai/julep/blob/dev/docs/julep-concepts.md).

## Comprendre les Tâches

Les tâches sont le cœur du système de flux de travail de Julep. Elles vous permettent de définir des flux de travail IA complexes et à plusieurs étapes que vos agents peuvent exécuter. Voici un bref aperçu des composants des tâches :

- **Nom et Description** : Chaque tâche a un nom et une description uniques pour une identification facile.
- **Étapes Principales** : Le cœur d'une tâche, définissant la séquence des actions à effectuer.
- **Outils** : Intégrations facultatives qui étendent les capacités de votre agent lors de l'exécution de la tâche.

### Types d'Étapes de Flux de Travail

Les tâches dans Julep peuvent inclure divers types d'étapes :

1. **Invite** : Envoyer un message au modèle IA et recevoir une réponse.
   ```python
   {"prompt": "Analyze the following data: {{data}}"}
   ```
2. **Appel d'Outil** : Exécuter un outil ou une API intégrée.
   ```python
   {"tool": "web_search", "arguments": {"query": "Latest AI developments"}}
   ```

3. **Évaluer** : Effectuer des calculs ou manipuler des données.
   ```python
   {"evaluate": {"average_score": "sum(scores) / len(scores)"}}
   ```

4. **Logique Conditionnelle** : Exécuter des étapes en fonction de conditions.
   ```python
   {"if": "score > 0.8", "then": [...], "else": [...]}
   ```

5. **Boucles** : Itérez sur des données ou répétez des étapes.

```python
   {"foreach": {"in": "data_list", "do": [...]}}
   ```

| Nom de l'Étape     | Description                                                                                      | Entrée                                              |
|--------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Invite**         | Envoyer un message au modèle IA et recevoir une réponse.                                        | Texte de l'invite ou modèle                          |
| **Appel d'Outil**  | Exécuter un outil ou une API intégrée.                                                           | Nom de l'outil et arguments                          |
| **Évaluer**        | Effectuer des calculs ou manipuler des données.                                                 | Expressions ou variables à évaluer                   |
| **Attendre l'Entrée** | Mettre le flux de travail en pause jusqu'à ce qu'une entrée soit reçue.                      | Toute entrée utilisateur ou système requise          |
| **Journaliser**    | Journaliser une valeur ou un message spécifié.                                                  | Message ou valeur à journaliser                      |
| **Intégrer**       | Intégrer du texte dans un format ou système spécifique.                                         | Texte ou contenu à intégrer                          |
| **Rechercher**     | Effectuer une recherche de documents basée sur une requête.                                     | Requête de recherche                                 |
| **Obtenir**        | Récupérer une valeur d'un magasin de clé-valeur.                                               | Identifiant de clé                                   |
| **Définir**        | Assigner une valeur à une clé dans un magasin de clé-valeur.                                    | Clé et valeur à assigner                             |
| **Parallèle**      | Exécuter plusieurs étapes en parallèle.                                                         | Liste des étapes à exécuter simultanément            |
| **PourChaque**     | Itérer sur une collection et effectuer des étapes pour chaque élément.                         | Collection ou liste à itérer                         |
| **MapReduce**      | Mapper sur une collection et réduire les résultats en fonction d'une expression.                | Collection à mapper et expressions à réduire         |
| **Si Sinon**       | Exécution conditionnelle des étapes en fonction d'une condition.                                | Condition à évaluer                                  |
| **Switch**         | Exécuter des étapes en fonction de plusieurs conditions, similaire à une instruction switch-case.| Conditions multiples et étapes correspondantes       |
| **Renvoyer**       | Exécuter un sous-flux de travail et attendre son achèvement.                                   | Identifiant de sous-flux de travail et données d'entrée|
| **Erreur**         | Gérer les erreurs en spécifiant un message d'erreur.                                          | Message d'erreur ou instructions de gestion          |
| **Dormir**         | Mettre le flux de travail en pause pour une durée spécifiée.                                   | Durée (secondes, minutes, etc.)                      |
| **Retourner**      | Retourner une valeur du flux de travail.                                                        | Valeur à retourner                                   |

Pour des informations détaillées sur chaque type d'étape et une utilisation avancée, veuillez vous référer à notre [Documentation sur les Tâches](https://docs.julep.ai/tasks).

## Fonctionnalités Avancées

Julep offre une gamme de fonctionnalités avancées pour améliorer vos flux de travail IA :

### Ajout d'Outils aux Agents

Étendez les capacités de votre agent en intégrant des outils et des APIs externes :

```python
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="Search the web for information.",
    integration={
        "provider": "google",
        "method": "search",
        "setup": {"api_key": "your_google_api_key"},
    },
)
```

### Gestion des Sessions et des Utilisateurs

Julep offre une gestion robuste des sessions pour des interactions persistantes :

```python
session = client.sessions.create(
    agent_id=agent.id,
    user_id="user123",
    context_overflow="adaptive"
)

# Continue conversation in the same session
response = client.sessions.chat(
    session_id=session.id,
    message="Follow up on our previous conversation."
)
```

### Intégration et Recherche de Documents

Gérez et recherchez facilement des documents pour vos agents :

```python
# Upload a document
document = client.documents.create(
    file="path/to/document.pdf",
    metadata={"category": "research_paper"}
)

# Search documents
results = client.documents.search(
    query="AI advancements",
    filter={"category": "research_paper"}
)
```

Pour des fonctionnalités plus avancées et une utilisation détaillée, veuillez vous référer à notre [Documentation sur les Fonctionnalités Avancées](https://docs.julep.ai/advanced-features).

## Référence SDK

- [SDK Node.js](https://github.com/julep-ai/node-sdk/blob/main/api.md)
- [SDK Python](https://github.com/julep-ai/python-sdk/blob/main/api.md)

## Référence API

Explorez notre documentation API complète pour en savoir plus sur les agents, les tâches et les exécutions :

- [API Agents](https://api.julep.ai/api/docs#tag/agents)
- [API Tâches](https://api.julep.ai/api/docs#tag/tasks)
- [API Exécutions](https://api.julep.ai/api/docs#tag/executions)

## Exemples et Tutoriels

Découvrez des projets d'exemple et des tutoriels pour vous aider à démarrer et à construire sur les exemples fournis :

- [Projets d'Exemple](https://github.com/julep-ai/julep/tree/main/examples)
- [Tutoriels](https://docs.julep.ai/tutorials)

## Contribution

Nous accueillons les contributions au projet ! Apprenez comment contribuer et notre code de conduite :

- [Directives de Contribution](https://github.com/julep-ai/julep/blob/main/CONTRIBUTING.md)
- [Code de Conduite](https://github.com/julep-ai/julep/blob/main/CODE_OF_CONDUCT.md)

## Support et Communauté

Rejoignez notre communauté pour obtenir de l'aide, poser des questions et partager vos idées :

- [Discord](https://discord.com/invite/JTSBGRZrzj)
- [Discussions GitHub](https://github.com/julep-ai/julep/discussions)
- [Twitter](https://twitter.com/julep_ai)

## Licence

Ce projet est sous licence [Apache License 2.0](https://github.com/julep-ai/julep/blob/main/LICENSE).

## Remerciements

Nous tenons à exprimer notre gratitude à tous les contributeurs et à la communauté open-source pour leurs précieuses ressources et contributions.


