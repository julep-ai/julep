# Metadata Precedence in Julep

*****
> ### This docs site is currently under construction although this github README below should suffice for now.

![](https://i.giphy.com/vR1dPIYzQmkRzLZk2w.webp)
*****


In Julep, several objects can have `metadata` added to them:
- Agent
- User
- Session
- Doc
- Task
- Execution

When multiple objects with the same `metadata` field are present in a scope, the value takes the following precedence (from highest to lowest):

## In a session:
1. Session
2. User
3. Agent

## During a task execution:
1. Execution
2. Task
3. Agent

This precedence order ensures that more specific contexts (like a particular session or execution) can override more general settings, while still allowing for default values to be set at higher levels.