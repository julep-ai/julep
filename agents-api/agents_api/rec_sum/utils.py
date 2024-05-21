###########
## Utils ##
###########

class chatml:
    make = lambda content, role="system", name=None, **_: {
        key: value
        for key, value in dict(role=role, name=name, content=content).items()
        if value is not None
    }
    
    user = lambda content, name=None: chatml.make(role="user", content=content, name=name)
    assistant = lambda content, name=None: chatml.make(
        role="assistant", content=content, name=name
    )
    system = lambda content, name=None: chatml.make(content, name=name)
    thought = lambda content, name=None: chatml.make(content, name="thought")
    information = lambda content: chatml.system(content, name="information")
    summary = lambda content: chatml.system(content, name="summary")
    entities = lambda content: chatml.system(content, name="entity")



add_indices = lambda list_of_dicts, idx_name="index": [
    {idx_name: i, **msg} for i, msg in enumerate(list_of_dicts)
]



get_names_from_session = lambda session: {
    role: next((
        msg.get("name", None)
        for msg in session
        if msg["role"] == role
    ), None)
    for role in {"user", "assistant", "system"}
}
