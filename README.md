# Reproducibility supplement

Manuscript: Testing Adaptive Friction for Generative AI Programming Through Reproducible Simulations

## Evidence status

This is a simulation-only study. No participant experiment was conducted. All gains, time costs, moderator effects and delayed changes are imposed scenario assumptions. A successful simulation does not validate adaptive prompting in human users. The analytical trigger model is a separate sensitivity exercise, not a calibrated mechanism underlying the arm-level simulations.

## Run

Use Python 3.12 with the packages pinned in requirements.txt. Install those packages in a virtual environment, then run:

    python analyse.py

The script regenerates synthetic_data.csv, monte_carlo.csv, results.json and fig1.png through fig4.png in its own directory. There are 90,000 replicated trials across 18 configurations, plus one illustrative dataset of 165 synthetic units. The initial seed is 20261103. Per-configuration seeds and all generating coefficients are visible in the script and manuscript Appendix A. The script uses vectorised ordinary least-squares calculations. Reproducing floating-point results across different numerical libraries may produce insignificant rounding changes.

## Files

- analyse.py: complete executable analysis and figure generation.
- synthetic_data.csv: the illustrative synthetic dataset; not collected human records.
- monte_carlo.csv: all scenario operating characteristics, Monte Carlo standard errors, contrast bias and coverage.
- results.json: fitted contrasts, confidence intervals, assumptions and runtime metadata.
- fig1.png to fig4.png: standalone figures used in the manuscript.
- equations.py and equations.json: display-equation source; run equations.py to regenerate equation images with Matplotlib.
- reference_audit.csv: mapping of manuscript reference numbers to all 89 supplied records and 24 additional references.
- references.json: formatted bibliographic fields and explicit verification status. Supplied original records are preserved where applicable.
- supplied_refs.json: the original supplied bibliography parsed without inventing missing fields.
- content.json: final prose sections before numbered citation replacement.
- word_counts.json: section counts excluding citation markers, headings, equations, captions and tables; hyphenated forms count as one whitespace-delimited word.
- requirements.txt: exact versions used for analysis.

## Reference limitations

The 24 added references and four directly relevant supplied records were checked against primary-paper metadata or abstracts. The remaining 85 supplied records are not independently verified here and are marked accordingly. Their preservation supports a title-level applicability audit and does not establish existence, accuracy, peer-review status or relevance. Missing publication metadata and unrelated references must be resolved before a journal submission. No target journal was supplied.

## Interpretation limits

The primary joint rule requires a one-sided 95% transfer lower bound greater than five points and a one-sided 95% time-ratio upper bound below 1.10. It concerns one prespecified policy at mean ability. It does not guarantee individual or subgroup benefit. Complete observations, Gaussian errors and constant variance are modelling assumptions. The model does not simulate a validated behavioural detector, participant attrition, or a functioning AI interface. Prompt dose and adaptive timing are not experimentally separated.
