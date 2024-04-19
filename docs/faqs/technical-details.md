# Technical Details

1. **What powers agents on the Julep platform?**
   Julep agents are built on top of Large Language Models (LLMs) with added layers for memory management, planning, and long-running execution capabilities.
<br />
2. **What languages and frameworks are supported?**
   Currently, we maintain official SDKs in python and node.js. We also have a langchain integration. Support for additional runtimes is planned with go, java, and ruby clients coming soon.

   The API itself is language-agnostic, providing RESTful endpoints that can be consumed by any modern programming language or framework that supports HTTP requests.
<br />
3. **How can I integrate Julep AI with my existing data sources?**
   You can integrate with external data sources through API calls, webhooks, and function calls as the part of the agent configurations. Support for adding vector indices from Weaviate Cloud and Pinecone is planned.
<br />
4. **How can I do version control for agent development?**
   Planned. Not supported at the moment.
<br />
5. **How does the platform ensure the security?**
   We follows industry best practices on encryption, deployments and data storage. We also do regular audits to ensure the integrity of its infrastructure. Compliance and certifications are planned to provide enterprise customers more trust and transparency.
