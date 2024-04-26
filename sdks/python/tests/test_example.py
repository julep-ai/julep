from ward import test

from .fixtures import client, TEST_MODEL


@test("simple agent example")
def _(client=client):
    name = "Jessica"
    about = """\
    Your name is Jessica.
    You are a stuck up Cali teenager.
    You basically complain about everything.
    Showing rebellion is an evolutionary necessity for you."""

    instructions = [
        "Answer with disinterest and complete irreverence to absolutely everything.",
        "Don't write emotions.",
        "Keep your answers short.",
    ]

    default_settings = dict(
        temperature=1.5,  # increases variability in responses
        min_p=0.01,  # filters extremely improbable tokens
        repetition_penalty=1.05,  # just slightly high to avoid repetition
    )

    agent = client.agents.create(
        name=name,
        about=about,
        model=TEST_MODEL,
        instructions=instructions,
        default_settings=default_settings,
    )

    user = client.users.create(
        name="John Wick",
        about="Baba Yaga",
    )

    session = client.sessions.create(
        agent_id=agent.id,  # from above
        user_id=user.id,
        # Situation is the entrypoint of the session to set
        #  the starting context for the agent for this conversation.
        situation="You are chatting with a random stranger from the Internet.",
    )

    user_input = "hi!"

    message = dict(role="user", content=user_input)

    result = client.sessions.chat(
        session_id=session.id,
        messages=[message],
        max_tokens=200,  # and any other generation parameters
        stream=False,
        #
        # Memory options
        remember=True,  # "remember" / form memories about this user from the messages
        recall=True,  # "recall" / fetch past memories about this user.
    )

    [response_msg, *_] = result.response[0]
    assert hasattr(response_msg, "role")
    assert hasattr(response_msg, "content")

    # Clean up
    client.sessions.delete(session.id)
    client.users.delete(user.id)
    client.agents.delete(agent.id)
