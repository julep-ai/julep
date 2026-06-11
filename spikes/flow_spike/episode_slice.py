from __future__ import annotations

from examples import episode_summary_flow as episode

from .core import cond, each, flow, think, tool

SUMMARIZER = episode.SUMMARIZER
ONE_LINER = episode.ONE_LINER

read_episode = tool(episode.read_episode)
write_summary_surfaces = tool(episode.write_summary_surfaces)
episode_found = episode.episode_found
not_found_status = episode.not_found_status
tally_summary_statuses = episode.tally_summary_statuses


@flow
def happy_path(source):
    summary = think(SUMMARIZER, source)
    merged = source | summary
    liner = think(ONE_LINER, merged)
    return write_summary_surfaces(merged | liner)


@flow
def summarize_one(episode_id):
    source = read_episode(episode_id)
    return cond(episode_found, source, then=happy_path, orelse=not_found_status)


BATCH = each(summarize_one, max_parallel=2, reducer=tally_summary_statuses)
