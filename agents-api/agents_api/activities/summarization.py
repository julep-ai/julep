#!/usr/bin/env python3


import pandas as pd
from beartype import beartype
from temporalio import activity

# from agents_api.models.entry.entries_summarization import (
#     entries_summarization_query,
#     get_toplevel_entries_query,
# )


# TODO: remove stubs
def entries_summarization_query(*args, **kwargs):
    return pd.DataFrame()


def get_toplevel_entries_query(*args, **kwargs):
    return pd.DataFrame()


@activity.defn
@beartype
async def summarization(session_id: str) -> None:
    raise NotImplementedError()
    # session_id = UUID(session_id)
    # entries = []
    # entities_entry_ids = []
    # for _, row in get_toplevel_entries_query(session_id=session_id).iterrows():
    #     if row["role"] == "system" and row.get("name") == "entities":
    #         entities_entry_ids.append(UUID(row["entry_id"], version=4))
    #     else:
    #         entries.append(row)

    # assert len(entries) > 0, "no need to summarize on empty entries list"

    # summarized, entities = await asyncio.gather(
    #     summarize_messages(entries, model=summarization_model_name),
    #     get_entities(entries, model=summarization_model_name),
    # )
    # trimmed_messages = await trim_messages(summarized, model=summarization_model_name)
    # ts_delta = (entries[1]["timestamp"] - entries[0]["timestamp"]) / 2
    # new_entities_entry = Entry(
    #     session_id=session_id,
    #     source="summarizer",
    #     role="system",
    #     name="entities",
    #     content=entities["content"],
    #     timestamp=entries[0]["timestamp"] + ts_delta,
    # )

    # entries_summarization_query(
    #     session_id=session_id,
    #     new_entry=new_entities_entry,
    #     old_entry_ids=entities_entry_ids,
    # )

    # trimmed_map = {
    #     m["index"]: m["content"] for m in trimmed_messages if m.get("index") is not None
    # }

    # for idx, msg in enumerate(summarized):
    #     new_entry = Entry(
    #         session_id=session_id,
    #         source="summarizer",
    #         role="system",
    #         name="information",
    #         content=trimmed_map.get(idx, msg["content"]),
    #         timestamp=entries[-1]["timestamp"] + 0.01,
    #     )

    #     entries_summarization_query(
    #         session_id=session_id,
    #         new_entry=new_entry,
    #         old_entry_ids=[
    #             UUID(entries[idx - 1]["entry_id"], version=4)
    #             for idx in msg["summarizes"]
    #         ],
    #     )
