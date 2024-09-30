import Julep from '@julep/sdk';

// 🔑 Initialize the Julep client
const client = new Julep({
  apiKey: 'your_api_key',
  environment: 'production', // or 'dev' | 'local_multi_tenant' | 'local'
});

async function main() {
  /*
   * 🤖 Agent 🤖
   */

  // Create a research agent
  const agent = await client.agents.createOrUpdate('dad00000-0000-4000-a000-000000000000', {
    name: 'Research Agent',
    about: 'You are a research agent designed to handle research inquiries.',
    model: 'claude-3.5-sonnet',
  });

  // 🔍 Add a web search tool to the agent
  await client.agents.tools.create(agent.id, {
    name: 'web_search',
    description: 'Use this tool to research inquiries.',
    integration: {
      provider: 'brave',
      method: 'search',
      setup: {
        api_key: 'your_brave_api_key',
      },
    },
  });

  /*
   * 💬 Chat 💬
   */

  // Start an interactive chat session with the agent
  const session = await client.sessions.create({
    agentId: agent.id,
    contextOverflow: 'adaptive', /* 🧠 Julep will dynamically compute the context window if needed */
  });

  // 🔄 Chat loop
  const readline = require('readline').createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  const askQuestion = (query: string) => new Promise((resolve) => readline.question(query, resolve));

  while (true) {
    const userInput = await askQuestion('You: ');
    if (userInput === 'exit') break;

    const response = await client.sessions.chat(session.id, {
      message: userInput,
    });

    console.log('Agent: ', response.choices[0].message.content);
  }

  readline.close();

  /*
   * 📋 Task 📋
   */

  // Create a recurring research task for the agent
  const task = await client.tasks.create(agent.id, {
    name: 'Research Task',
    description: 'Research the given topic every 24 hours.',
    /* 🛠️ Task specific tools */
    tools: [
      {
        name: 'send_email',
        description: 'Send an email to the user with the results.',
        apiCall: {
          method: 'post',
          url: 'https://api.sendgrid.com/v3/mail/send',
          headers: { Authorization: 'Bearer YOUR_SENDGRID_API_KEY' },
        },
      },
    ],
    /* 🔢 Task main steps */
    main: [
      // Step 1: Research the topic
      {
        prompt: "Look up topic '{{_.topic}}' and summarize the results.",
        tools: [{ ref: { name: 'web_search' } }], /* 🔍 Use the web search tool from the agent */
        unwrap: true,
      },
      // Step 2: Send email with research results
      {
        tool: 'send_email',
        arguments: {
          subject: 'Research Results',
          body: "'Here are the research results for today: ' + _.content",
          to: 'inputs[0].email', // Reference the email from the user's input
        },
      },
      // Step 3: Wait for 24 hours before repeating
      { sleep: 24 * 60 * 60 },
    ],
  });

  // 🚀 Start the recurring task
  await client.executions.create(task.id, { input: { topic: 'TypeScript' } });

  /*
   * 🔁 This will run the task every 24 hours,
   *    research for the topic "TypeScript", and
   *    send the results to the user's email
   */
}

main().catch(console.error);