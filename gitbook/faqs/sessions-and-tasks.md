# Sessions and Tasks

1. **What is a 'Session' in Julep AI?**\
   A Session is a real-time interaction between a user and an AI agent, structured as a conversation with request-response exchanges, often resembling a chat interface.\

2. **How do I start a Session with an agent?**\
   You can initiate a Session by selecting an agent and a user within the platform, which creates a unique session\_id used to track the conversation.\

3. **What is a 'Task' in Julep AI, and how is it different from a Session?**\
   A Task is a defined operation with multiple steps and objectives, intended to run over a longer duration than a Session. Tasks are like state machines that handle complex, multi-step processes.\

4. **Can Sessions use the tools defined in an agent's configuration?**\
   Yes, but a restricted subset only in order to maintain speed and reliability. Sessions can execute instant tools such as document lookups and API calls in real-time, using the results to inform responses within the conversation. They can also _queue_ longer running operations and tasks.\

5. **How do agents manage memory within Sessions?**\
   During Sessions, agents automatically pull relevant memories to provide contextually appropriate responses and to maintain continuity in the interaction.\

6. **What are Scheduled Tasks and how do they work?**\
   Scheduled Tasks are Tasks that are set to run at specific times or intervals. They are configured to trigger automatically, based on the parameters set by the user.\

7. **How can I track the progress of a Task?**\
   Each Task run is associated with a unique run\_id, which you can use to monitor the state transitions and overall progress through the platform’s dashboard.\

8. **Are there limits on the length or complexity of a Session or Task?**\
   Sessions are designed for shorter interactions. Tasks, however, are better suited for operations with multiple steps and can run for extended periods.\

9. **How do I end a Session or Task?**\
   Sessions typically end when the user's immediate needs are met or when manually concluded by the user. Tasks end when the objective is achieved or if the state machine reaches a terminal state.
