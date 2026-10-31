"""Run the small regression set against the local SSE API."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx


async def run_one(client: httpx.AsyncClient, base_url: str, item: dict) -> dict:
    result = None
    async with client.stream(
        "POST", f"{base_url}/api/query", json={"query": item["question"]}
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line.startswith("data: "):
                continue
            payload = json.loads(line[6:])
            if "result" in payload:
                result = payload["result"]
            if "error" in payload:
                return {"id": item["id"], "ok": False, "error": payload["error"]}
    keys = set(result[0].keys()) if result else set()
    expected_keys = set(item["expected"].split(","))
    return {
        "id": item["id"],
        "ok": bool(result) and expected_keys.issubset(keys),
        "keys": sorted(keys),
    }


async def main(base_url: str, limit: int | None) -> int:
    items = json.loads(Path(__file__).with_name("questions.json").read_text())
    items = items[:limit] if limit else items
    async with httpx.AsyncClient(timeout=120) as client:
        results = [await run_one(client, base_url, item) for item in items]
    for result in results:
        print(json.dumps(result, ensure_ascii=False))
    passed = sum(result["ok"] for result in results)
    print(f"passed={passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(main(args.base_url, args.limit)))
