---
id: architecture-config-params
title: Configuration Parameters
type: architecture
tags: [architecture, config]
last_updated: 2026-07-05
status: active
source: agent
---

# Context
Canonical explanation of config knobs and business impact.

Target: src/models/forecasting.py -> run_forecast()
Config Parameter: volatility_penalty in config/config.yaml
Business Context: Increasing volatility_penalty above 0.5 reduces false-positive alerts, lowering operator alert fatigue.

## Related
- [[qa/business]]
- [[qa/technical]]
