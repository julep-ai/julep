# Multi-Agent Sessions in Julep

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


Julep supports different types of sessions based on the number of agents and users involved. This flexibility allows for complex interactions and use cases.

## Types of Sessions

1. Single agent:
   - No user
   - Single user
   - Multiple users

2. Multiple agents:
   - No user
   - Single user
   - Multiple users

## Behavior in Multi-Agent/User Sessions

### User Behavior

- **No user**: 
  - No user data is retrieved
  - (Upcoming) Memories are not mined from the session

- **One or more users**:
  - Docs, metadata, memories, etc. are retrieved for all users in the session
  - Messages can be added for each user by referencing them by name in the `ChatML` messages
  - (Upcoming) Memories mined in the background are added to the corresponding user's scope

### Agent Behavior

- **One agent**: 
  - Works as expected

- **Multiple agents**: 
  - When a message is received by the session, each agent is called one after another in the order they were defined in the session
  - You can specify which `agent` to use in a request, in which case, only that agent will be used

This multi-agent/user capability allows for sophisticated scenarios such as:
- Collaborative problem-solving with multiple AI agents
- Group conversations with multiple users and agents
- Specialized agents working together on complex tasks

By supporting these various configurations, Julep provides a flexible framework for building diverse and powerful AI applications.