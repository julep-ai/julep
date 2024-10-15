# Document Management and Search Cookbook
#
# Plan:
# 1. Import necessary libraries and set up the Julep client
# 2. Create an agent for document management
# 3. Define a task for document upload and indexing
# 4. Define a task for document search
# 5. Create sample documents
# 6. Execute the document upload and indexing task
# 7. Execute the document search task
# 8. Display the search results

# UNDER CONSTRUCTION - YAML is working but the flow is not correct yet

import uuid
import yaml,time
from julep import Client

# Global UUID is generated for agent and tasks
AGENT_UUID = uuid.uuid4()
UPLOAD_TASK_UUID = uuid.uuid4()
SEARCH_TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = ""  # Your API key here
client = Client(api_key=api_key, environment="dev")

# Creating an agent for document management
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name="Document Manager",
    about="An AI agent specialized in document management and search.",
    model="gpt-4o",
)

# Defining a task for document upload and indexing
upload_task_def = yaml.safe_load(f"""
name: Document Upload and Indexing

input_schema:
  type: object
  properties:
    documents:
      type: array
      items:
        type: object
        properties:
          tile:  
            type: string
          content: 
            type: string
          metadata:
            type: object
                                 
tools:
- name: document_create
  system:
    resource: agent
    subresource: doc
    operation: create                             

main:
- over: inputs[0].documents
  map:
    tool: document_create
    arguments:
      agent_id: "'{agent.id}'"
      data:
        title: _.title
        content: _.content
        metadata: _.metadata
                                 
- prompt:
  - role: system
    content: >-
      You have successfully uploaded and indexed {{len(outputs[0])}} documents.
      Provide a summary of the uploaded documents.
""")

# Creating the upload task
upload_task = client.tasks.create_or_update(
    task_id=UPLOAD_TASK_UUID,
    agent_id=AGENT_UUID,
    **upload_task_def
)

# Defining a task for document search
search_task_def = yaml.safe_load(f"""
name: Document Search

input_schema:
  type: object
  properties:
    query:
      type: string
    filters:
      type: object

tools:
- name: document_search
  system:
    resource: agent
    subresource: doc
    operation: search
                                     
main:
- tool: document_search
  arguments:
    agent_id: "'{agent.id}'"
    text: inputs[0].query
    metadata_filters: inputs[0].filters

- prompt:
  - role: system
    content: >-
      Based on the search results, provide a summary of the most relevant documents found.
      Search query: {{inputs[0].query}}
      Number of results: {{len(outputs[0])}}
      
      Results:
      {{outputs[0]}}
  unwrap: true
""")

# Creating the search task
search_task = client.tasks.create_or_update(
    task_id=SEARCH_TASK_UUID,
    agent_id=AGENT_UUID,
    **search_task_def
)

# Sample documents
sample_documents = [
    {
        "title": "The Impact of Technology on Society",
        "content": "Artificial Intelligence (AI) is revolutionizing various industries, including healthcare, finance, and transportation.",
        "metadata": {"category": "technology", "author": "John Doe"}
    },
    {
        "title": "Climate Change and Global Warming",
        "content": "Climate change is a pressing global issue that requires immediate action from governments, businesses, and individuals.",
        "metadata": {"category": "environment", "author": "Jane Smith"}
    },
    {
        "title": "Remote Work and Digital Transformation",
        "content": "The COVID-19 pandemic has accelerated the adoption of remote work and digital technologies across many organizations.",
        "metadata": {"category": "business", "author": "Alice Johnson"}
    }
]

# Execute the document upload and indexing task
upload_execution = client.executions.create(
    task_id=UPLOAD_TASK_UUID,
    input={"documents": sample_documents}
)

print("Uploading and indexing documents...")
# Wait for the execution to complete
time.sleep(5)
upload_result = client.executions.get(upload_execution.id)
upload_response = client.executions.transitions.list(upload_execution.id).items[0].output
print("Upload Result:")
print(upload_response)

# Execute the document search task
search_execution = client.executions.create(
    task_id=SEARCH_TASK_UUID,
    input={
        "query": "impact of technology on society",
        "filters": {"category": "technology"}
    }
)

print("\nSearching documents...")
# Wait for the execution to complete
time.sleep(5)
search_result = client.executions.get(search_execution.id)
# Display the search results
print("\nSearch Results:")
for transition in client.executions.transitions.list(execution_id=search_execution.id).items:
    if transition.type == "tool_call" and transition.tool == "document_search":
        for doc in transition.output:
            print(f"- {doc['content']} (Score: {doc['score']})")

print("\nSearch Summary:")
search_response = client.executions.transitions.list(search_result.id).items[0].output
print(search_response)