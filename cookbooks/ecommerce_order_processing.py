import os
import uuid
import yaml
from julep import Client

AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

api_key = os.getenv("API_KEY")
client = Client(api_key=api_key, environment="dev")

name = "E-commerce Order Processor"
about = "Automates order processing, inventory management, and shipment tracking."
default_settings = {
    "temperature": 0.7,
    "top_p": 1,
    "min_p": 0.01,
    "presence_penalty": 0,
    "frequency_penalty": 0,
    "length_penalty": 1.0,
    "max_tokens": 150,
}

agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name=name,
    about=about,
    model="gpt-4o",
)

task_def = yaml.safe_load("""
name: E-commerce Order Processing

input_schema:
  type: object
  properties:
    customer_order:
      type: object
      properties:
        order_id:
          type: string
        items:
          type: array
          items:
            type: string
        customer_location:
          type: string
        payment_status:
          type: string
      required: ["order_id", "items", "customer_location", "payment_status"]

tools:
- name: inventory
  type: integration
  integration:
    provider: inventory_management

- name: shipping
  type: integration
  integration:
    provider: shipment_tracking

- name: notifications
  type: integration
  integration:
    provider: notification_system

main:
- over: inputs[0].items
  map:
    tool: inventory
    arguments:
      item: _

- map:
    tool: shipping
    arguments:
      location: inputs[0].customer_location

- evaluate:
    zipped: "list(zip(inputs[0].items, [output['inventory_status'] for output in outputs[0]], [output['shipment_status'] for output in outputs[1]]))"

- over: _['zipped']
  parallelism: 3
  map:
    prompt:
    - role: system
      content: >-
        Process order {{inputs[0]['order_id']}} for items "{{_[0]}}":
        - Inventory status: "{{_[1]}}"
        - Shipment status: "{{_[2]}}"
        Send notifications if needed.
    unwrap: true
""")


task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

execution = client.executions.create(
    task_id=task.id,
    input={
         "customer_order": {
             "order_id": "ORD12345",
             "items": ["Laptop", "Mouse", "Keyboard"],
             "customer_location": "New York",
             "payment_status": "Paid"
         }
    }
)

print(f"Execution ID: {execution.id}")

execution = client.executions.get(execution.id)
print("Execution Output:")
print(execution.output)

print("Execution Steps:")
for item in client.executions.transitions.list(execution_id=execution.id).items:
    print(item)

print("Streaming Execution Steps:")
for step in client.executions.transitions.stream(execution_id=execution.id):
    print(step)
