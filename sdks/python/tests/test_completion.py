from ward import test

from .fixtures import async_client, client, TEST_MODEL


@test("test completion")
def _(client=client):
    r = client.completions.create(
        model=TEST_MODEL,
        prompt="Once upon a time",
        min_p=0.1,
        temperature=0.7,
    )

    assert r.choices[0].text


@test("async test completions")
async def _(async_client=async_client):
    r = await async_client.completions.create(
        model=TEST_MODEL,
        prompt="Once upon a time",
        min_p=0.1,
        temperature=0.7,
    )

    assert r.choices[0].text


@test("test chat completion")
def _(client=client):
    r = client.chat.completions.create(
        model=TEST_MODEL,
        messages=[dict(role="system", content="Hello!")],
        min_p=0.1,
        temperature=0.7,
    )

    assert r.choices[0].message.content


@test("async test chat completion")
async def _(async_client=async_client):
    r = await async_client.chat.completions.create(
        model=TEST_MODEL,
        messages=[dict(role="system", content="Hello!")],
        min_p=0.1,
        temperature=0.7,
    )

    assert r.choices[0].message.content
