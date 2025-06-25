<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<h3>📖 Table des matières</h3>

  - [
    
    ·
    
    ·
    
  ](#%C2%B7%0A----%0A----%C2%B7)
- [Pourquoi Julep ?](#pourquoi-julep-)
- [Commencer](#commencer)
- [Documentation et exemples](#documentation-et-exemples)
- [Communauté et contributions](#communauté-et-contributions)
- [Licence](#licence)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

<sup><div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  [Deutsch](https://www.readme-i18n.com/julep-ai/julep?lang=de) | 
  [Español](https://www.readme-i18n.com/julep-ai/julep?lang=es) | 
  [français](https://www.readme-i18n.com/julep-ai/julep?lang=fr) | 
  [日本語](https://www.readme-i18n.com/julep-ai/julep?lang=ja) | 
  [한국어](https://www.readme-i18n.com/julep-ai/julep?lang=ko) | 
  [Português](https://www.readme-i18n.com/julep-ai/julep?lang=pt) | 
  [Русский](https://www.readme-i18n.com/julep-ai/julep?lang=ru) | 
  [中文](https://www.readme-i18n.com/julep-ai/julep?lang=zh)
</div></sup>

<div align="center" id="top">
<img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Serverless%20AI%20Workflows%20for%20Data%20%26%20ML%20Teams&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" height=300 />

<br>
  <p>
   <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License" height="28"></a>
  </p>
  
  <h3 align="center">
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow"><img src="https://user-images.githubusercontent.com/74038190/235294015-47144047-25ab-417c-af1b-6746820a20ff.gif" width="60"></a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow"><img src="https://raw.githubusercontent.com/gist/IgnaceMaes/744cd9cf41ec6acf46fc8f4e9f370f86/raw/d16658c2945d30c8a953b35cb17dd7085111b46c/x-logo.svg" width="45"></a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow"><img src="https://user-images.githubusercontent.com/74038190/235294012-0a55e343-37ad-4b0f-924f-c8431d9d2483.gif" width="60"></a>

  </h3>
  
  <!-- <h3>
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
  </h3> -->
</div>

**Essayez Julep dès aujourd'hui :** Visitez le **[Site Web de Julep](https://julep.ai)** · Commencez sur le **[Tableau de Bord Julep](https://dashboard.julep.ai)** (clé API gratuite) · Lisez la **[Documentation](https://docs.julep.ai/introduction/julep)**

<img src="https://private-user-images.githubusercontent.com/112978092/456212419-e8e13991-c0fe-46f7-a1db-5969da909dda.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTAxOTUwNzcsIm5iZiI6MTc1MDE5NDc3NywicGF0aCI6Ii8xMTI5NzgwOTIvNDU2MjEyNDE5LWU4ZTEzOTkxLWMwZmUtNDZmNy1hMWRiLTU5NjlkYTkwOWRkYS5naWY_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwNjE3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDYxN1QyMTEyNTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0wOTYzMWEwNDBlNzkwYzc2NDg4OTFmNzUwMjljZDQ5Y2JiZWIzMjMxOGM4MDc3N2I3YTlhNDlkYjY0OWY2YmIyJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.EmG9Ba0fnv-EF2FtkbnY0uVmRJROynLtTg2W9wzGuu4">

## Pourquoi Julep ?

Julep est une plateforme open-source pour construire des **flux de travail d'IA basés sur des agents** qui vont bien au-delà de simples chaînes de prompts. Elle vous permet d'orchestrer des processus complexes en plusieurs étapes avec des modèles de langage de grande taille (LLM) et des outils **sans gérer d'infrastructure**. Avec Julep, vous pouvez créer des agents d'IA qui **se souviennent des interactions passées** et gèrent des tâches sophistiquées avec une logique de branchement, des boucles, une exécution parallèle et l'intégration d'APIs externes. En bref, Julep agit comme un *"Firebase pour les agents d'IA,"* fournissant un backend robuste pour les flux de travail intelligents à grande échelle.

**Caractéristiques clés et avantages :**

* **Mémoire persistante :** Construisez des agents d'IA qui maintiennent le contexte et la mémoire à long terme à travers les conversations, afin qu'ils puissent apprendre et s'améliorer au fil du temps.
* **Flux de travail modulaires :** Définissez des tâches complexes comme des étapes modulaires (en YAML ou code) avec une logique conditionnelle, des boucles et la gestion d'erreurs. Le moteur de flux de travail de Julep gère automatiquement les processus multi-étapes et les décisions.
* **Orchestration d'outils :** Intégrez facilement des outils externes et des APIs (recherche web, bases de données, services tiers, etc.) dans la boîte à outils de votre agent. Les agents de Julep peuvent invoquer ces outils pour augmenter leurs capacités, permettant la génération augmentée par récupération et plus.
* **Parallèle et extensible :** Exécutez plusieurs opérations en parallèle pour l'efficacité, et laissez Julep gérer la mise à l'échelle et la concurrence en arrière-plan. La plateforme est sans serveur, donc elle met à l'échelle les flux de travail de manière transparente sans surcharge DevOps supplémentaire.
* **Exécution fiable :** Ne vous inquiétez pas des problèmes - Julep fournit des réessais intégrés, des étapes d'auto-guérison et une gestion d'erreurs robuste pour maintenir les tâches de longue durée sur la bonne voie. Vous obtenez également une surveillance et une journalisation en temps réel pour suivre les progrès.
* **Intégration facile :** Commencez rapidement avec nos SDKs pour **Python** et **Node.js**, ou utilisez le CLI Julep pour les scripts. L'API REST de Julep est disponible si vous voulez intégrer directement dans d'autres systèmes.

*Concentrez-vous sur votre logique et créativité d'IA, pendant que Julep s'occupe du gros travail !* <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/2c0eef4b-7b75-42bd-9722-4bea97a2d532" width="20">

<img src="https://private-user-images.githubusercontent.com/112978092/456212419-e8e13991-c0fe-46f7-a1db-5969da909dda.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTAxOTUwNzcsIm5iZiI6MTc1MDE5NDc3NywicGF0aCI6Ii8xMTI5NzgwOTIvNDU2MjEyNDE5LWU4ZTEzOTkxLWMwZmUtNDZmNy1hMWRiLTU5NjlkYTkwOWRkYS5naWY_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwNjE3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDYxN1QyMTEyNTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0wOTYzMWEwNDBlNzkwYzc2NDg4OTFmNzUwMjljZDQ5Y2JiZWIzMjMxOGM4MDc3N2I3YTlhNDlkYjY0OWY2YmIyJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.EmG9Ba0fnv-EF2FtkbnY0uVmRJROynLtTg2W9wzGuu4">

## Commencer
<p>
    <a href="https://dashboard.julep.ai">
      <img src="https://img.shields.io/badge/Get_API_Key-FF5733?style=logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXYxNGw5IDQgOS00VjVsLTktNHptMCAyLjh2MTYuNEw1IDE2LjJWNi44bDctMy4yem0yIDguMmwtMi0yLTIgMiAyIDIgMi0yeiIvPjwvc3ZnPg==" alt="Obtenir la clé API" height="28">
    </a>
    <span>&nbsp;</span>
    <a href="https://docs.julep.ai">
      <img src="https://img.shields.io/badge/Documentation-4B32C3?style=logo=gitbook&logoColor=white" alt="Documentation" height="28">
    </a>
  </p>
Démarrer avec Julep est simple :

1. **Inscription et clé API :** D'abord, inscrivez-vous sur le [Tableau de Bord Julep](https://dashboard.julep.ai) pour obtenir votre clé API (nécessaire pour authentifier vos appels SDK).
2. **Installer le SDK :** Installez le SDK Julep pour votre langage préféré :

   * <img src="https://user-images.githubusercontent.com/74038190/212257472-08e52665-c503-4bd9-aa20-f5a4dae769b5.gif" width="20"> **Python :** `pip install julep`
   * <img src="https://user-images.githubusercontent.com/74038190/212257454-16e3712e-945a-4ca2-b238-408ad0bf87e6.gif" width="20"> **Node.js :** `npm install @julep/sdk` (ou `yarn add @julep/sdk`)
3. **Définir votre agent :** Utilisez le SDK ou YAML pour définir un agent et son flux de travail de tâches. Par exemple, vous pouvez spécifier la mémoire de l'agent, les outils qu'il peut utiliser, et une logique de tâche étape par étape. (Voir le **[Guide de démarrage rapide](https://docs.julep.ai/introduction/quick-start)** dans notre documentation pour une procédure détaillée.)
4. **Exécuter un flux de travail :** Invoquez votre agent via le SDK pour exécuter la tâche. La plateforme Julep orchestrera l'ensemble du flux de travail dans le cloud et gérera l'état, les appels d'outils et les interactions LLM pour vous. Vous pouvez vérifier la sortie de l'agent, surveiller l'exécution sur le tableau de bord, et itérer selon les besoins.

C'est tout ! Votre premier agent d'IA peut être opérationnel en quelques minutes. Pour un tutoriel complet, consultez le **[Guide de démarrage rapide](https://docs.julep.ai/introduction/quick-start)** dans la documentation.

> **Note :** Julep offre également une interface en ligne de commande (CLI) (actuellement en bêta pour Python) pour gérer les flux de travail et les agents. Si vous préférez une approche sans code ou voulez scripter des tâches communes, voir les [documents CLI Julep](https://docs.julep.ai/responses/quickstart#cli-installation) pour plus de détails.

<img src="https://private-user-images.githubusercontent.com/112978092/456212419-e8e13991-c0fe-46f7-a1db-5969da909dda.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTAxOTUwNzcsIm5iZiI6MTc1MDE5NDc3NywicGF0aCI6Ii8xMTI5NzgwOTIvNDU2MjEyNDE5LWU4ZTEzOTkxLWMwZmUtNDZmNy1hMWRiLTU5NjlkYTkwOWRkYS5naWY_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwNjE3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDYxN1QyMTEyNTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0wOTYzMWEwNDBlNzkwYzc2NDg4OTFmNzUwMjljZDQ5Y2JiZWIzMjMxOGM4MDc3N2I3YTlhNDlkYjY0OWY2YmIyJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.EmG9Ba0fnv-EF2FtkbnY0uVmRJROynLtTg2W9wzGuu4">

## Documentation et exemples


Vous voulez plonger plus profondément ? La **[Documentation Julep](https://docs.julep.ai)** couvre tout ce dont vous avez besoin pour maîtriser la plateforme - des concepts fondamentaux (Agents, Tâches, Sessions, Outils) aux sujets avancés comme la gestion de la mémoire des agents et les éléments internes de l'architecture. Les ressources clés incluent :

* **[Guides de concepts](https://docs.julep.ai/concepts/) :** Apprenez sur l'architecture de Julep, comment fonctionnent les sessions et la mémoire, l'utilisation d'outils, la gestion de longues conversations, et plus.
* **[Référence API et SDK](https://docs.julep.ai/api-reference/) :** Trouvez une référence détaillée pour toutes les méthodes SDK et les points de terminaison de l'API REST pour intégrer Julep dans vos applications.
* **[Tutoriels](https://docs.julep.ai/tutorials/) :** Guides étape par étape pour construire des applications réelles (ex. un agent de recherche qui parcourt le web, un assistant de planification de voyage, ou un chatbot avec des connaissances personnalisées).
* **[Recettes de livre de cuisine](https://github.com/julep-ai/julep/tree/dev/cookbooks) :** Explorez le **Livre de cuisine Julep** pour des exemples de flux de travail et d'agents prêts à l'emploi. Ces recettes démontrent des modèles communs et des cas d'usage - un excellent moyen d'apprendre par l'exemple. *Parcourez le répertoire [`cookbooks/`](https://github.com/julep-ai/julep/tree/dev/cookbooks) dans ce dépôt pour des définitions d'agents d'exemple.*

<img src="https://private-user-images.githubusercontent.com/112978092/456212419-e8e13991-c0fe-46f7-a1db-5969da909dda.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTAxOTUwNzcsIm5iZiI6MTc1MDE5NDc3NywicGF0aCI6Ii8xMTI5NzgwOTIvNDU2MjEyNDE5LWU4ZTEzOTkxLWMwZmUtNDZmNy1hMWRiLTU5NjlkYTkwOWRkYS5naWY_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwNjE3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDYxN1QyMTEyNTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0wOTYzMWEwNDBlNzkwYzc2NDg4OTFmNzUwMjljZDQ5Y2JiZWIzMjMxOGM4MDc3N2I3YTlhNDlkYjY0OWY2YmIyJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.EmG9Ba0fnv-EF2FtkbnY0uVmRJROynLtTg2W9wzGuu4">

<img src="https://private-user-images.githubusercontent.com/112978092/456212419-e8e13991-c0fe-46f7-a1db-5969da909dda.gif?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTAxOTUwNzcsIm5iZiI6MTc1MDE5NDc3NywicGF0aCI6Ii8xMTI5NzgwOTIvNDU2MjEyNDE5LWU4ZTEzOTkxLWMwZmUtNDZmNy1hMWRiLTU5NjlkYTkwOWRkYS5naWY_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwNjE3JTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDYxN1QyMTEyNTdaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0wOTYzMWEwNDBlNzkwYzc2NDg4OTFmNzUwMjljZDQ5Y2JiZWIzMjMxOGM4MDc3N2I3YTlhNDlkYjY0OWY2YmIyJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.EmG9Ba0fnv-EF2FtkbnY0uVmRJROynLtTg2W9wzGuu4">

## Communauté et contributions

Rejoignez notre communauté grandissante de développeurs et d'enthousiastes de l'IA ! Voici quelques façons de s'impliquer et d'obtenir du soutien :

* **Communauté Discord :** Vous avez des questions ou des idées ? Rejoignez la conversation sur notre [serveur Discord officiel](https://discord.gg/7H5peSN9QP) pour discuter avec l'équipe Julep et d'autres utilisateurs. Nous sommes heureux d'aider avec le dépannage ou de réfléchir à de nouveaux cas d'usage.
* **Discussions et issues GitHub :** N'hésitez pas à utiliser GitHub pour signaler des bugs, demander des fonctionnalités, ou discuter des détails d'implémentation. Consultez les [**bonnes premières issues**](https://github.com/julep-ai/julep/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) si vous souhaitez contribuer - nous accueillons les contributions de toutes sortes.
* **Contribuer :** Si vous voulez contribuer du code ou des améliorations, veuillez voir notre [Guide de contribution](CONTRIBUTING.md) pour comment commencer. Nous apprécions toutes les PR et les retours. En collaborant, nous pouvons rendre Julep encore meilleur !

*Conseil de pro : <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/e379a33a-b428-4385-b44f-3da16e7bac9f" width="35"> Mettez une étoile à notre dépôt pour rester à jour - nous ajoutons constamment de nouvelles fonctionnalités et exemples.*    

<br/>

Vos contributions, grandes ou petites, nous sont précieuses. Construisons quelque chose d'incroyable ensemble !    <img src="https://github.com/Anmol-Baranwal/Cool-GIFs-For-GitHub/assets/74038190/2c0eef4b-7b75-42bd-9722-4bea97a2d532" width="20">
 <img src="https://user-images.githubusercontent.com/74038190/216125640-2783ebd5-e63e-4ed1-b491-627a40b24850.png" width="20">

<h4>Nos contributeurs extraordinaires :</h4>

<a href="https://github.com/julep-ai/julep/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=julep-ai/julep" />
</a>

<br/>

## Licence

Julep est offert sous la **Licence Apache 2.0**, ce qui signifie qu'il est libre d'utilisation dans vos propres projets. Voir le fichier [LICENSE](LICENSE) pour plus de détails. Amusez-vous à construire avec Julep !