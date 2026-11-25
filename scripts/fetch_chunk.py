#!/usr/bin/env python3
"""Fetch EVM block+receipt chunks from public RPC and emit gzip JSON + manifest."""
import argparse
import gzip
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

MAX_CHUNK = 100


def call(url, method, params, timeout=30):
    payload = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    ).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.load(resp)
    if data.get("error"):
        raise RuntimeError(f"{method} error at {url}: {data['error']}")
    if "result" not in data:
        raise RuntimeError(f"{method} no result at {url}")
    return data["result"]


def rpc_call(urls, method, params):
    last = None
    for url in urls:
        for attempt in range(3):
            try:
                return call(url, method, params)
            except Exception as exc:  # noqa: BLE001 - failover on any transport/RPC error
                last = exc
                if attempt < 2:
                    time.sleep(1 + attempt)
    raise RuntimeError(f"all RPC endpoints failed for {method}: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", required=True)
    ap.add_argument("--first", type=int, required=True)
    ap.add_argument("--last", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="raw", choices=["raw", "ledger"])
    ap.add_argument("--rpc-urls", required=True)
    args = ap.parse_args()

    if not (0 <= args.first <= args.last and args.last - args.first + 1 <= MAX_CHUNK):
        sys.exit("bad range: need 0 <= first <= last, span <= 100")

    urls = [u for u in args.rpc_urls.split(",") if u]
    if not urls:
        sys.exit("no RPC urls")

    blocks = []
    for n in range(args.first, args.last + 1):
        hex_n = hex(n)
        block = rpc_call(urls, "eth_getBlockByNumber", [hex_n, True])
        receipts = rpc_call(urls, "eth_getBlockReceipts", [hex_n])
        if block is None:
            sys.exit(f"block {n} missing on all RPC endpoints")
        blocks.append({"block": block, "receipts": receipts or []})
        if n < args.last:
            time.sleep(2)

    doc = {
        "chain": args.chain,
        "first": args.first,
        "last": args.last,
        "mode": args.mode,
        "blocks": blocks,
    }
    raw = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode()
    blob = gzip.compress(raw, compresslevel=9)
    with open(args.out, "wb") as fh:
        fh.write(blob)

    manifest = {
        "first": args.first,
        "last": args.last,
        "block_count": len(blocks),
        "tx_count": sum(len(b["receipts"]) for b in blocks),
        "bytes": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "chain": args.chain,
        "mode": args.mode,
        "asset": os.path.basename(args.out),
    }
    with open(args.out + ".manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=2)
        fh.write("\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
