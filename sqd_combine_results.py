#!/usr/bin/env python3
"""Combine per-chain cohorts under the unchanged frozen BCLX M→Q contract."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import pandas as pd

import sqd_mq_fast_runner as f

m = f.m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    root = Path(args.input)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    cohort_files = sorted(root.rglob('borrow_cohort.parquet'))
    if len(cohort_files) != 4:
        raise RuntimeError(f'Expected four chain cohorts, found {len(cohort_files)}: {cohort_files}')
    B = pd.concat([pd.read_parquet(path) for path in cohort_files], ignore_index=True)
    if B.empty:
        raise RuntimeError('Combined Borrow cohort is empty')

    summaries = []
    for path in sorted(root.rglob('chain_summary.json')):
        summaries.append(json.loads(path.read_text()))
    asset_maps = [pd.read_csv(path) for path in sorted(root.rglob('asset_map.csv'))]
    pd.concat(asset_maps, ignore_index=True).to_csv(out / 'asset_map.csv', index=False)
    (out / 'extraction_summary.json').write_text(json.dumps(summaries, indent=2, default=str))

    matches, B = f.build_matches(B)
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
            'pipeline': 'four isolated chain runners; streaming event state; cross-chain frozen combiner',
        },
        'extraction': summaries,
        'borrow_counts': {
            'total': int(len(B)),
            'candidate': int(B.candidate.sum()),
            'control': int((~B.candidate).sum()),
            'by_chain': B.groupby(['chain', 'candidate']).size().rename('n').reset_index().to_dict('records'),
            'by_year': B.groupby(['year', 'candidate']).size().rename('n').reset_index().to_dict('records'),
        },
        'labels': {},
        'primary': {},
        'gates': {},
    }

    primary_pairs = pd.DataFrame()
    for label in labels:
        P = f.materialize_label(matches, B, label)
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
    trim_boot = m.bootstrap_lcb(trimmed.pair_diff.to_numpy(), seed=20260802)
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
        'each_2023_2025_candidate_count_ge_20': all(int((P.year == year).sum()) >= 20 for year in [2023, 2024, 2025]),
        'development_effect_positive': devb[0] > 0,
        'selection_2024_effect_positive': selb[0] > 0,
        'final_2025_effect_positive': finb[0] > 0,
        'final_2025_lcb5_positive': finb[1] > 0,
        'combined_2024_2025_lcb5_positive': combined[1] > 0,
        'delete_top10_users_effect_positive': trim_boot[0] > 0,
    }
    results['primary'] = {
        'development': {'n': len(dev), 'effect': devb[0], 'lcb5': devb[1]},
        'selection_2024': {'n': len(sel), 'effect': selb[0], 'lcb5': selb[1]},
        'final_2025': {'n': len(fin), 'effect': finb[0], 'lcb5': finb[1]},
        'combined_2024_2025': {'n': len(P[P.year.isin([2024, 2025])]), 'effect': combined[0], 'lcb5': combined[1]},
        'trim_top10_users': {'n': len(trimmed), 'effect': trim_boot[0], 'lcb5': trim_boot[1]},
        'top10_users': sorted(top_users),
    }
    results['gates'] = gates
    results['mq_verified'] = all(gates.values())
    (out / 'summary.json').write_text(json.dumps(results, indent=2, default=str))

    report = [
        '# Frozen BCLX-R M→Q Test — Four-chain streaming pipeline', '',
        f"- M→Q verified: **{results['mq_verified']}**",
        f"- Stable Borrow events: {len(B):,}",
        f"- Strict atomic candidates: {int(B.candidate.sum()):,}",
        f"- Matched primary candidates: {len(P):,}", '',
        '## Primary deleveraging effect',
    ]
    for key, value in results['primary'].items():
        report.append(f"- {key}: n={value.get('n')}, effect={value.get('effect')}, LCB5={value.get('lcb5')}")
    report += ['', '## Gates', json.dumps(gates, indent=2)]
    (out / 'REPORT.md').write_text('\n'.join(report))
    print(json.dumps({'mq_verified': results['mq_verified'], 'borrow_counts': results['borrow_counts'], 'primary': results['primary'], 'gates': gates}, indent=2, default=str))


if __name__ == '__main__':
    main()
