###########
## Utils ##
###########


class chatml:
    @staticmethod
    def make(content, role="system", name=None, **_):
        return {
            key: value
            for key, value in dict(role=role, name=name, content=content).items()
            if value is not None
        }

    @staticmethod
    def user(content, name=None):
        return chatml.make(role="user", content=content, name=name)

    @staticmethod
    def assistant(content, name=None):
        return chatml.make(role="assistant", content=content, name=name)

    @staticmethod
    def system(content, name=None):
        return chatml.make(content, name=name)

    @staticmethod
    def thought(content, name=None):
        return chatml.make(content, name="thought")

    @staticmethod
    def information(content):
        return chatml.system(content, name="information")

    @staticmethod
    def summary(content):
        return chatml.system(content, name="summary")

    @staticmethod
    def entities(content):
        return chatml.system(content, name="entity")


def add_indices(list_of_dicts, idx_name="index"):
    return [{idx_name: i, **msg} for i, msg in enumerate(list_of_dicts)]


def get_names_from_session(session):
    return {
        role: next(
            (msg.get("name", None) for msg in session if msg["role"] == role), None
        )
        for role in {"user", "assistant", "system"}
    }
