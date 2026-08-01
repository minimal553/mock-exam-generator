#!/usr/bin/env python3
"""Memory-safe per-chain extraction for the frozen BCLX M→Q test."""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import sqd_mq_fast_runner_v2 as transport

m = transport.m


def has_future(values: list[int] | None, timestamp: int, days: int) -> bool:
    if not values:
        return False
    arr = np.asarray(values, dtype=np.int64)
    index = int(np.searchsorted(arr, timestamp, side='right'))
    return index < len(arr) and int(arr[index]) <= timestamp + days * 86400


def build_streaming_cohort(event_file: Path, assets: dict[str, dict]) -> pd.DataFrame:
    stable = {address for address, meta in assets.items() if meta.get('stable')}
    symbols = {address: meta.get('symbol', 'UNKNOWN') for address, meta in assets.items()}

    borrows: list[dict] = []
    borrow_keys: dict[tuple[str, str], list[int]] = defaultdict(list)
    flash_transactions: set[str] = set()
    repays: dict[tuple[str, str], list[int]] = defaultdict(list)
    liquidations: dict[str, list[int]] = defaultdict(list)
    candidate_withdrawals: dict[tuple[str, str], list[int]] = defaultdict(list)
    candidate_keys: set[tuple[str, str]] = set()

    with event_file.open('r', newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            event = row.get('event', '')
            tx_hash = row.get('tx_hash', '').lower()
            reserve = row.get('reserve', '').lower()
            user = row.get('user', '').lower()
            on_behalf = row.get('on_behalf', '').lower()
            timestamp = int(row.get('timestamp') or 0)
            log_index = int(row.get('log_index') or 0)

            if event == 'Borrow' and reserve in stable:
                record = {
                    'chain': row.get('chain', ''),
                    'block': int(row.get('block') or 0),
                    'timestamp': timestamp,
                    'tx_hash': tx_hash,
                    'log_index': log_index,
                    'reserve': reserve,
                    'asset_symbol': symbols.get(reserve, 'UNKNOWN'),
                    'on_behalf': on_behalf,
                    'amount': row.get('amount', '0'),
                    'candidate': False,
                    'candidate_reserve': '',
                    'candidate_symbol': '',
                }
                index = len(borrows)
                borrows.append(record)
                borrow_keys[(tx_hash, on_behalf)].append(index)

            elif event == 'Supply' and reserve and reserve not in stable:
                for index in borrow_keys.get((tx_hash, on_behalf), []):
                    record = borrows[index]
                    if log_index > int(record['log_index']) and not record['candidate']:
                        record['candidate'] = True
                        record['candidate_reserve'] = reserve
                        record['candidate_symbol'] = symbols.get(reserve, 'UNKNOWN')
                        candidate_keys.add((on_behalf, reserve))

            elif event == 'FlashLoan':
                flash_transactions.add(tx_hash)

            elif event == 'Repay' and reserve in stable:
                repays[(on_behalf, reserve)].append(timestamp)

            elif event == 'LiquidationCall':
                liquidations[on_behalf].append(timestamp)

            elif event == 'Withdraw' and (on_behalf, reserve) in candidate_keys:
                candidate_withdrawals[(on_behalf, reserve)].append(timestamp)

    if not borrows:
        return pd.DataFrame()

    for record in borrows:
        if record['tx_hash'] in flash_transactions:
            record['candidate'] = False
            record['candidate_reserve'] = ''
            record['candidate_symbol'] = ''

    for values in repays.values():
        values.sort()
    for values in liquidations.values():
        values.sort()
    for values in candidate_withdrawals.values():
        values.sort()

    borrows.sort(key=lambda x: (x['on_behalf'], x['timestamp'], x['log_index']))
    prior_count: dict[str, int] = defaultdict(int)
    cutoff_seconds = int(m.CANDIDATE_CUTOFF.timestamp())
    kept = []
    for borrow_id, record in enumerate(borrows):
        user = record['on_behalf']
        record['borrow_id'] = borrow_id
        record['prior_borrows'] = prior_count[user]
        prior_count[user] += 1
        record['year'] = pd.to_datetime(record['timestamp'], unit='s', utc=True).year
        record['date'] = pd.to_datetime(record['timestamp'], unit='s', utc=True)
        try:
            record['log_amount'] = float(np.log1p(float(record['amount'])))
        except (ValueError, OverflowError):
            record['log_amount'] = float('nan')
        if int(record['timestamp']) > cutoff_seconds:
            continue
        for days in m.LABEL_DAYS:
            repay = has_future(repays.get((user, record['reserve'])), int(record['timestamp']), days)
            liquid = has_future(liquidations.get(user), int(record['timestamp']), days)
            withdrawal = bool(record['candidate']) and has_future(
                candidate_withdrawals.get((user, record['candidate_reserve'])),
                int(record['timestamp']),
                days,
            )
            record[f'repay{days}'] = repay
            record[f'liquid{days}'] = liquid
            record[f'withdraw_candidate{days}'] = withdrawal
            record[f'delever{days}'] = repay or liquid
        kept.append(record)
    return pd.DataFrame(kept)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chain', required=True, choices=sorted(m.CHAINS))
    parser.add_argument('--out', required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = out / 'raw'
    raw.mkdir(exist_ok=True)
    config = m.CHAINS[args.chain]
    assets = m.fetch_asset_map(args.chain, config['address_file'])
    extraction = transport.extract_chain_complete(args.chain, config, raw)
    cohort = build_streaming_cohort(raw / f'{args.chain}_events.csv', assets)
    if cohort.empty:
        raise RuntimeError(f'No stablecoin Borrow cohort decoded for {args.chain}')

    cohort.to_parquet(out / 'borrow_cohort.parquet', index=False)
    asset_rows = [
        {'chain': args.chain, 'address': address, **meta}
        for address, meta in assets.items()
    ]
    pd.DataFrame(asset_rows).to_csv(out / 'asset_map.csv', index=False)
    summary = {
        'chain': args.chain,
        'extraction': extraction,
        'stable_borrows': int(len(cohort)),
        'candidates': int(cohort.candidate.sum()),
        'controls': int((~cohort.candidate).sum()),
        'year_counts': cohort.groupby(['year', 'candidate']).size().rename('n').reset_index().to_dict('records'),
    }
    (out / 'chain_summary.json').write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))


if __name__ == '__main__':
    main()
