from ward import test

from tests.fixtures import make_request


@test("model: list sessions")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/sessions",
    )

    assert response.status_code == 200
    response = response.json()
    sessions = response["items"]

    assert isinstance(sessions, list)
    assert len(sessions) > 0


@test("model: list sessions with metadata filter")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/sessions",
        params={
            "metadata_filter": {"test": "test"},
        },
    )

    assert response.status_code == 200
    response = response.json()
    sessions = response["items"]

    assert isinstance(sessions, list)
    assert len(sessions) > 0
