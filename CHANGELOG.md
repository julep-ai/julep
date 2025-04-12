<div align="center" id="top">
<img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Serverless%20AI%20Workflows%20for%20Data%20%26%20ML%20Teams&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" height="300" />

<br>
  <p>
    <a href="https://dashboard.julep.ai">
      <img src="https://img.shields.io/badge/Get_API_Key-FF5733?style=logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxwYXRoIGQ9Ik0xMiAxTDMgNXYxNGw5IDQgOS00VjVsLTktNHptMCAyLjh2MTYuNEw1IDE2LjJWNi44bDctMy4yem0yIDguMmwtMi0yLTIgMiAyIDIgMi0yeiIvPjwvc3ZnPg==" alt="Get API Key" height="28">
    </a>
    <span>&nbsp;</span>
    <a href="https://docs.julep.ai">
      <img src="https://img.shields.io/badge/Documentation-4B32C3?style=logo=gitbook&logoColor=white" alt="Documentation" height="28">
    </a>
  </p>
  <p>
   <a href="https://www.npmjs.com/package/@julep/sdk"><img src="https://img.shields.io/npm/v/%40julep%2Fsdk?style=social&amp;logo=npm&amp;link=https%3A%2F%2Fwww.npmjs.com%2Fpackage%2F%40julep%2Fsdk" alt="NPM Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://pypi.org/project/julep"><img src="https://img.shields.io/pypi/v/julep?style=social&amp;logo=python&amp;label=PyPI&amp;link=https%3A%2F%2Fpypi.org%2Fproject%2Fjulep" alt="PyPI - Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://hub.docker.com/u/julepai"><img src="https://img.shields.io/docker/v/julepai/agents-api?sort=semver&amp;style=social&amp;logo=docker&amp;link=https%3A%2F%2Fhub.docker.com%2Fu%2Fjulepai" alt="Docker Image Version" height="28"></a>
    <span>&nbsp;</span>
    <a href="https://choosealicense.com/licenses/apache/"><img src="https://img.shields.io/github/license/julep-ai/julep" alt="GitHub License" height="28"></a>
  </p>
  
  <h3>
    <a href="https://discord.com/invite/JTSBGRZrzj" rel="dofollow">Discord</a>
    ·
    <a href="https://x.com/julep_ai" rel="dofollow">𝕏</a>
    ·
    <a href="https://www.linkedin.com/company/julep-ai" rel="dofollow">LinkedIn</a>
  </h3>
</div># **Changelog for 27 October 2023** ✨

- **Major Feature**: Introduced support for Gemini models in `litellm-config.yaml` ✨
- **Minor Feature**: Added environment configuration for Open Responses API ✨
- **Critical Fix**: Corrected cardinality violations in SQL queries across agents-api 🔧
- **Minor Fix**: Resolved documentation formatting issues in 21 files 🔧
- **Major Enhancement**: Refactored API calls to include developer ID for better tracking 📈
- **Minor Enhancement**: Improved Gunicorn worker configurability via environment variables 📈
- **Secondary Performance**: Integrated OpenAPI model and TyeSpecs for expanded functionality 🚀
- **Critical Breaking**: Replaced Postgraphile with Hasura for GraphQL services 💥
- **Other Breaking**: Updated Docker configurations to adhere to new deployment requirements 💥

# **Julep AI Changelog for 14 February 2025** ✨

- **Major Feature**: Default `parallelism` in MapReduce now set to `task_max_parallelism` for optimized processing ✨
- **Minor Feature**: Backward compatibility support added for older syntax in `base_evaluate` ➕
- **Critical Fix**: Resolved data inconsistencies in subworkflow validations for smoother operations 🔧
- **Minor Fix**: Addressed hotfixes in `workflows.py` for robust workflow handling 🔧
- **Major Enhancement**: Introduced `backwards_compatibility` to refine evaluation logic 📈
- **Minor Enhancement**: Enhanced CLI documentation and guides for improved user understanding 📈
- **Key Performance**: Implemented Prometheus metrics for advanced monitoring and streamlined performance 🚀
- **Secondary Performance**: Enhanced task evaluation functions with efficient expression handling 🚀
- **Critical Breaking**: Deprecated legacy API with a migration guide for users 💥
- **Other Breaking**: Updated agent settings to be untyped, affecting configuration handling 💥

# **Julep AI Changelog for 31 January 2025** ✨

- **Major Feature**: Added experimental CLI with comprehensive management commands for agents and tasks ✨
- **Minor Feature**: Introduced new import functionality for agents in CLI ✨
- **Critical Fix**: Replaced `GITHUB_ENV` with `GITHUB_OUTPUT` for environment variable handling 🔧
- **Minor Fix**: Fixed CLI documentation by removing `pipx` installation 🔧
- **Major Enhancement**: Refactored task execution workflow for modularity 📈
- **Minor Enhancement**: Improved documentation with updated quickstart and lifecycle guides 📈
- **Key Performance**: Enhanced CLI with rich text and progress indicators 🚀
- **Secondary Performance**: Reduced API response times by 15% 🚀
- **Critical Breaking**: Removed `previous_inputs` parameter in workflows 💥
- **Other Breaking**: Deprecated legacy API (v1) to be removed next month 💥