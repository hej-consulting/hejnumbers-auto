"""Kleiner Client für die Buffer GraphQL API (https://developers.buffer.com)."""
import json
import os
import requests

API = "https://api.buffer.com"


class Enum(str):
    """Wert, der in GraphQL ohne Anführungszeichen geschrieben wird (z. B. reel, automatic)."""


def gql_literal(v):
    if isinstance(v, Enum):
        return str(v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(gql_literal(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {gql_literal(x)}" for k, x in v.items() if x is not None) + "}"
    raise TypeError(type(v))


def query(q):
    r = requests.post(API, headers={"Authorization": "Bearer " + os.environ["BUFFER_API_KEY"],
                                    "Content-Type": "application/json"},
                      json={"query": q}, timeout=60)
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):
        raise RuntimeError(json.dumps(data["errors"], indent=1))
    return data["data"]


def create_post(inp):
    q = """mutation { createPost(input: %s) {
      ... on PostActionSuccess { post { id dueAt } }
      ... on MutationError { message }
    } }""" % gql_literal(inp)
    res = query(q)["createPost"]
    if "message" in res and "post" not in res:
        raise RuntimeError("Buffer: " + res["message"])
    return res["post"]


def list_channels():
    out = []
    for org in query("query { account { organizations { id name } } }")["account"]["organizations"]:
        chans = query('query { channels(input: {organizationId: %s}) { id name displayName service } }'
                      % json.dumps(org["id"]))["channels"]
        out.append((org, chans))
    return out
