# DE Consumption-Production Model

Pre-registered prediction for the dark energy equation of state $w(z)$, tied to the cosmic star-formation history. This repository contains the LaTeX source of the pre-registration, the bibliography, and the Python scripts that operationalise the registered prediction.

**Pre-registration on Zenodo:** [10.5281/zenodo.19635852](https://doi.org/10.5281/zenodo.19635852)

## Summary

The model predicts that the dark-energy sector receives two opposite-sign source terms:

- **Production:** $+\alpha\,\psi(t)$, proportional to the cosmic star-formation rate density (Madau & Dickinson 2014).
- **Consumption:** $-\beta\,\rho_{\star,\rm surv}(t)$, proportional to surviving stellar mass density, with return fraction $R = 0.4$.

The two terms enter an integral kernel as a subtraction; what survives is the net integrated cosmic history.

**Locked parameters** (frozen at registration):

| Parameter | Value |
|---|---|
| $f_{\rm prim}$ | 0.445 |
| $\gamma$ | 0.272 |
| $R$ | 0.4 |

**Key predictions:**

- $w(z)$ at 10 redshift bins ($z = 0.05$ to $2.0$).
- $\Lambda$CDM ($w = -1$) excluded at 8 of 10 bins.
- Phantom crossing at $z = 0.33 \pm 0.12$ (window $[0.21, 0.45]$).
- Curvature $d^2w/dz^2$ at the crossing distinguishes the model from any CPL fit.

**Test surveys:** DESI 5-yr (weakly independent — Year 1 was used to fit), Euclid, Roman Space Telescope, LSST / Vera Rubin, and gravitational-wave standard sirens.

The model is registered as a fitting function tied to the observed SFR history, not as a fundamental theory: no Lagrangian, no identified DE degree of freedom, no perturbation-stability proof.

## Repository contents

| File | Purpose |
|---|---|
| `preregistration_FINAL.tex` | LaTeX source of the registered pre-registration document |
| `references.bib` | Bibliography |
| `test_preregistration.py` | Runnable test script — applies the registered confirmation/falsification criteria to measured $w(z)$ data |
| `cf4_h0_environment_test.py` | Cosmicflows-4 $H_0$-by-environment test (related Developmental Cosmology probe) |
| `extract_tng_SLIM.py` | TNG300 data-extraction helper |
| `CF4_DOWNLOAD_GUIDE.md` | Step-by-step instructions for the Cosmicflows-4 dataset |

## Running the pre-registration test

```bash
# Show the predicted w(z) trajectory and tolerances
python test_preregistration.py

# Test against measured w(z) data
python test_preregistration.py --data measurements.csv
```

Input CSV format:

```
z,w,sigma_w
0.05,-0.92,0.08
0.15,-0.95,0.06
...
```

**Decision rule:**

- A bin is *within tolerance* if $|w_{\rm meas} - w_{\rm pred}| < \delta_{\rm tol} + \sigma_{\rm meas}$.
- **Confirmation:** $\geq 6/10$ bins within tolerance + phantom crossing in $[0.21, 0.45]$ + overall $\chi^2$ $p > 0.05$ + $w(z=0) > -1$ at $\geq 2\sigma$.
- **Falsification:** $\geq 5/10$ bins outside, or no crossing in window, or $\chi^2$ $p < 0.01$, or $w(z)$ consistent with $-1$ at all $z$ at $2\sigma$.

## Dependencies

- Python 3.8+
- `numpy`
- `scipy`

```bash
pip install numpy scipy
```

## Citation

If you use this code or test the prediction, please cite the Zenodo deposit:

> Mustafa, D. (2026). *Pre-registered Prediction for the Dark Energy Equation of State from a Consumption-Production Model.* Zenodo. [10.5281/zenodo.19635852](https://doi.org/10.5281/zenodo.19635852)

## License

See [`LICENSE`](LICENSE).
