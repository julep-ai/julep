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
    about="You are a research agent designed to handle research inquiries.",
    model="claude-3.5-sonnet",
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
