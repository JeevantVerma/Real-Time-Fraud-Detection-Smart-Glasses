| Method | Test set | Bona fide / attack | EER [95% CI] | AUC | Frozen thr. | APCER | BPCER |
|---|---|---|---|---|---|---|---|
| Heuristic | asvspoof2019_la_eval | 7355 / 63882 | 46.81% [44.75%, 48.60%] | 0.5240 | 0.4000 | 25.32% | 68.31% |
| AASIST-L pretrained | asvspoof2019_la_eval | 7355 / 63882 | 0.99% [0.75%, 1.30%] | 0.9992 | -0.9485 | 11.17% | 0.10% |

EER is threshold-free (each set's own). APCER/BPCER use the threshold frozen from that method's dev set (docs/EVALUATION_PLAN.md §3). CIs: bootstrap, resampled by speaker where IDs exist.

**Heuristic — asvspoof2019_la_eval, EER by attack_type** (each vs. all bona fide)

| attack_type | n | EER |
|---|---|---|
| A07 | 4914 | 44.67% |
| A08 | 4914 | 37.84% |
| A09 | 4914 | 34.73% |
| A10 | 4914 | 42.24% |
| A11 | 4914 | 38.48% |
| A12 | 4914 | 55.15% |
| A13 | 4914 | 63.28% |
| A14 | 4914 | 39.28% |
| A15 | 4914 | 45.65% |
| A16 | 4914 | 47.31% |
| A17 | 4914 | 50.86% |
| A18 | 4914 | 54.04% |
| A19 | 4914 | 55.04% |

**AASIST-L pretrained — asvspoof2019_la_eval, EER by attack_type** (each vs. all bona fide)

| attack_type | n | EER |
|---|---|---|
| A07 | 4914 | 0.55% |
| A08 | 4914 | 0.20% |
| A09 | 4914 | 0.00% |
| A10 | 4914 | 1.00% |
| A11 | 4914 | 0.14% |
| A12 | 4914 | 0.69% |
| A13 | 4914 | 0.20% |
| A14 | 4914 | 0.06% |
| A15 | 4914 | 0.57% |
| A16 | 4914 | 0.63% |
| A17 | 4914 | 1.91% |
| A18 | 4914 | 3.05% |
| A19 | 4914 | 0.71% |
