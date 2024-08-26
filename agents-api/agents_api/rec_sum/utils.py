###########
## Utils ##
###########


from typing import Any, Dict, List, TypeVar

_T2 = TypeVar("_T2")


class chatml:
    @staticmethod
    def make(content, role="system", name: _T2 = None, **_) -> Dict[str, _T2]:
        return {
            key: value
            for key, value in dict(role=role, name=name, content=content).items()
            if value is not None
        }

    @staticmethod
    def user(content, name=None) -> Any:
        return chatml.make(role="user", content=content, name=name)

    @staticmethod
    def assistant(content, name=None) -> Any:
        return chatml.make(role="assistant", content=content, name=name)

    @staticmethod
    def system(content, name=None) -> Any:
        return chatml.make(content, name=name)

    @staticmethod
    def thought(content, name=None) -> Any:
        return chatml.make(content, name="thought")

    @staticmethod
    def information(content) -> Any:
        return chatml.system(content, name="information")

    @staticmethod
    def summary(content) -> Any:
        return chatml.system(content, name="summary")

    @staticmethod
    def entities(content) -> Any:
        return chatml.system(content, name="entity")


def add_indices(list_of_dicts, idx_name="index") -> List[dict]:
    return [{idx_name: i, **msg} for i, msg in enumerate(list_of_dicts)]


def get_names_from_session(session) -> Dict[str, Any]:
    return {
        role: next(
            (msg.get("name", None) for msg in session if msg["role"] == role), None
        )
        for role in {"user", "assistant", "system"}
    }
