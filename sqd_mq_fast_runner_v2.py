#!/usr/bin/env python3
"""Continuation-safe entrypoint for the engineering-equivalent frozen BCLX test."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import sqd_mq_fast_runner as runner

m = runner.m


def extract_chain_complete(name: str, cfg: dict[str, Any], raw_dir: Path) -> dict[str, Any]:
    out = raw_dir / f'{name}_events.csv'
    fields = [
        'chain','block','timestamp','tx_hash','log_index','event','reserve','user',
        'on_behalf','counterparty','amount','collateral_asset','debt_asset'
    ]
    total = 0
    counts = defaultdict(int)
    session = runner.m.requests.Session()
    url = f"https://portal.sqd.dev/datasets/{cfg['slug']}/finalized-stream"
    with out.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        windows = 0
        for window_start in range(int(cfg['start']), int(cfg['end']) + 1, int(m.WINDOW_BLOCKS)):
            window_end = min(int(cfg['end']), window_start + int(m.WINDOW_BLOCKS) - 1)
            current = window_start
            continuations = 0
            while current <= window_end:
                payload = {
                    'type': 'evm',
                    'fromBlock': current,
                    'toBlock': window_end,
                    'fields': {
                        'block': {'number': True, 'timestamp': True},
                        'log': {
                            'address': True, 'topics': True, 'data': True,
                            'transactionHash': True, 'logIndex': True,
                        },
                    },
                    'logs': [{'address': [m.POOL], 'topic0': m.TOPICS}],
                }
                response = m.request_portal(session, url, payload)
                if response.status_code == 204:
                    break
                if response.status_code != 200:
                    raise RuntimeError(
                        f"{name} {current}-{window_end} HTTP {response.status_code}: {response.text[:500]}"
                    )
                blocks = m.parse_blocks(response.text)
                if not blocks:
                    break
                last = current - 1
                for block in blocks:
                    header = block.get('header') or {}
                    number = int(header.get('number', -1))
                    timestamp = int(header.get('timestamp', 0) or 0)
                    last = max(last, number)
                    for log in block.get('logs', []) or []:
                        row = m.decode_log(name, number, timestamp, log)
                        if row:
                            writer.writerow(row)
                            total += 1
                            counts[row['event']] += 1
                if last < current:
                    break
                current = last + 1
                continuations += 1
                if continuations > 5000:
                    raise RuntimeError(
                        f'{name}: continuation safety ceiling exceeded at {window_start}-{window_end}'
                    )
            windows += 1
            if windows % 5 == 0:
                print(
                    f'{name}: windows={windows}, events={total}, block={window_end}',
                    flush=True,
                )
    return {'chain': name, 'events': total, 'counts': dict(counts), 'file': str(out)}


m.extract_chain = extract_chain_complete

if __name__ == '__main__':
    runner.main()
