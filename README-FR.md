<sup>[English](README.md) | [中文翻译](README-CN.md) | [日本語翻訳](README-JA.md) | [French](README-FR.md)</sup>

<div align="center" id="top">
 <img src="https://github.com/user-attachments/assets/10ba11e4-4ced-400e-a400-ee0f72541780" alt="julep" width="640" height="320" />
</div>

<p align="center">
  <br />
  <a href="https://docs.julep.ai" rel="dofollow">Explorer les documents (en cours)</a>
  ·
  <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discorde</a>
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

---

> [!REMARQUE]
> 👨‍💻 Vous êtes ici pour l'événement devfest.ai ? Rejoignez notre [Discord](https://discord.com/invite/JTSBGRZrzj) et consultez les détails ci-dessous.
>
> Obtenez votre clé API [ici](https://dashboard-dev.julep.ai).

<details>
<summary><b>🌟 Contributeurs et participants au DevFest.AI</b>(Cliquez pour agrandir)</summary>

## 🌟 Appel aux contributeurs !

Nous sommes ravis d'accueillir de nouveaux contributeurs au projet Julep ! Nous avons créé plusieurs « bons premiers numéros » pour vous aider à démarrer. Voici comment vous pouvez contribuer :

1. Consultez notre fichier [CONTRIBUTING.md](https://github.com/julep-ai/julep/blob/dev/CONTRIBUTING.md) pour obtenir des instructions sur la façon de contribuer.
2. Parcourez nos [bons premiers numéros](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) pour trouver une tâche qui vous intéresse.
3. Si vous avez des questions ou avez besoin d'aide, n'hésitez pas à nous contacter sur notre chaîne [Discord](https://discord.com/invite/JTSBGRZrzj).

Vos contributions, grandes ou petites, sont précieuses pour nous. Construisons ensemble quelque chose d'extraordinaire ! 🚀

### 🎉 DevFest.AI octobre 2024

Des nouvelles passionnantes ! Nous participons au DevFest.AI tout au long du mois d'octobre 2024 ! 🗓️

- Contribuez à Julep pendant cet événement et obtenez une chance de gagner de superbes produits et cadeaux Julep ! 🎁
- Rejoignez des développeurs du monde entier pour contribuer aux référentiels d'IA et participer à des événements incroyables.
- Un grand merci à DevFest.AI pour l'organisation de cette fantastique initiative !

> [!TIP]
> Prêt à vous joindre à la fête ? **[Tweetez que vous participez](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)** et commençons à coder ! 🖥️

![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)

</details>

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 Table des matières</h3>

- [Présentation](#introduction)
- [Caractéristiques principales](#key-features)
- [Exemple rapide](#quick-example)
- [Installation](#installation)
- [Démarrage rapide de Python 🐍](#python-quick-start-)
- [Démarrage rapide de Node.js 🟩](#nodejs-quick-start-)
- [Étape 1 : Créer un agent](#step-1-create-an-agent)
- [Composants](#composants)
- [Modèle mental](#mental-model)
- [Concepts](#concepts)
- [Comprendre les tâches](#understanding-tasks)
- [Cycle de vie d'une tâche](#cycle-de-vie-d-une-tâche)
- [Types d'étapes de flux de travail](#types-of-workflow-steps)
- [Types d'outils](#types-d'outils)
- [`Fonctions` définies par l'utilisateur](#user-defined-functions)
- [outils système](#outils-système)
- [`Intégrations` intégrées](#integrations-integrées)
- [Appels directs `api_calls`](#appels directs-api_calls)
- [Intégrations](#intégrations)
- [Autres fonctionnalités](#other-features)
- [Ajout d'outils aux agents](#adding-tools-to-agents)
- [Gestion des sessions et des utilisateurs](#managing-sessions-and-users)
- [Intégration et recherche de documents](#document-integration-and-search)
- [Référence](#référence)
- [Référence SDK](#sdk-reference)
- [Référence API](#api-reference)
- [Démarrage rapide local](#local-quickstart)
- [Quelle est la différence entre Julep et LangChain etc ?](#quelle-est-la-différence-entre-julep-et-langchain-etc)
- [Différents cas d'utilisation](#different-use-cases)
- [Facteur de forme différent](#different-form-factor)
- [En résumé](#en-resumé)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Introduction

Julep est une plateforme permettant de créer des agents IA qui se souviennent des interactions passées et peuvent effectuer des tâches complexes. Elle offre une mémoire à long terme et gère des processus en plusieurs étapes.

Julep permet la création de tâches en plusieurs étapes intégrant la prise de décision, les boucles, le traitement parallèle et l'intégration avec de nombreux outils et API externes.

Alors que de nombreuses applications d'IA se limitent à des chaînes simples et linéaires d'invites et d'appels d'API avec une ramification minimale, Julep est conçu pour gérer des scénarios plus complexes qui :

- comporter plusieurs étapes,
- prendre des décisions basées sur les résultats du modèle,
- générer des branches parallèles,
- utiliser beaucoup d'outils, et
- courir pendant une longue période.

> [!TIP]
> Imaginez que vous souhaitiez créer un agent d'IA capable de faire plus que simplement répondre à des questions simples : il doit gérer des tâches complexes, mémoriser des interactions passées et peut-être même utiliser d'autres outils ou API. C'est là qu'intervient Julep. Lisez [Comprendre les tâches](#understanding-tasks) pour en savoir plus.

## Principales caractéristiques

1. 🧠 **Agents IA persistants** : mémorisent le contexte et les informations au cours d'interactions à long terme.
2. 💾 **Sessions avec état** : gardez une trace des interactions passées pour des réponses personnalisées.
3. 🔄 **Tâches en plusieurs étapes** : créez des processus complexes en plusieurs étapes avec des boucles et une prise de décision.
4. ⏳ **Gestion des tâches** : gérez les tâches de longue durée qui peuvent s'exécuter indéfiniment.
5. 🛠️ **Outils intégrés** : utilisez des outils intégrés et des API externes dans vos tâches.
6. 🔧 **Auto-réparation** : Julep réessaiera automatiquement les étapes ayant échoué, renverra les messages et assurera généralement le bon déroulement de vos tâches.
7. 📚 **RAG** ​​: Utilisez le magasin de documents de Julep pour créer un système permettant de récupérer et d'utiliser vos propres données.

![fonctionnalités](https://github.com/user-attachments/assets/4355cbae-fcbd-4510-ac0d-f8f77b73af70)

> [!TIP]
> Julep est idéal pour les applications qui nécessitent des cas d’utilisation de l’IA au-delà des simples modèles de réponse rapide.

## Exemple rapide

Imaginez un agent d’IA de recherche capable d’effectuer les opérations suivantes :

1. **Prenez un sujet**,
2. **Proposez 100 requêtes de recherche** pour ce sujet,
3. Effectuez ces **recherches Web en parallèle**,
4. **Résumez** les résultats,
5. Envoyez le **résumé à Discord**.

> [!REMARQUE]
> Dans Julep, ce serait une tâche unique sous<b>80 lignes de code</b>et courir<b>entièrement géré</b>tout seul. Toutes les étapes sont exécutées sur les propres serveurs de Julep et vous n'avez pas besoin de lever le petit doigt.

Voici un exemple fonctionnel :

```yaml
name: Research Agent

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
        api_key: BSAqES7dj9d... # dummy key

  - name: discord_webhook
    type: api_call
    api_call:
      url: https://eobuxj02se0n.m.pipedream.net # dummy requestbin
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
    parallelism: 10

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
    settings:
      model: gpt-4o-mini

  # Send the summary to Discord
  - tool: discord_webhook
    arguments:
      content: |-
        f'''
        **Research Summary for {inputs[0].topic}**

        {_}
        '''
```

Dans cet exemple, Julep gérera automatiquement les exécutions parallèles, réessayera les étapes ayant échoué, renverra les requêtes API et maintiendra les tâches en cours d'exécution de manière fiable jusqu'à leur achèvement.

> Cela s'exécute en moins de 30 secondes et renvoie le résultat suivant :

<details>
<summary><b>Résumé de la recherche sur l'IA</b> <i>(Cliquez pour agrandir)</i></summary>

> **Résumé de la recherche sur l'IA**
>
> ### Résumé des résultats de recherche sur l'intelligence artificielle (IA)
>
> #### Présentation
>
> Le domaine de l’intelligence artificielle (IA) a connu des avancées significatives ces dernières années, marquées par le développement de méthodes et de technologies permettant aux machines de percevoir leur environnement, d’apprendre à partir de données et de prendre des décisions. L’objectif principal de ce résumé est de présenter les enseignements tirés de divers résultats de recherche liés à l’IA.
>
> #### Principales conclusions
>
> 1. **Définition et portée de l’IA** :
>
> - L'IA est définie comme une branche de l'informatique axée sur la création de systèmes capables d'effectuer des tâches nécessitant une intelligence humaine, notamment l'apprentissage, le raisonnement et la résolution de problèmes (Wikipedia).
> - Il englobe divers sous-domaines, notamment l’apprentissage automatique, le traitement du langage naturel, la robotique et la vision par ordinateur.
>
> 2. **Impact et applications** :
>
> - Les technologies d'IA sont intégrées dans de nombreux secteurs, améliorant l'efficacité et la productivité. Les applications vont des véhicules autonomes et des diagnostics de santé à l'automatisation du service client et aux prévisions financières (OpenAI).
> - L'engagement de Google à rendre l'IA bénéfique pour tous met en évidence son potentiel à améliorer considérablement la vie quotidienne en améliorant l'expérience utilisateur sur diverses plateformes (Google AI).
>
> 3. **Considérations éthiques** :
>
> - Un débat est en cours sur les implications éthiques de l'IA, notamment sur les préoccupations relatives à la confidentialité, aux préjugés et à la responsabilité dans les processus de prise de décision. La nécessité d'un cadre garantissant l'utilisation sûre et responsable des technologies de l'IA est soulignée (OpenAI).
>
> 4. **Mécanismes d’apprentissage** :
>
> - Les systèmes d'IA utilisent différents mécanismes d'apprentissage, tels que l'apprentissage supervisé, l'apprentissage non supervisé et l'apprentissage par renforcement. Ces méthodes permettent à l'IA d'améliorer ses performances au fil du temps en apprenant des expériences et des données passées (Wikipedia).
> - La distinction entre l’apprentissage supervisé et non supervisé est essentielle ; l’apprentissage supervisé s’appuie sur des données étiquetées, tandis que l’apprentissage non supervisé identifie des modèles sans étiquettes prédéfinies (non supervisé).
>
> 5. **Orientations futures**:
> - Les futurs développements de l’IA devraient se concentrer sur l’amélioration de l’interprétabilité et de la transparence des systèmes d’IA, garantissant qu’ils peuvent fournir des décisions et des actions justifiables (OpenAI).
> - On observe également une volonté de rendre les systèmes d’IA plus accessibles et plus conviviaux, encourageant une adoption plus large dans différents groupes démographiques et secteurs (Google AI).
>
> #### Conclusion
>
> L’IA représente une force de transformation dans de nombreux domaines, promettant de remodeler les industries et d’améliorer la qualité de vie. Cependant, à mesure que ses capacités se développent, il est essentiel de tenir compte des implications éthiques et sociétales qui en découlent. La poursuite des recherches et de la collaboration entre les technologues, les éthiciens et les décideurs politiques sera essentielle pour s’orienter dans le futur paysage de l’IA.

</details>

## Installation

Pour commencer à utiliser Julep, installez-le en utilisant [npm](https://www.npmjs.com/package/@julep/sdk) ou [pip](https://pypi.org/project/julep/) :

**Node.js**:

```bash
npm install @julep/sdk

# or

bun add @julep/sdk
```

**Python**:

```bash
pip install julep
```

> [!REMARQUE]
> Obtenez votre clé API [ici](https://dashboard-dev.julep.ai).
>
> Pendant que nous sommes en version bêta, vous pouvez également nous contacter sur [Discord](https://discord.com/invite/JTSBGRZrzj) pour obtenir la levée des limites de débit sur votre clé API.

> [!TIP]
> 💻 Êtes-vous du genre à vouloir _montrer le code !™_ ? Nous avons créé une multitude de livres de recettes pour vous aider à démarrer. **Consultez les [livres de recettes](https://github.com/julep-ai/julep/tree/dev/cookbooks)** pour parcourir les exemples.
>
> 💡 Il existe également de nombreuses idées que vous pouvez développer en plus de Julep. **Consultez la [liste d'idées](https://github.com/julep-ai/julep/tree/dev/cookbooks/IDEAS.md)** pour vous inspirer.

## Démarrage rapide de Python 🐍

````python
### Step 0: Setup

import time
import yaml
from julep import Julep # or AsyncJulep

client = Julep(api_key="your_julep_api_key")

### Step 1: Create an Agent

agent = client.agents.create(
    name="Storytelling Agent",
    model="claude-3.5-sonnet",
    about="You are a creative storyteller that crafts engaging stories on a myriad of topics.",
)

### Step 2: Create a Task that generates a story and comic strip

task_yaml = """
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
          Based on the idea '{{_.idea}}', generate a list of 5 plot ideas. Go crazy and be as creative as possible. Return your output as a list of long strings inside ```balises yaml à la fin de votre réponse.
déballer : vrai

- évaluer:
plot_ideas : load_yaml(_.split('```yaml')[1].split('```')[0].strip())

# Étape 2 : Extraire les domaines de recherche des idées de l'intrigue
- rapide:
- rôle : système
contenu : Vous êtes {{agent.name}}. {{agent.about}}
- rôle : utilisateur
contenu : >
Voici quelques idées d’intrigue pour une histoire :
{% pour l'idée dans _.plot_ideas %}
- {{idée}}
{% fin de %}

Pour développer l’histoire, nous devons rechercher les idées d’intrigue.
Sur quoi devrions-nous faire des recherches ? Notez les requêtes de recherche Wikipédia pour les idées d'intrigue que vous trouvez intéressantes.
Renvoyez votre sortie sous forme de liste yaml à l'intérieur```yaml tags at the end of your response.
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
          Then finally write the plot as a yaml object inside ```balises yaml à la fin de votre réponse. L'objet yaml doit avoir la structure suivante :

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

Assurez-vous que le fichier YAML est valide et que les caractères et les scènes ne sont pas vides. Faites également attention aux points-virgules et autres problèmes liés à l'écriture du fichier YAML.
déballer : vrai

- évaluer:
intrigue : « load_yaml(_.split('```yaml')[1].split('```')[0].strip())"
"""

tâche = client.tasks.create(
agent_id=agent.id,
**yaml.safe_load(tâche_yaml)
)

### Étape 3 : Exécuter la tâche

exécution = client.executions.create(
task_id=task.id,
input={"idea": "Un chat qui apprend à voler"}
)

# 🎉 Regardez l'histoire et les panneaux de bande dessinée se générer
while (result := client.executions.get(execution.id)).status n'est pas dans ['réussi', 'échec'] :
print(résultat.statut, résultat.sortie)
heure.sommeil(1)

# 📦 Une fois l'exécution terminée, récupérez les résultats
si result.status == "réussi" :
imprimer(résultat.sortie)
autre:
déclencher une exception (résultat.erreur)
````

You can find the full python example [here](example.py).

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Node.js Quick Start 🟩

```javascript
// Étape 0 : Configuration
const dotenv = require("dotenv");
const { Julep } = require("@julep/sdk");
const yaml = require("yaml");

dotenv.config();

const client = nouveau Julep({
Clé API : processus.env.JULEP_API_KEY,
environnement : process.env.JULEP_ENVIRONMENT || "production",
});

/* Étape 1 : Créer un agent */

fonction asynchrone createAgent() {
agent constant = attendez que le client.agents.create({
nom : « Agent de narration »,
modèle : "claude-3.5-sonnet",
à propos de:
« Vous êtes un conteur créatif qui crée des histoires captivantes sur une myriade de sujets. »,
  });
agent de retour;
}

/* Étape 2 : Créer une tâche qui génère une histoire et une bande dessinée */

const tâcheYaml = `
nom : Conteur
description : Créez une histoire basée sur une idée.

outils:
- nom : research_wikipedia
intégration:
fournisseur : wikipedia
méthode : recherche

principal:
# Étape 1 : Générer une idée d'intrigue
- rapide:
- rôle : système
contenu : Vous êtes {{agent.name}}. {{agent.about}}
- rôle : utilisateur
contenu : >
En vous basant sur l'idée « {{_.idea}} », générez une liste de 5 idées d'intrigue. Laissez libre cours à votre créativité. Renvoyez votre résultat sous forme de liste de longues chaînes à l'intérieur des balises \`\`\`yaml à la fin de votre réponse.
déballer : vrai

- évaluer:
plot_ideas: load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())

# Étape 2 : Extraire les domaines de recherche des idées de l'intrigue
- rapide:
- rôle : système
contenu : Vous êtes {{agent.name}}. {{agent.about}}
- rôle : utilisateur
contenu : >
Voici quelques idées d’intrigue pour une histoire :
{% pour l'idée dans _.plot_ideas %}
- {{idée}}
{% fin de %}

Pour développer l’histoire, nous devons rechercher les idées d’intrigue.
Sur quoi devrions-nous faire des recherches ? Notez les requêtes de recherche Wikipédia pour les idées d'intrigue que vous trouvez intéressantes.
Renvoyez votre sortie sous forme de liste yaml à l'intérieur des balises \`\`\`yaml à la fin de votre réponse.
déballer : vrai
paramètres:
modèle: gpt-4o-mini
température: 0,7

- évaluer:
requêtes de recherche : load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip())

# Étape 3 : Recherchez chaque idée d'intrigue
- pour chaque :
dans : _.research_queries
faire:
outil : research_wikipedia
Arguments:
requête: _

- évaluer:
wikipedia_results: 'NEWLINE.join([f"- {doc.metadata.title}: {doc.metadata.summary}" pour l'élément dans _ pour le document dans l'élément.documents])'

# Étape 4 : Réfléchir et délibérer
- rapide:
- rôle : système
contenu : Vous êtes {{agent.name}}. {{agent.about}}
- rôle : utilisateur
contenu: |-
Avant d'écrire l'histoire, réfléchissons et délibérons. Voici quelques idées d'intrigue :
{% pour l'idée dans les sorties[1].plot_ideas %}
- {{idée}}
{% fin de %}

Voici les résultats de la recherche d'idées d'intrigue sur Wikipédia :
{{_.wikipedia_results}}

Réfléchissez aux idées de l'intrigue de manière critique. Combinez les idées de l'intrigue avec les résultats de Wikipédia pour créer une intrigue détaillée pour une histoire.
Écrivez toutes vos notes et vos pensées.
Ensuite, écrivez enfin le tracé sous forme d'objet yaml à l'intérieur des balises \`\`\`yaml à la fin de votre réponse. L'objet yaml doit avoir la structure suivante :

\`\`\`yaml
titre: "<string>"
personnages:
- nom: "<string>"
à propos de: "<string>"
résumé: "<string>"
scènes:
- titre: "<string>"
description: "<string>"
personnages:
- nom: "<string>"
rôle: "<string>"
intrigues:
            - "<string>"\`\`\`

Assurez-vous que le fichier YAML est valide et que les caractères et les scènes ne sont pas vides. Faites également attention aux points-virgules et autres problèmes liés à l'écriture du fichier YAML.
déballer : vrai

- évaluer:
tracé : « load_yaml(_.split('\`\`\`yaml')[1].split('\`\`\`')[0].strip()) »
`;

fonction asynchrone createTask(agentId) {
const tâche = wait client.tasks.create(agentId, yaml.parse(taskYaml));
tâche de retour;
}

/* Étape 3 : Exécuter la tâche */

fonction asynchrone executeTask(taskId) {
const exécution = attendre client.executions.create(taskId, {
entrée : { idée : "Un chat qui apprend à voler" },
  });

// 🎉 Regardez comment l'histoire et les panneaux de bande dessinée sont générés
tandis que (vrai) {
const résultat = wait client.executions.get(execution.id);
console.log(résultat.status, résultat.output);

si (résultat.status === "réussi" || résultat.status === "échec") {
// 📦 Une fois l'exécution terminée, récupérez les résultats
si (résultat.status === "réussi") {
console.log(résultat.sortie);
} autre {
lancer une nouvelle erreur (résultat.erreur);
      }
casser;
    }

attendre une nouvelle promesse((résolution) => setTimeout(résolution, 1000));
  }
}

// Fonction principale pour exécuter l'exemple
fonction asynchrone main() {
essayer {
agent constant = wait createAgent();
const tâche = wait createTask(agent.id);
attendre executeTask(task.id);
} catch (erreur) {
console.error("Une erreur s'est produite :", error);
  }
}

principal()
.then(() => console.log("Terminé"))
.catch(console.erreur);
```

You can find the full Node.js example [here](example.js).

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

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

   - You can use the Julep SDK in your application to define agents, tasks, and workflows.
   - The SDK provides functions and classes that make it easy to set up and manage these components.

2. **Julep Backend Service:**

   - The SDK communicates with the Julep backend over the network.
   - The backend handles execution of tasks, maintains session state, stores documents, and orchestrates workflows.

3. **Integration with Tools and APIs:**
   - Within your workflows, you can integrate external tools and services.
   - The backend facilitates these integrations, so your agents can, for example, perform web searches, access databases, or call third-party APIs.

## Concepts

Julep is built on several key technical components that work together to create powerful AI workflows:

```sirène
graphique TD
Utilisateur[Utilisateur] ==> Session[Session]
Session --> Agent[Agent]
Agent --> Tâches[Tâches]
Agent --> LLM [Modèle de langage étendu]
Tâches --> Outils[Outils]
Agent --> Documents[Documents]
Documents --> VectorDB[Base de données vectorielles]
Tâches --> Exécutions[Exécutions]

client classDef remplissage : #9ff, trait : #333, largeur du trait : 1 px ;
classe Utilisateur client ;

classDef core fill:#f9f,trait:#333,largeur-trait:2px;
classe Agent,Tâches,Session core;
```

- **Agents**: AI-powered entities backed by large language models (LLMs) that execute tasks and interact with users.
- **Users**: Entities that interact with agents through sessions.
- **Sessions**: Stateful interactions between agents and users, maintaining context across multiple exchanges.
- **Tasks**: Multi-step, programmatic workflows that agents can execute, including various types of steps like prompts, tool calls, and conditional logic.
- **Tools**: Integrations that extend an agent's capabilities, including user-defined functions, system tools, or third-party API integrations.
- **Documents**: Text or data objects associated with agents or users, vectorized and stored for semantic search and retrieval.
- **Executions**: Instances of tasks that have been initiated with specific inputs, with their own lifecycle and state machine.

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Understanding Tasks

Tasks are the core of Julep's workflow system. They allow you to define complex, multi-step AI workflows that your agents can execute. Here's a brief overview of task components:

- **Name, Description and Input Schema**: Each task has a unique name and description for easy identification. An input schema (optional) that is used to validate the input to the task.
- **Main Steps**: The core of a task, defining the sequence of actions to be performed. Each step can be a prompt, tool call, evaluate, wait_for_input, log, get, set, foreach, map_reduce, if-else, switch, sleep, or return. (See [Types of Workflow Steps](#types-of-workflow-steps) for more details)
- **Tools**: Optional integrations that extend the capabilities of your agent during task execution.

### Lifecycle of a Task

You create a task using the Julep SDK and specify the main steps that the agent will execute. When you execute a task, the following lifecycle happens:

```sirène
Diagramme de séquence
participant D comme votre code
participant C en tant que client Julep
participant S en tant que serveur Julep

D->>C : Créer une tâche
C->>S : Soumettre l'exécution
Remarque sur S : Exécuter la tâche
Remarque sur S : Gérer l'état
S-->>C : Événements d'exécution
C-->>D : Mises à jour de la progression
S->>C : Fin de l'exécution
C->>D : Résultat final
```

### Types of Workflow Steps

Tasks in Julep can include various types of steps, allowing you to create complex and powerful workflows. Here's an overview of the available step types:

#### Common Steps

<table>
<tr>
    <th>Name</th>
    <th>About</th>
    <th>Syntax</th>
</tr>
<tr>
<td> <b>Prompt</b> </td>
<td>
Send a message to the AI model and receive a response
<br><br><b>Note:</b> The prompt step uses Jinja templates and you can access context variables in them.
</td>

<td>

```YAML
- invite : « Analyser les données suivantes : {{agent.name}} » # <-- ceci est un modèle jinja
```

```YAML
- rapide:
- rôle : système
contenu : « Vous êtes {{agent.name}}. {{agent.about}} »
- rôle : utilisateur
contenu : « Analysez les données suivantes : {{_.data}} »
```

</td>
</tr>
<tr>
<td> <b>Tool Call</b> </td>
<td>
Execute an integrated tool or API that you have previously declared in the task.
<br><br><b>Note:</b> The tool call step uses Python expressions inside the arguments.

</td>

<td>

```YAML
- outil : recherche_sur_le_web
Arguments:
requête : « Derniers développements de l'IA » # <-- il s'agit d'une expression Python (remarquez les guillemets)
num_results: len(_.topics) # <-- expression python pour accéder à la longueur d'une liste
```

</td>
</tr>
<tr>
<td> <b>Evaluate</b> </td>
<td>
Perform calculations or manipulate data
<br><br><b>Note:</b> The evaluate step uses Python expressions.
</td>

<td>

```YAML
- évaluer:
average_score : somme(scores) / len(scores)
```

</td>
</tr>
<tr>
<td> <b>Wait for Input</b> </td>
<td>
Pause workflow until input is received. It accepts an `info` field that can be used by your application to collect input from the user.

<br><br><b>Note:</b> The wait_for_input step is useful when you want to pause the workflow and wait for user input e.g. to collect a response to a prompt.

</td>

<td>

```YAML
- attendre_la_saisie :
info:
message : « Veuillez fournir des informations supplémentaires sur {_.required_info}. » # <-- expression Python pour accéder à la variable de contexte
```

</td>
</tr>
<tr>
<td> <b>Log</b> </td>
<td>
Log a specified value or message.

<br><br><b>Note:</b> The log step uses Jinja templates and you can access context variables in them.

</td>

<td>

```YAML
- log : « Traitement terminé pour l'élément {{_.item_id}} » # <-- modèle jinja pour accéder à la variable de contexte
```

</td>
</tr>
</table>

#### Key-Value Steps

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>Get</b> </td>
<td>
Retrieve a value from the execution's key-value store.

</td>

<td>

```YAML
- obtenir : préférences_utilisateur
```

</td>
</tr>
<tr>
<td> <b>Set</b> </td>
<td>
Assign a value to a key in the execution's key-value store.

<br><br><b>Note:</b> The set step uses Python expressions.

</td>

<td>

```YAML
- ensemble:
préférence_utilisateur : '"dark_mode"' # <-- expression python
```

</td>
</tr>
</table>

#### Iteration Steps

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>Foreach</b> </td>
<td>
Iterate over a collection and perform steps for each item

</td>

<td>

```YAML
- pour chaque :
dans : _.data_list # <-- expression python pour accéder à la variable de contexte
faire:
- log : « Traitement de l'élément {{_.item}} » # <-- modèle jinja pour accéder à la variable de contexte
```

</td>
</tr>
<tr>
<td> <b>Map-Reduce</b> </td>
<td>
Map over a collection and reduce the results

</td>

<td>

```YAML
- map_reduce:
over: _.numbers # <-- expression python pour accéder à la variable de contexte
carte:
- évaluer:
au carré : "_ ** 2"
réduire : résultats + [_] # <-- (facultatif) expression Python pour réduire les résultats. Il s'agit de la valeur par défaut si elle est omise.
```

```YAML
- map_reduce:
plus de: _.topics
carte:
- invite : Rédigez un essai sur {{_}}
parallélisme : 10
```

</td>
</tr>
<tr>
<td> <b>Parallel</b> </td>
<td>
Run multiple steps in parallel

</td>

<td>

```YAML
- parallèle:
- outil : recherche_sur_le_web
Arguments:
requête : « Actualités sur l'IA »
- outil : weather_check
Arguments:
Lieu : « New York »
```

</td>
</tr>
</table>

#### Conditional Steps

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>If-Else</b> </td>
<td>
Conditional execution of steps

</td>

<td>

```YAML
- si : _.score > 0.8 # <-- expression python
alors:
- log : score élevé atteint
autre:
- erreur : le score doit être amélioré
```

</td>
</tr>
<tr>
<td> <b>Switch</b> </td>
<td>
Execute steps based on multiple conditions

</td>

<td>

```YAML
- changer:
- cas : _.category == 'A'
alors:
- log : « Traitement de catégorie A »
- cas : _.category == 'B'
alors:
- log : « Traitement de catégorie B »
- case: _ # Cas par défaut
alors:
- erreur : catégorie inconnue
```

</td>
</tr>
</table>

#### Other Control Flow

<table>
<tr>
<th> Name </th> <th> About </th><th>Syntax</th>
</tr>
<tr>
<td> <b>Sleep</b> </td>
<td>
Pause the workflow for a specified duration

</td>

<td>

```YAML
- dormir:
secondes: 30
# minutes: 1
# heures: 1
# jours: 1
```

</td>
</tr>
<tr>
<td> <b>Return</b> </td>
<td>
Return a value from the workflow

<br><br><b>Note:</b> The return step uses Python expressions.

</td>

<td>

```YAML
- retour:
résultat : " Tâche terminée avec succès " # <-- expression python
heure : datetime.now().isoformat() # <-- expression python
```

</td>
</tr>
<tr>
<td> <b>Yield</b> </td>
<td>
Run a subworkflow and await its completion

</td>

<td>

```YAML
- rendement:
flux de travail : données_de_processus
Arguments:
données_d'entrée : _. données_raw # <-- expression python
```

</td>
</tr>
</tr>
<tr>
<td> <b>Error</b> </td>
<td>
Handle errors by specifying an error message

</td>

<td>

```YAML
- erreur : « Entrée non valide fournie » # <-- Chaînes uniquement
```

</td>
</tr>
</table>

Each step type serves a specific purpose in building sophisticated AI workflows. This categorization helps in understanding the various control flows and operations available in Julep tasks.

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Tool Types

Agents can be given access to a number of "tools" -- any programmatic interface that a foundation model can "call" with a set of inputs to achieve a goal. For example, it might use a `web_search(query)` tool to search the Internet for some information.

Unlike agent frameworks, julep is a _backend_ that manages agent execution. Clients can interact with agents using our SDKs. julep takes care of executing tasks and running integrations.

Tools in julep can be one of:

1. **User-defined `functions`**: These are function signatures that you can give the model to choose from, similar to how [openai]'s function-calling works. They need to be handled by the client. The workflow will pause until the client calls the function and gives the results back to julep.
2. **`system` tools**: Built-in tools that can be used to call the julep APIs themselves, like triggering a task execution, appending to a metadata field, etc.
3. **`integrations`**: Built-in third party tools that can be used to extend the capabilities of your agents.
4. **`api_calls`**: Direct api calls during workflow executions as tool calls.

### User-defined `functions`

These are function signatures that you can give the model to choose from, similar to how [openai]'s function-calling works. An example:

```YAML
nom : Exemple de tâche d'outil système
description : Lister les agents à l'aide d'un appel système

outils:
- nom : send_notification
description : Envoyer une notification à l'utilisateur
type : fonction
fonction:
paramètres:
type: objet
propriétés:
texte:
type : chaîne
description : Contenu de la notification

principal:
- outil : send_notification
Arguments:
contenu : '"salut"' # <-- expression python
```

Whenever julep encounters a _user-defined function_, it pauses, giving control back to the client and waits for the client to run the function call and give the results back to julep.

> [!TIP] > **Example cookbook**: [cookbooks/13-Error_Handling_and_Recovery.py](https://github.com/julep-ai/julep/blob/dev/cookbooks/13-Error_Handling_and_Recovery.py)

### `system` tools

Built-in tools that can be used to call the julep APIs themselves, like triggering a task execution, appending to a metadata field, etc.

`system` tools are built into the backend. They get executed automatically when needed. They do _not_ require any action from the client-side.

For example,

```YAML
nom : Exemple de tâche d'outil système
description : Lister les agents à l'aide d'un appel système

outils:
- nom : list_agent_docs
description : liste tous les documents pour l'agent donné
type : système
système:
ressource : agent
sous-ressource : doc
opération : liste

principal:
- outil : list_agents
Arguments:
limite : 10 # <-- expression python
```

#### Available `system` resources and operations

- `agent`:

  - `list`: List all agents.
  - `get`: Get a single agent by id.
  - `create`: Create a new agent.
  - `update`: Update an existing agent.
  - `delete`: Delete an existing agent.

- `user`:

  - `list`: List all users.
  - `get`: Get a single user by id.
  - `create`: Create a new user.
  - `update`: Update an existing user.
  - `delete`: Delete an existing user.

- `session`:

  - `list`: List all sessions.
  - `get`: Get a single session by id.
  - `create`: Create a new session.
  - `update`: Update an existing session.
  - `delete`: Delete an existing session.
  - `chat`: Chat with a session.
  - `history`: Get the chat history with a session.

- `task`:

  - `list`: List all tasks.
  - `get`: Get a single task by id.
  - `create`: Create a new task.
  - `update`: Update an existing task.
  - `delete`: Delete an existing task.

- `doc` (subresource for `agent` and `user`):
  - `list`: List all documents.
  - `create`: Create a new document.
  - `delete`: Delete an existing document.
  - `search`: Search for documents.

Additional operations available for some resources:

- `embed`: Embed a resource (specific resources not specified in the provided code).
- `change_status`: Change the status of a resource (specific resources not specified in the provided code).
- `chat`: Chat with a resource (specific resources not specified in the provided code).
- `history`: Get the chat history with a resource (specific resources not specified in the provided code).
- `create_or_update`: Create a new resource or update an existing one (specific resources not specified in the provided code).

Note: The availability of these operations may vary depending on the specific resource and implementation details.

> [!TIP] > **Example cookbook**: [cookbooks/10-Document_Management_and_Search.py](https://github.com/julep-ai/julep/blob/dev/cookbooks/10-Document_Management_and_Search.py)

### Built-in `integrations`

Julep comes with a number of built-in integrations (as described in the section below). `integration` tools are directly executed on the julep backend. Any additional parameters needed by them at runtime can be set in the agent/session/user's `metadata` fields.

See [Integrations](#integrations) for details on the available integrations.

> [!TIP] > **Example cookbook**: [cookbooks/01-Website_Crawler_using_Spider.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/01-Website_Crawler_using_Spider.ipynb)

### Direct `api_calls`

julep can also directly make api calls during workflow executions as tool calls. Same as `integration`s, additional runtime parameters are loaded from `metadata` fields.

For example,

```YAML
nom : Exemple de tâche api_call
outils:
- type : api_call
nom : bonjour
appel_API :
méthode : GET
URL: https://httpbin.org/get

principal:
- outil : bonjour
Arguments:
json:
test: _.input # <-- expression python
```

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Integrations

Julep supports various integrations that extend the capabilities of your AI agents. Here's a list of available integrations and their supported arguments:

<table>

<tr>
<td> <b>Brave Search</b> </td>
<td>

```YAML
installation:
api_key : chaîne # La clé API pour Brave Search

Arguments:
requête : chaîne # La requête de recherche pour rechercher avec Brave

sortir:
résultat : chaîne # Le résultat de la recherche Brave
```

</td>

<td>

**Example cookbook**: [cookbooks/03-SmartResearcher_With_WebSearch.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/03-SmartResearcher_With_WebSearch.ipynb)

</td>
</tr>
<tr>
<td> <b>BrowserBase</b> </td>
<td>

```YAML
installation:
api_key : chaîne # La clé API pour BrowserBase
project_id : chaîne # L'ID de projet pour BrowserBase
session_id : chaîne # (facultatif) L'ID de session pour BrowserBase

Arguments:
urls : liste[chaîne] # Les URL pour le chargement avec BrowserBase

sortir:
documents : liste # Les documents chargés à partir des URL
```

</td>

</tr>
<tr>
<td> <b>Email</b> </td>
<td>

```YAML
installation:
hôte : chaîne # L'hôte du serveur de messagerie
port : entier # Le port du serveur de messagerie
utilisateur : chaîne # Le nom d'utilisateur du serveur de messagerie
mot de passe : chaîne # Le mot de passe du serveur de messagerie

Arguments:
à : chaîne # L'adresse e-mail à laquelle envoyer l'e-mail
de : chaîne # L'adresse e-mail à partir de laquelle envoyer l'e-mail
objet : chaîne # L'objet de l'e-mail
corps : chaîne # Le corps de l'e-mail

sortir:
succès : booléen # Indique si l'e-mail a été envoyé avec succès
```

</td>

<td>

**Example cookbook**: [cookbooks/00-Devfest-Email-Assistant.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/00-Devfest-Email-Assistant.ipynb)

</td>
</tr>
<tr>
<td> <b>Spider</b> </td>
<td>

```YAML
installation:
spider_api_key : chaîne # La clé API pour Spider

Arguments:
url : chaîne # L'URL pour laquelle récupérer les données
mode : chaîne # Le type de robots d'exploration (par défaut : « scrape »)
paramètres : dict # (facultatif) Les paramètres de l'API Spider

sortir:
documents : liste # Les documents renvoyés par l'araignée
```

</td>

<td>

**Example cookbook**: [cookbooks/01-Website_Crawler_using_Spider.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/01-Website_Crawler_using_Spider.ipynb)

</td>
</tr>
<tr>
<td> <b>Weather</b> </td>
<td>

```YAML
installation:
openweathermap_api_key : chaîne # La clé API pour OpenWeatherMap

Arguments:
emplacement : chaîne # L'emplacement pour lequel récupérer les données météorologiques

sortir:
résultat : chaîne # Les données météorologiques pour l'emplacement spécifié
```

</td>

<td>

**Example cookbook**: [cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb)

</td>
</tr>
</tr>
<tr>
<td> <b>Wikipedia</b> </td>
<td>

```YAML
Arguments:
requête : chaîne # La chaîne de requête de recherche
load_max_docs : entier # Nombre maximal de documents à charger (par défaut : 2)

sortir:
documents : liste # Les documents renvoyés par la recherche sur Wikipédia
```

</td>

<td>

**Example cookbook**: [cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb](https://github.com/julep-ai/julep/blob/dev/cookbooks/04-TripPlanner_With_Weather_And_WikiInfo.ipynb)

</td>
</tr>
</table>

For more details, refer to our [Integrations Documentation](#integrations).

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Other Features

Julep offers a range of advanced features to enhance your AI workflows:

### Adding Tools to Agents

Extend your agent's capabilities by integrating external tools and APIs:

```python
client.agents.outils.créer(
agent_id=agent.id,
nom="recherche_sur_le_web",
description="Rechercher des informations sur le Web.",
intégration={
"fournisseur": "courageux",
"méthode": "recherche",
"setup": {"api_key": "votre_brave_api_key"},
    },
)
```

### Managing Sessions and Users

Julep provides robust session management for persistent interactions:

```python
session = client.sessions.create(
agent_id=agent.id,
user_id=utilisateur.id,
context_overflow="adaptatif"
)

# Poursuivre la conversation dans la même session
réponse = client.sessions.chat(
session_id=session.id,
messages=[
      {
"rôle": "utilisateur",
« contenu » : « Suivi de la conversation précédente. »
      }
    ]
)
```

### Document Integration and Search

Easily manage and search through documents for your agents:

```python
# Télécharger un document
document = client.agents.docs.create(
titre="Progrès de l'IA",
content="L'IA change le monde...",
métadonnées={"category": "article_de_recherche"}
)

# Rechercher des documents
résultats = client.agents.docs.search(
texte="Progrès de l'IA",
metadata_filter={"category": "article_de_recherche"}
)
```

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Référence

### Référence du SDK

- **Node.js** [Référence SDK](https://github.com/julep-ai/node-sdk/blob/main/api.md) | [Package NPM](https://www.npmjs.com/package/@julep/sdk)
- **Python** [Référence SDK](https://github.com/julep-ai/python-sdk/blob/main/api.md) | [Package PyPI](https://pypi.org/project/julep/)

### Référence API

Explorez notre documentation API pour en savoir plus sur les agents, les tâches et les exécutions :

- [API des agents](https://dev.julep.ai/api/docs#tag/agents)
- [API des tâches](https://dev.julep.ai/api/docs#tag/tasks)
- [API d'exécution](https://dev.julep.ai/api/docs#tag/executions)

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

## Démarrage rapide local

**Exigences**:

- dernier docker compose installé

**Mesures**:

1. `git clone https://github.com/julep-ai/julep.git`
2. `cd julep`
3. `docker volume create cozo_backup`
4. `docker volume create cozo_data`
5. `cp .env.example .env # <-- Modifier ce fichier`
6. `docker compose --env-file .env --profile temporal-ui --profile single-tenant --profile self-hosted-db up --build`

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>

---

## Quelle est la différence entre Julep et LangChain etc ?

### Différents cas d'utilisation

Considérez LangChain et Julep comme des outils avec des objectifs différents au sein de la pile de développement de l’IA.

LangChain est idéal pour créer des séquences d'invites et gérer les interactions avec les LLM. Il dispose d'un vaste écosystème avec de nombreuses intégrations prédéfinies, ce qui le rend pratique si vous souhaitez mettre en place quelque chose rapidement. LangChain s'adapte bien aux cas d'utilisation simples qui impliquent une chaîne linéaire d'invites et d'appels d'API.

Julep, en revanche, s'intéresse davantage à la création d'agents d'IA persistants capables de conserver le contexte lors d'interactions à long terme. Il est idéal lorsque vous avez besoin de flux de travail complexes impliquant des tâches en plusieurs étapes, une logique conditionnelle et une intégration avec divers outils ou API directement dans le processus de l'agent. Il est conçu dès le départ pour gérer les sessions persistantes et les flux de travail complexes.

Utilisez Julep si vous imaginez créer un assistant IA complexe qui doit :

- Suivez les interactions des utilisateurs sur plusieurs jours ou semaines.
- Exécutez des tâches planifiées, comme l'envoi de résumés quotidiens ou la surveillance des sources de données.
- Prendre des décisions basées sur des interactions antérieures ou des données stockées.
- Interagir avec plusieurs services externes dans le cadre de son flux de travail.

Ensuite, Julep fournit l’infrastructure pour prendre en charge tout cela sans que vous ayez à le construire à partir de zéro.

### Facteur de forme différent

Julep est une **plateforme** qui comprend un langage pour décrire les workflows, un serveur pour exécuter ces workflows et un SDK pour interagir avec la plateforme. Pour créer quelque chose avec Julep, vous écrivez une description du workflow en YAML, puis vous exécutez le workflow dans le cloud.

Julep est conçu pour les flux de travail lourds, en plusieurs étapes et de longue durée, et il n'y a aucune limite à la complexité du flux de travail.

LangChain est une **bibliothèque** qui inclut quelques outils et un framework pour créer des chaînes linéaires d'invites et d'outils. Pour créer quelque chose avec LangChain, vous écrivez généralement du code Python qui configure et exécute les chaînes de modèles que vous souhaitez utiliser.

LangChain pourrait être suffisant et plus rapide à mettre en œuvre pour les cas d'utilisation simples impliquant une chaîne linéaire d'invites et d'appels d'API.

### En résumé

Utilisez LangChain lorsque vous devez gérer les interactions LLM et les séquences d'invite dans un contexte sans état ou à court terme.

Choisissez Julep lorsque vous avez besoin d'un framework robuste pour les agents avec état avec des capacités de workflow avancées, des sessions persistantes et une orchestration de tâches complexes.

<div align="center">
    <a href="#top">
        <img src="https://img.shields.io/badge/Back%20to%20Top-000000?style=for-the-badge&logo=github&logoColor=white" alt="Back to Top">
    </a>&nbsp;|&nbsp;
    <a href="#-table-of-contents">
        <img src="https://img.shields.io/badge/Table%20of%20Contents-000000?style=for-the-badge&logo=github&logoColor=white" alt="Table of Contents">
    </a>
</div>
