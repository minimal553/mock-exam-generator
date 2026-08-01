#!/usr/bin/env python3
"""Engineering-equivalent accelerated runner for the frozen BCLX M→Q test."""
from __future__ import annotations
import argparse
import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sqd_mq_analysis as m

# Same observations and rules; only wider transport windows and one global rate gate.
m.WINDOW_BLOCKS = 5_000_000
_ORIG_REQUEST = m.request_portal
_RATE_LOCK = threading.Lock()
_LAST_REQUEST = 0.0

def rate_limited_request(session, url, payload):
    global _LAST_REQUEST
    with _RATE_LOCK:
        delay = 0.55 - (time.monotonic() - _LAST_REQUEST)
        if delay > 0:
            time.sleep(delay)
        _LAST_REQUEST = time.monotonic()
    return _ORIG_REQUEST(session, url, payload)

m.request_portal = rate_limited_request


def extract_one(chain: str, cfg: dict[str, Any], raw: Path):
    assets = m.fetch_asset_map(chain, cfg['address_file'])
    extraction = m.extract_chain(chain, cfg, raw)
    borrows = m.build_chain_borrows(chain, raw / f'{chain}_events.csv', assets)
    return chain, assets, extraction, borrows


def build_matches(b: pd.DataFrame, controls_per: int = 5) -> pd.DataFrame:
    b = b.copy().reset_index(drop=True)
    b['global_id'] = np.arange(len(b))
    cand = b[b.candidate]
    ctrl = b[~b.candidate]
    groups = {k: g for k, g in ctrl.groupby(['chain', 'reserve', 'year'])}
    rows = []
    for r in cand.itertuples(index=False):
        g = groups.get((r.chain, r.reserve, r.year))
        if g is None or g.empty:
            continue
        g = g[g.on_behalf != r.on_behalf]
        if g.empty:
            continue
        score = (
            np.abs(g.log_amount.to_numpy(float) - float(r.log_amount))
            + .002 * np.abs((g.timestamp.to_numpy(np.int64) - int(r.timestamp)) / 86400.0)
            + .05 * np.abs(g.prior_borrows.to_numpy(float) - float(r.prior_borrows))
        )
        k = min(controls_per, len(g))
        selected = np.argpartition(score, k - 1)[:k] if k < len(g) else np.arange(len(g))
        chosen = g.iloc[selected]
        rows.append({
            'candidate_global_id': int(r.global_id),
            'candidate_user': r.on_behalf,
            'chain': r.chain,
            'reserve': r.reserve,
            'year': int(r.year),
            'candidate_asset': r.candidate_symbol,
            'candidate_timestamp': int(r.timestamp),
            'candidate_log_amount': float(r.log_amount),
            'control_global_ids': chosen.global_id.astype(int).tolist(),
            'controls': int(k),
        })
    return pd.DataFrame(rows), b


def materialize_label(matches: pd.DataFrame, b: pd.DataFrame, label: str) -> pd.DataFrame:
    if matches.empty:
        return pd.DataFrame()
    values = b.set_index('global_id')[label].astype(float)
    rows = []
    for r in matches.itertuples(index=False):
        cval = float(values.loc[r.candidate_global_id])
        ids = list(r.control_global_ids)
        mean = float(values.loc[ids].mean())
        rows.append({
            'chain': r.chain,
            'candidate_global_id': r.candidate_global_id,
            'candidate_user': r.candidate_user,
            'year': r.year,
            'reserve': r.reserve,
            'candidate_asset': r.candidate_asset,
            'candidate_value': cval,
            'control_mean': mean,
            'pair_diff': cval - mean,
            'controls': r.controls,
            'candidate_timestamp': r.candidate_timestamp,
            'candidate_log_amount': r.candidate_log_amount,
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = out / 'raw'
    raw.mkdir(exist_ok=True)

    extracted = []
    all_assets = {}
    borrow_frames = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(extract_one, chain, cfg, raw): chain for chain, cfg in m.CHAINS.items()}
        for future in as_completed(futures):
            chain, assets, summary, borrows = future.result()
            all_assets[chain] = assets
            extracted.append(summary)
            if not borrows.empty:
                borrow_frames.append(borrows)
            print(f'completed {chain}: {summary}', flush=True)

    B = pd.concat(borrow_frames, ignore_index=True) if borrow_frames else pd.DataFrame()
    if B.empty:
        raise RuntimeError('No stablecoin Borrow events decoded')

    assets_rows = []
    for chain, amap in all_assets.items():
        for address, meta in amap.items():
            assets_rows.append({'chain': chain, 'address': address, **meta})
    pd.DataFrame(assets_rows).to_csv(out / 'asset_map.csv', index=False)
    pd.DataFrame(extracted).to_json(out / 'extraction_summary.json', orient='records', indent=2)

    matches, B = build_matches(B)
    labels = ['repay7', 'repay30', 'repay90', 'liquid30', 'liquid90', 'delever30', 'delever90']
    results = {
        'contract': {
            'development': '2022-2023',
            'selection': '2024',
            'final': '2025',
            'candidate': 'stablecoin Borrow followed in same tx by non-stable Supply for same debtor; Borrow precedes Supply; FlashLoan excluded',
            'primary_label': 'delever90',
            'matching': 'chain + stable reserve + calendar year; nearest log amount, time, prior borrow count; five controls',
            'right_censor_cutoff': str(m.CANDIDATE_CUTOFF),
            'engineering_equivalence': '5m transport windows, SQD continuation, two-chain concurrency, global 0.55s request gate; statistical contract unchanged',
        },
        'extraction': extracted,
        'borrow_counts': {
            'total': int(len(B)),
            'candidate': int(B.candidate.sum()),
            'control': int((~B.candidate).sum()),
            'by_year': B.groupby(['year', 'candidate']).size().rename('n').reset_index().to_dict('records'),
        },
        'labels': {},
        'primary': {},
        'gates': {},
    }
    primary_pairs = pd.DataFrame()
    for label in labels:
        P = materialize_label(matches, B, label)
        if label == 'delever90':
            primary_pairs = P
            P.to_csv(out / 'matched_delever90.csv', index=False)
        yearly = []
        if not P.empty:
            for year, group in P.groupby('year'):
                mean, lcb, ucb = m.bootstrap_lcb(group.pair_diff.to_numpy(), seed=20260801 + int(year))
                yearly.append({'year': int(year), 'n': len(group), 'effect': mean, 'lcb5': lcb, 'ucb95': ucb})
            overall = m.bootstrap_lcb(P.pair_diff.to_numpy())
        else:
            overall = (math.nan, math.nan, math.nan)
        results['labels'][label] = {
            'unmatched': m.rate_stats(B, label),
            'matched_n': int(len(P)),
            'matched_effect': overall[0],
            'matched_lcb5': overall[1],
            'matched_ucb95': overall[2],
            'yearly': yearly,
        }

    P = primary_pairs
    top_users = set(P.candidate_user.value_counts().head(10).index) if not P.empty else set()
    trimmed = P[~P.candidate_user.isin(top_users)] if not P.empty else P
    trimmed_boot = m.bootstrap_lcb(trimmed.pair_diff.to_numpy(), seed=20260802)
    dev = P[P.year.isin([2022, 2023])]
    sel = P[P.year == 2024]
    fin = P[P.year == 2025]
    devb = m.bootstrap_lcb(dev.pair_diff.to_numpy(), seed=20260803)
    selb = m.bootstrap_lcb(sel.pair_diff.to_numpy(), seed=20260804)
    finb = m.bootstrap_lcb(fin.pair_diff.to_numpy(), seed=20260805)
    combined = m.bootstrap_lcb(P[P.year.isin([2024, 2025])].pair_diff.to_numpy(), seed=20260806)

    gates = {
        'candidate_count_ge_100': int(B.candidate.sum()) >= 100,
        'matched_candidate_count_ge_100': len(P) >= 100,
        'each_2023_2025_candidate_count_ge_20': all(int((P.year == y).sum()) >= 20 for y in [2023, 2024, 2025]),
        'development_effect_positive': devb[0] > 0,
        'selection_2024_effect_positive': selb[0] > 0,
        'final_2025_effect_positive': finb[0] > 0,
        'final_2025_lcb5_positive': finb[1] > 0,
        'combined_2024_2025_lcb5_positive': combined[1] > 0,
        'delete_top10_users_effect_positive': trimmed_boot[0] > 0,
    }
    results['primary'] = {
        'development': {'n': len(dev), 'effect': devb[0], 'lcb5': devb[1]},
        'selection_2024': {'n': len(sel), 'effect': selb[0], 'lcb5': selb[1]},
        'final_2025': {'n': len(fin), 'effect': finb[0], 'lcb5': finb[1]},
        'combined_2024_2025': {'n': len(P[P.year.isin([2024, 2025])]), 'effect': combined[0], 'lcb5': combined[1]},
        'trim_top10_users': {'n': len(trimmed), 'effect': trimmed_boot[0], 'lcb5': trimmed_boot[1]},
        'top10_users': sorted(top_users),
    }
    results['gates'] = gates
    results['mq_verified'] = all(gates.values())
    (out / 'summary.json').write_text(json.dumps(results, indent=2, default=str))
    report = [
        '# Frozen BCLX-R M→Q Test — Accelerated Equivalent Runner', '',
        f"- M→Q verified: **{results['mq_verified']}**",
        f"- Stable Borrow events: {len(B):,}",
        f"- Strict atomic candidates: {int(B.candidate.sum()):,}",
        f"- Matched primary candidates: {len(P):,}", '',
        '## Primary effect',
    ]
    for key, value in results['primary'].items():
        report.append(f"- {key}: n={value.get('n')}, effect={value.get('effect')}, LCB5={value.get('lcb5')}")
    report += ['', '## Gates', json.dumps(gates, indent=2)]
    (out / 'REPORT.md').write_text('\n'.join(report))
    print(json.dumps({'mq_verified': results['mq_verified'], 'borrow_counts': results['borrow_counts'], 'primary': results['primary'], 'gates': gates}, indent=2, default=str))

if __name__ == '__main__':
    main()
