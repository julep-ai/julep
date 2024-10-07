<sup>English | [中文翻译](/README-CN.md) | [日本語翻訳](/README-JP.md) | [français(/README-FR.md)</sup>

<div align="center">
 <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=API%20for%20building%20multi-step%20agent%20workflows.&forks=1&name=1&owner=1&pattern=Solid&stargazers=1&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&theme=Auto" alt="julep" width="640" height="320" />
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

*****

> [!NOTE]
> 👨‍💻 Ici pour l'événement devfest.ai ? Rejoignez notre [Discord](https://discord.com/invite/JTSBGRZrzj) et consultez les détails ci-dessous.

<details>
<summary><b>🌟 Contributeurs et Participants à DevFest.AI</b> (Cliquez pour développer)</summary>

## 🌟 Appel à Contributeurs !

Nous sommes ravis d'accueillir de nouveaux contributeurs au projet Julep ! Nous avons créé plusieurs "good first issues" pour vous aider à démarrer. Voici comment vous pouvez contribuer :

1. Consultez notre fichier [CONTRIBUTING.md](CONTRIBUTING.md) pour des directives sur la façon de contribuer.
2. Parcourez nos [good first issues](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) pour trouver une tâche qui vous intéresse.
3. Si vous avez des questions ou avez besoin d'aide, n'hésitez pas à nous contacter sur notre chaîne [Discord](https://discord.com/invite/JTSBGRZrzj).

Vos contributions, grandes ou petites, sont précieuses pour nous. Construisons ensemble quelque chose d'extraordinaire ! 🚀

### 🎉 DevFest.AI Octobre 2024

Bonne nouvelle ! Nous participons à DevFest.AI tout au long du mois d'octobre 2024 ! 🗓️

- Contribuez à Julep pendant cet événement et tentez de gagner des articles Julep exclusifs et des goodies ! 🎁
- Rejoignez des développeurs du monde entier pour contribuer à des dépôts d'IA et participer à des événements incroyables.
- Un grand merci à DevFest.AI pour l'organisation de cette fantastique initiative !

> [!TIP]
> Prêt à rejoindre l'aventure ? **[Tweete que tu participes](https://twitter.com/intent/tweet?text=Pumped%20to%20be%20participating%20in%20%40devfestai%20with%20%40julep_ai%20building%20%23ai%20%23agents%20%23workflows%20Let's%20gooo!%20https%3A%2F%2Fgit.new%2Fjulep)** et commençons à coder ! 🖥️

![Julep DevFest.AI](https://media.giphy.com/media/YjyUeyotft6epaMHtU/giphy.gif)

</details>

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<details>
<summary><h3>📖 Table des Matières</h3></summary>

- [Introduction](#introduction)
- [Exemple Rapide](#exemple-rapide)
- [Caractéristiques Clés](#caracteristiques-cles)
- [Pourquoi Julep vs. LangChain ?](#pourquoi-julep-vs-langchain)
  - [Cas d'utilisation différents](#cas-dutilisation-differents)
  - [Forme Différente](#forme-differente)
  - [En Résumé](#en-resume)
- [Installation](#installation)
- [Démarrage Rapide Python 🐍](#demarrage-rapide-python-)
  - [Étape 1 : Créer un Agent](#etape-1-creer-un-agent)
  - [Étape 2 : Créer une Tâche qui génère une histoire et une bande dessinée](#etape-2-creer-une-tache-qui-genere-une-histoire-et-une-bande-dessinee)
  - [Étape 3 : Exécuter la Tâche](#etape-3-executer-la-tache)
  - [Étape 4 : Discuter avec l'Agent](#etape-4-discuter-avec-lagent)
- [Démarrage Rapide Node.js 🟩](#demarrage-rapide-nodejs-)
  - [Étape 1 : Créer un Agent](#etape-1-creer-un-agent-1)
  - [Étape 2 : Créer une Tâche qui génère une histoire et une bande dessinée](#etape-2-creer-une-tache-qui-genere-une-histoire-et-une-bande-dessinee-1)
  - [Étape 3 : Exécuter la Tâche](#etape-3-executer-la-tache-1)
  - [Étape 4 : Discuter avec l'Agent](#etape-4-discuter-avec-lagent-1)
- [Composants](#composants)
  - [Modèle Mental](#modele-mental)
- [Concepts](#concepts)
- [Comprendre les Tâches](#comprendre-les-taches)
  - [Types d'Étapes de Workflow](#types-detapes-de-workflow)
- [Fonctionnalités Avancées](#fonctionnalites-avancees)
  - [Ajouter des Outils aux Agents](#ajouter-des-outils-aux-agents)
  - [Gérer les Sessions et les Utilisateurs](#gerer-les-sessions-et-les-utilisateurs)
  - [Intégration et Recherche de Documents](#integration-et-recherche-de-documents)
- [Référence SDK](#reference-sdk)
- [Référence API](#reference-api)

</details>
<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Introduction

<!-- TODO: Ajouter une démonstration vidéo -->

Julep est une plateforme de création d'agents IA capables de maintenir un état et d'exécuter des workflows complexes. Elle offre un contexte à long terme et orchestre des tâches multi-étapes.

Julep vous permet de définir des tâches multi-étapes incluant de la logique conditionnelle, des boucles, du traitement parallèle et une intégration directe avec des centaines d'outils et d'APIs externes. Les applications IA sont souvent linéaires et reposent sur des chaînes simples de quelques invites et appels API sans beaucoup de prise de décision.

> [!TIP]
> Imaginez que vous souhaitez construire un agent IA qui peut faire plus que répondre à des requêtes simples : il doit gérer des tâches complexes, se souvenir des interactions passées et peut-être même s'intégrer à d'autres outils ou API. C'est là que Julep intervient.

## Exemple Rapide

Imaginez un agent de recherche IA capable de :

  1. Prendre un sujet,
  2. Proposer 100 requêtes de recherche pour ce sujet,
  3. Effectuer ces recherches web en parallèle,
  4. Collecter et compiler les résultats,
  5. Proposer 5 questions supplémentaires,
  6. Répéter le processus avec de nouvelles requêtes,
  7. Résumer les résultats,
  8. Envoyer le résumé sur Discord.

Dans Julep, cela constituerait une tâche unique en moins de <b>80 lignes de code</b>, gérée <b>automatiquement</b> du début à la fin. Voici un exemple fonctionnel :

```yaml

Agent de Recherche
Schéma d'entrée (facultatif)

input_schema:
  type: object
  properties:
    topic:
      type: string
      description: Le sujet principal de la recherche


##  Outils définis pour l'agent

tools:
- name: web_search
  type: integration
  integration:
    provider: brave
    setup:
      api_key: "VOTRE_API_BRAVE"

- name: discord_webhook
  type: api_call
  api_call:
    url: "VOTRE_URL_WEBHOOK_DISCORD"
    method: POST
    headers:
      Content-Type: application/json

##Définir le workflow principal

main:
- prompt:
    - role: system
      content: >-
        Vous êtes un assistant de recherche.
        Générer 100 requêtes de recherche liées au sujet : 
        {{inputs[0].topic}}

        Une requête par ligne.
  unwrap: true

- evaluate:
    search_queries: "_.split('\n')"

- over: "_.search_queries"
  map:
    tool: web_search
    arguments:
      query: "_"
  parallelism: 100

- evaluate:
    results: "'\n'.join([item.result for item in _])"

- prompt:
    - role: system
      content: >-
        Sur la base des résultats de recherche suivants, générez 5 questions de suivi pour approfondir notre compréhension de {{inputs[0].topic}} :
        {{_.results}}

        Une question par ligne.
  unwrap: true

- evaluate:
    follow_up_queries: "_.split('\n')"

- over: "_.follow_up_queries"
  map:
    tool: web_search
    arguments:
      query: "_"
  parallelism: 5

- evaluate:
    all_results: "outputs[3].results + '\n'.join([item.result for item in _])"

- prompt:
    - role: system
      content: >
        Vous êtes un résumé de recherche. Créez un résumé complet des résultats de recherche suivants sur le sujet {{inputs[0].topic}}. 
        Le résumé doit être structuré, informatif et souligner les principales découvertes :
        {{_.all_results}}
  unwrap: true

- tool: discord_webhook
  arguments:
    content: >
      **Résumé de recherche pour {{inputs[0].topic}}**

      {{_}}
```
Astuce : Julep gère automatiquement l'exécution parallèle, les étapes échouées, et garantit le bon déroulement des workflows jusqu'à leur achèvement.

## Fonctionnalités Clés

1. **Agents AI persistants** : Maintiennent le contexte et l'état au cours d'interactions à long terme.
2. **Sessions avec état** : Conservent les interactions passées pour fournir des réponses personnalisées.
3. **Workflows multi-étapes** : Permettent de créer des processus complexes avec des boucles et une logique conditionnelle.
4. **Orchestration des tâches** : Gèrent des tâches longues pouvant s'exécuter de manière continue.
5. **Outils intégrés** : Intègrent des outils natifs et des API externes dans les workflows.
6. **Auto-récupération** : Julep relance automatiquement les étapes échouées, renvoie les requêtes API et garantit que les workflows se déroulent de manière fluide.
7. **Récupération de documents augmentée (RAG)** : Utilisez le magasin de documents de Julep pour créer un système RAG (Récupération augmentée par la génération) avec vos propres données.

## Comparaison : Julep vs LangChain

Julep et LangChain visent des cas d’usage différents. 

- **LangChain** est efficace pour des **séquences simples** et la gestion des interactions avec les modèles de langage. Il convient aux cas où une **chaîne linéaire** de prompts et d'appels API suffit.

- **Julep** est idéal pour des **assistants AI persistants** qui nécessitent des **workflows complexes**, une gestion de **sessions longue durée**, et l'**intégration de multiples services externes** dans le processus de l'agent. Il est conçu pour gérer des workflows multi-étapes avec des boucles, une logique conditionnelle, et des tâches planifiées.

### Différents Formats

Julep est une **plateforme** qui inclut un langage pour décrire des workflows, un serveur pour exécuter ces workflows et un SDK pour interagir avec la plateforme. Pour créer quelque chose avec Julep, vous écrivez une description du workflow en `YAML`, puis exécutez le workflow dans le cloud.

Julep est conçu pour des workflows lourds, multi-étapes et de longue durée, sans limite de complexité pour le workflow.

LangChain est une **bibliothèque** qui inclut quelques outils et un cadre pour créer des chaînes linéaires de prompts et d'outils. Pour créer quelque chose avec LangChain, vous écrivez généralement du code Python qui configure et exécute les chaînes de modèles que vous souhaitez utiliser.

LangChain peut être suffisant et plus rapide à implémenter pour des cas d'usage simples impliquant une chaîne linéaire de prompts et d'appels API.

### En résumé

Utilisez LangChain lorsque vous avez besoin de gérer des interactions avec des LLM et des séquences de prompts dans un contexte sans état ou de courte durée.

Choisissez Julep lorsque vous avez besoin d'un cadre robuste pour des agents avec des workflows avancés, des sessions persistantes et une orchestration de tâches complexe.

## Installation

Pour commencer avec Julep, installez-le en utilisant [npm](https://www.npmjs.com/package/@julep/sdk) ou [pip](https://pypi.org/project/julep/) :

```bash
npm install @julep/sdk

pip install julep

[!NOTE] Obtenez votre clé API ici.

Pendant la bêta, vous pouvez demander votre clé API sur Discord.

[!TIP] 💻 Vous êtes du genre montrez-moi le code™ ? Nous avons créé de nombreux exemples pour vous aider à démarrer. Consultez les cookbooks pour parcourir les exemples.

💡 Vous pouvez également trouver de nombreuses idées à construire avec Julep. Consultez la liste d'idées pour vous inspirer.

Démarrage rapide en Python 🐍
Étape 1 : Créer un Agent
python

import yaml
from julep import Julep # ou AsyncJulep

client = Julep(api_key="votre_clé_api_julep")

agent = client.agents.create(
    name="Agent de Récits",
    model="gpt-4o",
    about="Vous êtes un agent créatif qui rédige des récits captivants et génère des bandes dessinées basées sur des idées.",
)

# 🛠️ Ajoutez un outil de génération d'images (DALL·E) à l'agent
client.agents.tools.create(
    agent_id=agent.id,
    name="générateur_image",
    description="Utilisez cet outil pour générer des images basées sur des descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "votre_clé_api_openai",
        },
    },
)
Étape 2 : Créer une Tâche pour générer une histoire et une bande dessinée
Définissons une tâche multi-étapes pour créer une histoire et générer une bande dessinée en 4 panneaux basée sur une idée d'entrée :

python

# 📋 Tâche
# Créez une tâche qui prend une idée et génère une histoire et une bande dessinée en 4 panneaux
task_yaml = """
name: Créateur d'Histoires et de Bandes Dessinées
description: Créer une histoire basée sur une idée et générer une bande dessinée en 4 panneaux illustrant l'histoire.

main:
  # Étape 1 : Générer une histoire et un plan en 4 panneaux
  - prompt:
      - role: system
        content: Vous êtes {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Basé sur l'idée '{{_.idea}}', rédigez une courte histoire adaptée à une bande dessinée en 4 panneaux.
          Fournissez l'histoire et une liste numérotée de 4 brèves descriptions de chaque panneau illustrant les moments clés de l'histoire.
    unwrap: true

  # Étape 2 : Extraire les descriptions des panneaux et l'histoire
  - evaluate:
      story: _.split('1. ')[0].strip()
      panels: re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)

  # Étape 3 : Générer des images pour chaque panneau à l'aide de l'outil de génération d'images
  - foreach:
      in: _.panels
      do:
        tool: générateur_image
        arguments:
          description: _

  # Étape 4 : Générer un titre accrocheur pour l'histoire
  - prompt:
      - role: system
        content: Vous êtes {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Basé sur l'histoire ci-dessous, générez un titre accrocheur.

          Histoire : {{outputs[1].story}}
    unwrap: true

  # Étape 5 : Retourner l'histoire, les images générées et le titre
  - return:
      title: outputs[3]
      story: outputs[1].story
      comic_panels: "[output.image.url for output in outputs[2]]"
"""

task = client.tasks.create(
    agent_id=agent.id,
    **yaml.safe_load(task_yaml)
)
Étape 3 : Exécuter la Tâche
python

# 🚀 Exécutez la tâche avec une idée d'entrée
execution = client.executions.create(
    task_id=task.id,
    input={"idea": "Un chat qui apprend à voler"}
)

# 🎉 Regardez comment l'histoire et les panneaux de bande dessinée sont générés
for transition in client.executions.transitions.stream(execution_id=execution.id):
    print(transition)

# 📦 Une fois l'exécution terminée, récupérez les résultats
result = client.executions.get(execution_id=execution.id)
Étape 4 : Discuter avec l'Agent
Lancez une session de discussion interactive avec l'agent :

python

session = client.sessions.create(agent_id=agent.id)

# 💬 Envoyez des messages à l'agent
while (message := input("Entrez un message : ")) != "quitter":
    response = client.sessions.chat(
        session_id=session.id,
        message=message,
    )

    print(response)

### Différents Formats

Julep est une **plateforme** qui inclut un langage pour décrire des workflows, un serveur pour exécuter ces workflows et un SDK pour interagir avec la plateforme. Pour créer quelque chose avec Julep, vous écrivez une description du workflow en `YAML`, puis exécutez le workflow dans le cloud.

Julep est conçu pour des workflows lourds, multi-étapes et de longue durée, sans limite de complexité pour le workflow.

LangChain est une **bibliothèque** qui inclut quelques outils et un cadre pour créer des chaînes linéaires de prompts et d'outils. Pour créer quelque chose avec LangChain, vous écrivez généralement du code Python qui configure et exécute les chaînes de modèles que vous souhaitez utiliser.

LangChain peut être suffisant et plus rapide à implémenter pour des cas d'usage simples impliquant une chaîne linéaire de prompts et d'appels API.

### En résumé

Utilisez LangChain lorsque vous avez besoin de gérer des interactions avec des LLM et des séquences de prompts dans un contexte sans état ou de courte durée.

Choisissez Julep lorsque vous avez besoin d'un cadre robuste pour des agents avec des workflows avancés, des sessions persistantes et une orchestration de tâches complexe.

## Installation

Pour commencer avec Julep, installez-le en utilisant [npm](https://www.npmjs.com/package/@julep/sdk) ou [pip](https://pypi.org/project/julep/) :

```bash
npm install @julep/sdk
pip install julep

```
[!NOTE] Obtenez votre clé API ici.

Pendant la bêta, vous pouvez demander votre clé API sur Discord.

[!TIP] 💻 Vous êtes du genre montrez-moi le code™ ? Nous avons créé de nombreux exemples pour vous aider à démarrer. Consultez les cookbooks pour parcourir les exemples.

💡 Vous pouvez également trouver de nombreuses idées à construire avec Julep. Consultez la liste d'idées pour vous inspirer.

Démarrage rapide en Python 🐍
Étape 1 : Créer un Agent
```
import yaml
from julep import Julep # ou AsyncJulep

client = Julep(api_key="votre_clé_api_julep")

agent = client.agents.create(
    name="Agent de Récits",
    model="gpt-4o",
    about="Vous êtes un agent créatif qui rédige des récits captivants et génère des bandes dessinées basées sur des idées.",
)

# 🛠️ Ajoutez un outil de génération d'images (DALL·E) à l'agent
client.agents.tools.create(
    agent_id=agent.id,
    name="générateur_image",
    description="Utilisez cet outil pour générer des images basées sur des descriptions.",
    integration={
        "provider": "dalle",
        "method": "generate_image",
        "setup": {
            "api_key": "votre_clé_api_openai",
        },
    },
)
```
Étape 2 : Créer une Tâche pour générer une histoire et une bande dessinée
Définissons une tâche multi-étapes pour créer une histoire et générer une bande dessinée en 4 panneaux basée sur une idée d'entrée :

```
# 📋 Tâche
# Créez une tâche qui prend une idée et génère une histoire et une bande dessinée en 4 panneaux
task_yaml = """
name: Créateur d'Histoires et de Bandes Dessinées
description: Créer une histoire basée sur une idée et générer une bande dessinée en 4 panneaux illustrant l'histoire.

main:
  # Étape 1 : Générer une histoire et un plan en 4 panneaux
  - prompt:
      - role: system
        content: Vous êtes {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Basé sur l'idée '{{_.idea}}', rédigez une courte histoire adaptée à une bande dessinée en 4 panneaux.
          Fournissez l'histoire et une liste numérotée de 4 brèves descriptions de chaque panneau illustrant les moments clés de l'histoire.
    unwrap: true

  # Étape 2 : Extraire les descriptions des panneaux et l'histoire
  - evaluate:
      story: _.split('1. ')[0].strip()
      panels: re.findall(r'\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)', _)

  # Étape 3 : Générer des images pour chaque panneau à l'aide de l'outil de génération d'images
  - foreach:
      in: _.panels
      do:
        tool: générateur_image
        arguments:
          description: _

  # Étape 4 : Générer un titre accrocheur pour l'histoire
  - prompt:
      - role: system
        content: Vous êtes {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Basé sur l'histoire ci-dessous, générez un titre accrocheur.

          Histoire : {{outputs[1].story}}
    unwrap: true

  # Étape 5 : Retourner l'histoire, les images générées et le titre
  - return:
      title: outputs[3]
      story: outputs[1].story
      comic_panels: "[output.image.url for output in outputs[2]]"
"""

task = client.tasks.create(
    agent_id=agent.id,
    **yaml.safe_load(task_yaml)
)
```
Étape 3 : Exécuter la Tâche
```

# 🚀 Exécutez la tâche avec une idée d'entrée
execution = client.executions.create(
    task_id=task.id,
    input={"idea": "Un chat qui apprend à voler"}
)

# 🎉 Regardez comment l'histoire et les panneaux de bande dessinée sont générés
for transition in client.executions.transitions.stream(execution_id=execution.id):
    print(transition)

# 📦 Une fois l'exécution terminée, récupérez les résultats
result = client.executions.get(execution_id=execution.id)

```

Étape 4 : Discuter avec l'Agent
Lancez une session de discussion interactive avec l'agent :

```
session = client.sessions.create(agent_id=agent.id)

# 💬 Envoyez des messages à l'agent
while (message := input("Entrez un message : ")) != "quitter":
    response = client.sessions.chat(
        session_id=session.id,
        message=message,
    )

    print(response)
```
Démarrage rapide en Node.js 🟩
Étape 1 : Créer un Agent
```
import { Julep } from '@julep/sdk';
import yaml from 'js-yaml';

const client = new Julep({ apiKey: 'votre_clé_api_julep' });

async function createAgent() {
  const agent = await client.agents.create({
    name: "Agent de Récits",
    model: "gpt-4",
    about: "Vous êtes un agent créatif qui rédige des récits captivants et génère des bandes dessinées basées sur des idées.",
  });

  // 🛠️ Ajoutez un outil de génération d'images (DALL·E) à l'agent
  await client.agents.tools.create(agent.id, {
    name: "générateur_image",
    description: "Utilisez cet outil pour générer des images basées sur des descriptions.",
    integration: {
      provider: "dalle",
      method: "generate_image",
      setup: {
        api_key: "votre_clé_api_openai",
      },
    },
  });

  return agent;
}
```
Étape 2 : Créer une Tâche pour générer une histoire et une bande dessinée
```
const taskYaml = `
name: Créateur d'Histoires et de Bandes Dessinées
description: Créer une histoire basée sur une idée et générer une bande dessinée en 4 panneaux illustrant l'histoire.

main:
  # Étape 1 : Générer une histoire et un plan en 4 panneaux
  - prompt:
      - role: system
        content: Vous êtes {{agent.name}}. {{agent.about}}
      - role: user
        content: >
          Basé sur l'idée '{{_.idea}}', rédigez une courte histoire adaptée à une bande dessinée en 4 panneaux.
          Fournissez l'histoire et une liste numérotée de 4 brèves descriptions de chaque panneau illustrant les moments clés de l'histoire.
    unwrap: true

  # Étape 2 : Extraire les descriptions des panneaux et l'histoire
  - evaluate:
      story: _.split('1. ')[0].trim()
      panels: _.match(/\\d+\\.\\s*(.*?)(?=\\d+\\.\\s*|$)/g)

  # Étape 3 : Générer des images pour chaque panneau à l
```

Étape 4 : Discussion avec l'Agent

```
async function chatWithAgent(agent) {
  const session = await client.sessions.create({ agent_id: agent.id });

  // 💬 Envoyer des messages à l'agent
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const chat = async () => {
    rl.question("Entrez un message (ou 'quit' pour quitter) : ", async (message) => {
      if (message.toLowerCase() === 'quit') {
        rl.close();
        return;
      }

      const response = await client.sessions.chat(session.id, { message });
      console.log(response);
      chat();
    });
  };

  chat();
}

// Exécuter l'exemple
async function runExample() {
  const agent = await createAgent();
  const task = await createTask(agent);
  const result = await executeTask(task);
  console.log("Résultat de la tâche :", result);
  await chatWithAgent(agent);
}

runExample().catch(console.error);

```

# Composants

## Julep se compose des composants suivants :

### Plateforme Julep
La plateforme Julep est un service cloud qui exécute vos flux de travail. Elle comprend :
- Un langage pour décrire les flux de travail
- Un serveur pour exécuter ces flux
- Un SDK pour interagir avec la plateforme

### SDKs Julep
Les SDKs Julep sont un ensemble de bibliothèques pour construire des flux de travail. Il existe des SDK pour :
- Python
- JavaScript
- D'autres SDKs sont en préparation

### API Julep
L'API Julep est une API RESTful que vous pouvez utiliser pour interagir avec la plateforme Julep.

# Modèle Mental
Pensez à Julep comme à une plateforme qui combine à la fois des composants côté client et côté serveur pour vous aider à construire des agents IA avancés. Voici comment le visualiser :

## Votre Code d'Application
- Vous utilisez le SDK Julep dans votre application pour définir des agents, des tâches et des flux de travail.
- Le SDK fournit des fonctions et des classes qui facilitent la configuration et la gestion de ces composants.

## Service Backend Julep
- Le SDK communique avec le backend Julep via le réseau.
- Le backend gère l'exécution des tâches, maintient l'état de la session, stocke des documents et orchestre les flux de travail.

## Intégration avec des Outils et des APIs
- Au sein de vos flux de travail, vous pouvez intégrer des outils et services externes.
- Le backend facilite ces intégrations, permettant à vos agents de, par exemple, effectuer des recherches sur le web, accéder à des bases de données, ou appeler des APIs tierces.

# En termes plus simples :
- Julep est une plateforme pour construire des agents IA avec état.
- Vous utilisez le SDK (comme un ensemble d'outils) dans votre code pour définir ce que font vos agents.
- Le service backend (que vous pouvez considérer comme le moteur) exécute ces définitions, gère l'état, et traite la complexité.

# Concepts
Julep repose sur plusieurs composants techniques clés qui travaillent ensemble pour créer des flux de travail IA puissants.

```
graph TD
    User[Utilisateur] ==> Session[Session]
    Session --> Agent[Agent]
    Agent --> Tasks[Tâches]
    Agent --> LLM[Modèle de Langage de Grande Taille]
    Tasks --> Tools[Outils]
    Agent --> Documents[Documents]
    Documents --> VectorDB[Base de Données Vectorielle]
    Tasks --> Executions[Exécutions]

    classDef client fill:#9ff,stroke:#333,stroke-width:1px;
    class User client;
    
    classDef core fill:#f9f,stroke:#333,stroke-width:2px;
    class Agent,Tasks,Session core;

```

## Agents
Entités alimentées par IA soutenues par des modèles de langage de grande taille (LLMs) qui exécutent des tâches et interagissent avec les utilisateurs.

## Utilisateurs
Entités qui interagissent avec les agents via des sessions.

## Sessions
Interactions avec état entre agents et utilisateurs, maintenant le contexte à travers plusieurs échanges.

## Tâches
Flux de travail programmatiques à plusieurs étapes que les agents peuvent exécuter, comprenant divers types d'étapes telles que des invites, des appels d'outils, et une logique conditionnelle.

## Outils
Intégrations qui étendent les capacités d'un agent, y compris des fonctions définies par l'utilisateur, des outils système ou des intégrations d'API tierces.

## Documents
Objets texte ou données associés aux agents ou aux utilisateurs, vectorisés et stockés pour une recherche sémantique et une récupération.

## Exécutions
Instances de tâches qui ont été initiées avec des entrées spécifiques, ayant leur propre cycle de vie et machine d'état.

Pour une explication plus détaillée de ces concepts et de leurs interactions, veuillez consulter notre [Documentation sur les Concepts](#).

# Comprendre les Tâches
Les tâches sont le cœur du système de flux de travail de Julep. Elles vous permettent de définir des flux de travail IA complexes à plusieurs étapes que vos agents peuvent exécuter. Voici un aperçu des composants des tâches :

- **Nom et Description** : Chaque tâche a un nom unique et une description pour une identification facile.
- **Étapes Principales** : Le cœur d'une tâche, définissant la séquence d'actions à exécuter.
- **Outils** : Intégrations optionnelles qui étendent les capacités de votre agent lors de l'exécution de la tâche.

## Types d'Étapes de Flux de Travail
Les tâches dans Julep peuvent inclure divers types d'étapes :

- **Invite** : Envoyer un message au modèle IA et recevoir une réponse.

# Comprendre les Tâches
Les tâches sont le cœur du système de flux de travail de Julep. Elles vous permettent de définir des flux de travail IA complexes à plusieurs étapes que vos agents peuvent exécuter. Voici un aperçu des composants des tâches :

- **Nom et Description** : Chaque tâche a un nom unique et une description pour une identification facile.
- **Étapes Principales** : Le cœur d'une tâche, définissant la séquence d'actions à exécuter.
- **Outils** : Intégrations optionnelles qui étendent les capacités de votre agent lors de l'exécution de la tâche.

## Types d'Étapes de Flux de Travail
Les tâches dans Julep peuvent inclure divers types d'étapes :

- **Invite** : Envoyer un message au modèle IA et recevoir une réponse.
    ```python
    {"prompt": "Analysez les données suivantes : {{data}}"}
    ```

- **Appel d'Outil** : Exécuter un outil ou une API intégrée.
    ```python
    {"tool": "web_search", "arguments": {"query": "Derniers développements en IA"}}
    ```

- **Évaluer** : Effectuer des calculs ou manipuler des données.
    ```python
    {"evaluate": {"average_score": "sum(scores) / len(scores)"}}
    ```

- **Logique Conditionnelle** : Exécuter des étapes en fonction de conditions.
    ```python
    {"if": "score > 0.8", "then": [...], "else": [...]}
    ```

- **Boucles** : Itérer sur des données ou répéter des étapes.
    ```python
    {"foreach": {"in": "data_list", "do": [...]}}
    ```

## Tableau des Étapes de Tâches

| Nom de l'Étape        | Description                                               | Entrée                                     |
|-----------------------|-----------------------------------------------------------|--------------------------------------------|
| **Invite**            | Envoyer un message au modèle IA et recevoir une réponse. | Texte ou modèle d'invite                   |
| **Appel d'Outil**     | Exécuter un outil ou une API intégrée.                   | Nom de l'outil et arguments                |
| **Évaluer**           | Effectuer des calculs ou manipuler des données.          | Expressions ou variables à évaluer         |
| **Attendre l'Entrée** | Mettre le flux de travail en pause jusqu'à ce qu'une entrée soit reçue. | Toute entrée requise par l'utilisateur ou le système |
| **Journaliser**       | Journaliser une valeur ou un message spécifié.           | Message ou valeur à journaliser            |
| **Intégrer**          | Intégrer du texte dans un format ou système spécifique.  | Texte ou contenu à intégrer                |
| **Rechercher**        | Effectuer une recherche de documents basée sur une requête. | Requête de recherche                       |
| **Obtenir**           | Récupérer une valeur d'un magasin de clé-valeur.         | Identifiant de la clé                      |
| **Définir**           | Assigner une valeur à une clé dans un magasin de clé-valeur. | Clé et valeur à assigner                   |
| **Parallèle**         | Exécuter plusieurs étapes en parallèle.                   | Liste d'étapes à exécuter simultanément    |
| **Pour Chacun**       | Itérer sur une collection et effectuer des étapes pour chaque élément. | Collection ou liste à parcourir            |
| **MapReduce**         | Mapper sur une collection et réduire les résultats selon une expression. | Collection à mapper et réduire les expressions |
| **Si Sinon**          | Exécution conditionnelle d'étapes basées sur une condition. | Condition à évaluer                        |


Fonctionnalités Avancées
Julep propose une gamme de fonctionnalités avancées pour améliorer vos flux de travail IA :

Ajout d'Outils aux Agents
Élargissez les capacités de votre agent en intégrant des outils et des API externes :

```
client.agents.tools.create(
    agent_id=agent.id,
    name="web_search",
    description="Rechercher des informations sur le web.",
    integration={
        "provider": "google",
        "method": "search",
        "setup": {"api_key": "your_google_api_key"},
    },
)
```

Gestion des Sessions et des Utilisateurs
Julep offre une gestion robuste des sessions pour des interactions persistantes :

```
session = client.sessions.create(
    agent_id=agent.id,
    user_id="user123",
    context_overflow="adaptive"
)

# Continuer la conversation dans la même session
response = client.sessions.chat(
    session_id=session.id,
    message="Faites un suivi de notre conversation précédente."
)

```
Intégration et Recherche de Documents
Gérez et recherchez facilement des documents pour vos agents :

```
# Télécharger un document
document = client.documents.create(
    title="Avancées en IA",
    content="L'IA change le monde...",
    metadata={"category": "research_paper"}
)

# Rechercher des documents
results = client.documents.search(
    query="Avancées en IA",
    metadata_filter={"category": "research_paper"}
)

```
Pour des fonctionnalités plus avancées et une utilisation détaillée, veuillez consulter notre [Documentation sur les Fonctionnalités Avancées](https://docs.julep.ai/advanced-features).

## Référence SDK

- [SDK Node.js](https://github.com/julep-ai/node-sdk/blob/main/api.md)
- [SDK Python](https://github.com/julep-ai/python-sdk/blob/main/api.md)

## Référence API

Explorez notre documentation API complète pour en savoir plus sur les agents, les tâches et les exécutions :

- [API Agents](https://api.julep.ai/api/docs#tag/agents)
- [API Tâches](https://api.julep.ai/api/docs#tag/tasks)
- [API Exécutions](https://api.julep.ai/api/docs#tag/executions)


