# Mechanism family search

{
  "selected_without_oos": "drawdown_recovery_k1",
  "selected_leverage": 0.25,
  "oos": {
    "terminal": 0.19408969659933936,
    "mdd": 0.8972627420534808,
    "trades": 365,
    "yearly": {
      "2023": {
        "factor": 0.6393832817795515,
        "mdd": 0.4967964601526268
      },
      "2024": {
        "factor": 0.44557116937716745,
        "mdd": 0.7205374357684311
      },
      "2025": {
        "factor": 0.6812776200769128,
        "mdd": 0.7225952554513039
      }
    }
  },
  "delete_top5": {
    "terminal": 0.11861063282398854,
    "mdd": 0.9060414758919947,
    "trades": 360,
    "yearly": {
      "2023": {
        "factor": 0.6393832817795515,
        "mdd": 0.4967964601526268
      },
      "2024": {
        "factor": 0.4093788511438373,
        "mdd": 0.743237284309147
      },
      "2025": {
        "factor": 0.4531447405691559,
        "mdd": 0.7004987886554732
      }
    }
  },
  "delete_top10": {
    "terminal": 0.08264727229839759,
    "mdd": 0.9311674082153478,
    "trades": 355,
    "yearly": {
      "2023": {
        "factor": 0.6393832817795515,
        "mdd": 0.4967964601526268
      },
      "2024": {
        "factor": 0.35417893761115726,
        "mdd": 0.7778587105624817
      },
      "2025": {
        "factor": 0.36495936922251054,
        "mdd": 0.734136844790128
      }
    }
  },
  "year_concentration": 1,
  "gates": {
    "terminal_ge_1331": false,
    "mdd_le_40pct": false,
    "each_year_ge_3": false,
    "year_log_share_le_50pct": false,
    "delete_top5_ge_512": false,
    "delete_top10_gt_1": false,
    "trades_ge_60": true
  },
  "verified": false,
  "candidate_count": 36,
  "data_rows": 103186,
  "symbols": 578
}