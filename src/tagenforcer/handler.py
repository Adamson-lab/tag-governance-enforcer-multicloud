"""Thin cloud entry points. They parse provider events, call the neutral engine, and hand plans to injected writers.
Maturity: prototype. Not yet exercised against live clouds; API writers are injected so tests never touch a cloud."""
import json, os
from .adapters import from_aws_config, from_azure_graph, from_gcp_asset
from .engine import evaluate, load_standard

_STD = None


def _std():
    global _STD
    _STD = _STD or load_standard(os.environ.get("STANDARD_PATH"))
    return _STD


def decide(resource, exemptions=None):
    return evaluate(resource, _std(), exemptions=exemptions)


def aws_handler(event, context=None, sink=print):
    for rec in event.get("Records", []):
        body = json.loads(rec["body"])
        item = (body.get("detail") or {}).get("configurationItem") or body
        sink(decide(from_aws_config(item)))


def azure_handler(event, sink=print):
    sink(decide(from_azure_graph(event)))


def gcp_handler(event, sink=print):
    sink(decide(from_gcp_asset(event.get("asset", event))))
