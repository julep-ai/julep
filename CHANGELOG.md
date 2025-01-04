<div align="center" id="top">
  <img src="https://socialify.git.ci/julep-ai/julep/image?description=1&descriptionEditable=Rapidly%20build%20AI%20workflows%20and%20agents&font=Source%20Code%20Pro&logo=https%3A%2F%2Fraw.githubusercontent.com%2Fjulep-ai%2Fjulep%2Fdev%2F.github%2Fjulep-logo.svg&owner=1&forks=1&pattern=Solid&stargazers=1&theme=Auto" alt="julep" width="640" height="320" />
 </div>
 
 <p align="center">
   <br />
   <a href="https://docs.julep.ai" rel="dofollow">Explore Docs (wip)</a>
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

# **Julep AI Changelog for 12 December 2024** ✨

Welcome to the latest Julep AI changelog! We’ve been busy refining and enhancing our systems to ensure a seamless experience for you. Dive into the exciting updates below!

## **Features** ✨

- **Prometheus Summary for Cozo Queries**:
  - A **Summary** metric has been introduced for query latency in `query_metrics_update()` within `counters.py`.
  - The `increase_counter()` function has been renamed to `query_metrics_update()` across multiple files for consistency.
  - **Why**: To improve performance monitoring and streamline code.
  - **Impact**: Enhanced visibility into query performance and simplified codebase.

- **MMR Search and Configurable Parameters**:
  - Introduced MMR search with configurable parameters, including `mmr_strength`, in `gather_messages.py`.
  - Updated documentation and OpenAPI spec with new search parameters.
  - **Why**: To offer flexible and powerful search capabilities.
  - **Impact**: Users can now tailor search functionalities to better meet their needs.

- **In-Memory Rate Limiter**:
  - Added an in-memory rate limiter to `transition_step` using `RateLimiter` from `utils.py`.
  - **Why**: To prevent system overload and ensure stable performance.
  - **Impact**: Improved resource management and system reliability.

## **Fixes** 🔧

- **GitHub Action Workflow for Changelog Generation**:
  - Fixed issues in the GitHub Action workflow by renaming and reconfiguring the workflow.
  - **Why**: To ensure accurate changelog generation and avoid JSON structure errors.
  - **Impact**: Streamlined changelog updates and enhanced workflow clarity.

- **Grafana Dashboard and Temporal Metrics Port**:
  - Resolved provisioning issues in Grafana dashboards and set a static port for Temporal metrics.
  - **Why**: To maintain consistent monitoring and avoid configuration errors.
  - **Impact**: Reliable dashboard visualization and metrics tracking.

## **Improvements** 📈

- **Metrics Refactoring**:
  - Centralized initialization of `Counter`, `Summary`, and `Histogram` metrics in `counters.py`.
  - Updated `query_metrics_update` to handle both sync and async functions.
  - **Why**: To simplify metric management and enhance functionality.
  - **Impact**: Improved performance tracking and easier maintenance.

- **Async Support in Spider API**:
  - Added async support and new methods to the Spider API, along with code refactoring.
  - **Why**: To enhance the efficiency and flexibility of web crawling capabilities.
  - **Impact**: Faster and more reliable API operations.

## **Performance Enhancements** 🚀

- **Integration with New Cozo RocksDB**:
  - Updated configurations to integrate the latest Cozo with RocksDB, enhancing the engine and settings.
  - **Why**: To leverage new features and improved performance of the Cozo database.
  - **Impact**: Enhanced data processing speed and system robustness.

- **Default Worker Settings**:
  - Set default Temporal worker settings for improved concurrency and activity limits.
  - **Why**: To optimize task handling and resource allocation.
  - **Impact**: More efficient workflow management and reduced latency.

## **Breaking Changes** 💥

- **Deprecated Index References**:
  - Removed unused index references from queries across multiple files to handle undefined indices.
  - **Why**: To clean up the codebase and avoid potential errors.
  - **Impact**: May require updates to dependent queries or scripts.

## **Notes** 📝

- **Attention Developers**: Please ensure you update your configurations and dependencies to align with the latest changes.
- **Known Issues**: Some users might experience temporary delays in search functionalities as new indices are created.

Thank you for using Julep AI! We’re committed to delivering the best possible experience and appreciate your support and feedback. Stay tuned for more updates!

## Contributors

Thank you to all our contributors who helped make this release possible!

- [Dmitry Paramonov](https://github.com/whiterabbit1983) 🐇
- [Ahmad Haidar](https://github.com/Ahmad-mtos) 🚀
- [Diwank Tomar](https://github.com/creatorrr) 🌟
- [Vedant Sahai](https://github.com/Vedantsahai18) 🔥
- [Hamada Salhab](https://github.com/HamadaSalhab) 💡