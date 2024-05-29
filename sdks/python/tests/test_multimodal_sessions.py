from ward import test


from .fixtures import (
    client,
    test_multimodal_session,
)

first_turn_image_message = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": "https://imgs.xkcd.com/comics/local_group_2x.png"},
            }
        ],
    }
]
second_turn_text_message = [
    {"role": "user", "content": "who do you think the author of this image is?"}
]


@test("sessions: multimodal sessions.chat")
def _(client=client, session=test_multimodal_session):
    client.sessions.chat(
        session_id=session.id,
        messages=first_turn_image_message,
    )

    client.sessions.chat(
        session_id=session.id,
        messages=second_turn_text_message,
    )

    history = client.sessions.history(
        session_id=session.id,
    )

    assert len(history) > 0
