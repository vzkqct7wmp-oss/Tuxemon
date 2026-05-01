# SPDX-License-Identifier: GPL-3.0
import json

from tuxemon.hermes.trace import JsonlTraceWriter


def test_trace_writer_appends_jsonl(tmp_path):
    path = tmp_path / "trace.jsonl"
    writer = JsonlTraceWriter(path)

    writer.write("event.one", {"value": 1})
    writer.write("event.two", {"value": 2})

    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [row["sequence"] for row in rows] == [1, 2]
    assert rows[0]["event_type"] == "event.one"
