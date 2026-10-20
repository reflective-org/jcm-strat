# Phase 19b precision gate: p19

Run: `runs/p19jhn400_spinup_19891201`; reference (old jcm, context only): `/data/JCM_stripped/jcm-strat-phase13/runs/p13jhn400_19900101`

Gate: max |change of NH-SH area-mean ps| < 5.0 hPa and max |change of global-mean ps| < 0.5 hPa over the first 31 days (jcm #892: buggy -116 hPa NH-SH in 30 d, fixed +0.03 hPa on HS T63L47).

| run | NH-SH at start [hPa] | max abs dA | dA at end | global mean at start | max abs dG | dG at end |
|---|---|---|---|---|---|---|
| new jcm (35dc1997, dinosaur 1.5.0) | -4.80 | 2.228 | -1.204 | 998.52 | 0.0726 | +0.0386 |
| old jcm (849893be, dinosaur SL bd99e39) | -5.15 | 2.162 | +0.229 | 998.51 | 0.1345 | +0.1335 |

**Result: PASS** (new jcm: max |dA| 2.228 hPa, end -1.204; max |dG| 0.0726 hPa, end +0.0386).

![ps gate](p19_ps_gate.png)
