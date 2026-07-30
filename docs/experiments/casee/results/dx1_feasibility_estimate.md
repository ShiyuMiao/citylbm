# Case E dx=1 m Feasibility Estimate

- STL model-scale bbox: 1.581267 x 1.580606 x 0.240000 m.
- Full-scale bbox at scale 250: 395.317 x 395.151 x 60.000 m.
- The conservative domain estimate is illustrative only and adds 5H lateral padding on both sides, 5H upstream, 15H downstream, and 6H height.
- This artifact is not a solver run and not grid-independence evidence.

| dx (m) | bbox cells | bbox cell count | illustrative domain cells | illustrative cell count |
|---:|---|---:|---|---:|
| 3 | 132x132x21 | 365904 | 332x532x121 | 21371504 |
| 2 | 198x198x31 | 1215324 | 498x798x181 | 71930124 |
| 1 | 396x396x61 | 9565776 | 996x1596x361 | 573851376 |
