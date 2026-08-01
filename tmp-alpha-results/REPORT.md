# Frozen listing-lifecycle validation

- Verified alpha found: **False**
- Input rows: 103,186
- Symbols: 578
- Generated signal trades: 686

## Results

### base
- Development-selected leverage: 0.25
- OOS terminal factor: 0.6180x
- OOS CAGR: -14.82%
- OOS stress MDD: 71.98%
- OOS trades: 365
- Passed: **False**
- Gates: `{"three_year_terminal_ge_1331": false, "stress_mdd_le_40pct": false, "at_least_3_calendar_years": true, "every_year_factor_ge_3": false, "best_year_log_share_le_50pct": false, "delete_top5_terminal_ge_512": false, "delete_top10_terminal_gt_1": false, "trade_count_ge_60": true}`

### dispersion_gate
- Development-selected leverage: 0.25
- OOS terminal factor: 1.0823x
- OOS CAGR: 2.67%
- OOS stress MDD: 30.78%
- OOS trades: 242
- Passed: **False**
- Gates: `{"three_year_terminal_ge_1331": false, "stress_mdd_le_40pct": true, "at_least_3_calendar_years": true, "every_year_factor_ge_3": false, "best_year_log_share_le_50pct": false, "delete_top5_terminal_ge_512": false, "delete_top10_terminal_gt_1": false, "trade_count_ge_60": true}`
