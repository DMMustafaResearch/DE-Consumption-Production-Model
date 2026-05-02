#!/usr/bin/env python3
"""
PRE-REGISTRATION TEST SCRIPT
=============================
Tests the Developmental Cosmology w(z) prediction against data.

This script implements the exact confirmation/falsification criteria
from the pre-registration document posted to Zenodo.

MODEL: DE density evolves with star formation
  d(rho_DE)/dt = alpha * psi(t) - beta * rho_star_surviving(t)
  
FIXED PARAMETERS (locked at pre-registration):
  f_prim = 0.445  (primordial DE fraction)
  gamma  = 0.272  (consumption coupling)
  R      = 0.4    (stellar mass return fraction)

PREDICTIONS: w(z) at 10 redshift bins with tolerances
CRITERIA: 
  Confirmation: 6/10 bins within tolerance
  Falsification: 5/10 bins outside tolerance
  Phantom crossing: z = 0.33 +/- 0.12

RUN AGAINST:
  - DESI 5yr (primary, ~2027)
  - Euclid, Roman, LSST, GW sirens (independent)

Usage:
  python test_preregistration.py                    # shows predictions only
  python test_preregistration.py --data desi5yr.csv # tests against data
  
Data file format (CSV):
  z, w, sigma_w
  0.05, -0.92, 0.08
  0.15, -0.95, 0.06
  ...
"""

import numpy as np
from scipy import integrate
import sys
import os

# ============================================================
# FIXED MODEL PARAMETERS (locked at pre-registration)
# ============================================================
F_PRIM = 0.445   # primordial DE fraction
GAMMA = 0.272    # consumption coupling to SFR
R_RETURN = 0.4   # stellar mass return fraction
Z_MAX = 10.0     # integration upper limit
H0 = 67.4        # km/s/Mpc (Planck 2018)
OMEGA_M = 0.315  # matter density parameter

# ============================================================
# STAR FORMATION RATE (Madau & Dickinson 2014)
# ============================================================
def sfr_density(z):
    """Cosmic star-formation rate density [Msun/yr/Mpc^3]"""
    return 0.015 * (1 + z)**2.7 / (1 + ((1 + z) / 2.9)**5.6)

def dt_dz(z):
    """dt/dz in Gyr, using LCDM expansion history"""
    H_z = H0 * np.sqrt(OMEGA_M * (1 + z)**3 + (1 - OMEGA_M))  # km/s/Mpc
    H_z_per_Gyr = H_z * 1.022e-3  # convert to 1/Gyr
    return -1.0 / ((1 + z) * H_z_per_Gyr)

def surviving_stellar_mass(z):
    """Surviving stellar mass density at redshift z [Msun/Mpc^3]"""
    def integrand(zp):
        return sfr_density(zp) * abs(dt_dz(zp)) * 1e9  # Gyr -> yr
    result, _ = integrate.quad(integrand, z, Z_MAX)
    return (1 - R_RETURN) * result

# Cache the peak SFR and stellar mass at z=0
SFR_PEAK = sfr_density(1.9)  # peak of Madau-Dickinson
STELLAR_MASS_Z0 = surviving_stellar_mass(0)

# ============================================================
# DE DENSITY EVOLUTION
# ============================================================
def compute_F(z):
    """Compute the integral F(z) from the model."""
    def integrand(zp):
        psi = sfr_density(zp)
        rho_star = surviving_stellar_mass(zp)
        consumption = GAMMA * (rho_star / STELLAR_MASS_Z0) * SFR_PEAK
        return (psi - consumption) * abs(dt_dz(zp))
    result, _ = integrate.quad(integrand, z, Z_MAX, limit=100)
    return result

def rho_DE_ratio(z):
    """rho_DE(z) / rho_DE(0)"""
    F_z = compute_F(z)
    F_0 = compute_F(0)
    return F_PRIM + (1 - F_PRIM) * F_z / F_0

def w_of_z(z):
    """Dark energy equation of state w(z)"""
    dz = 0.01
    if z < dz:
        rho_0 = rho_DE_ratio(0)
        rho_dz = rho_DE_ratio(dz)
        dlnrho_dlna = -((rho_dz - rho_0) / rho_0) / (np.log(1/(1+dz)))
    else:
        rho_plus = rho_DE_ratio(z + dz/2)
        rho_minus = rho_DE_ratio(z - dz/2)
        rho_center = rho_DE_ratio(z)
        dlnrho_dlna = -((rho_plus - rho_minus) / rho_center) / (
            np.log((1+z-dz/2)/(1+z+dz/2)))
    return -1 + dlnrho_dlna / 3

# ============================================================
# PRE-REGISTERED PREDICTIONS (Table 1 from document)
# ============================================================
PREDICTIONS = [
    # (z, w_predicted, tolerance)
    (0.05, -0.906, 0.038),
    (0.15, -0.938, 0.030),
    (0.30, -0.981, 0.030),
    (0.40, -1.003, 0.030),
    (0.50, -1.018, 0.025),
    (0.70, -1.036, 0.025),
    (0.90, -1.043, 0.025),
    (1.10, -1.044, 0.030),
    (1.50, -1.037, 0.035),
    (2.00, -1.022, 0.040),
]

# Phantom crossing prediction
Z_CROSS = 0.33
Z_CROSS_ERR = 0.12  # so window is [0.21, 0.45]

# ============================================================
# TEST FUNCTION
# ============================================================
def test_against_data(data_file):
    """
    Test pre-registered predictions against measured w(z) data.
    
    Data file should be CSV with columns: z, w, sigma_w
    """
    import csv
    
    measurements = []
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            measurements.append({
                'z': float(row['z']),
                'w': float(row['w']),
                'sigma_w': float(row['sigma_w'])
            })
    
    print("="*72)
    print("PRE-REGISTRATION TEST RESULTS")
    print("="*72)
    print()
    
    bins_in = 0
    bins_out = 0
    
    print(f"{'z':>6} | {'w_pred':>8} | {'tol':>6} | {'w_meas':>8} | {'sigma':>6} | {'|diff|':>8} | {'limit':>8} | {'Result':>8}")
    print("-"*72)
    
    for z_pred, w_pred, tol in PREDICTIONS:
        # Find the closest measurement to this redshift bin
        closest = min(measurements, key=lambda m: abs(m['z'] - z_pred))
        
        if abs(closest['z'] - z_pred) > 0.1:
            print(f"  {z_pred:4.2f} | {w_pred:+8.3f} | {tol:6.3f} | {'---':>8} | {'---':>6} | {'---':>8} | {'---':>8} | NO DATA")
            continue
        
        w_meas = closest['w']
        sigma = closest['sigma_w']
        
        # Criterion: |w_meas - w_pred| < tol + sigma
        diff = abs(w_meas - w_pred)
        limit = tol + sigma
        is_in = diff < limit
        
        if is_in:
            bins_in += 1
            result = "IN"
        else:
            bins_out += 1
            result = "OUT"
        
        print(f"  {z_pred:4.2f} | {w_pred:+8.3f} | {tol:6.3f} | {w_meas:+8.3f} | {sigma:6.3f} | {diff:8.3f} | {limit:8.3f} | {result:>8}")
    
    total = bins_in + bins_out
    print()
    print(f"  Bins within tolerance: {bins_in}/{total}")
    print(f"  Bins outside tolerance: {bins_out}/{total}")
    print()
    
    # Confirmation/falsification
    if bins_in >= 6:
        print("  *** CONFIRMATION: 6+ bins within tolerance ***")
    elif bins_out >= 5:
        print("  *** FALSIFICATION: 5+ bins outside tolerance ***")
    else:
        print("  INCONCLUSIVE: neither threshold met")
    
    # Check phantom crossing
    print()
    print("Phantom crossing test:")
    print(f"  Predicted: z = {Z_CROSS} +/- {Z_CROSS_ERR} (window [{Z_CROSS-Z_CROSS_ERR:.2f}, {Z_CROSS+Z_CROSS_ERR:.2f}])")
    
    # Find where w crosses -1 in the data
    crossings = []
    sorted_meas = sorted(measurements, key=lambda m: m['z'])
    for i in range(len(sorted_meas)-1):
        if (sorted_meas[i]['w'] + 1) * (sorted_meas[i+1]['w'] + 1) < 0:
            # Linear interpolation for crossing point
            z1, w1 = sorted_meas[i]['z'], sorted_meas[i]['w']
            z2, w2 = sorted_meas[i+1]['z'], sorted_meas[i+1]['w']
            z_cross_meas = z1 + (z2 - z1) * (-1 - w1) / (w2 - w1)
            crossings.append(z_cross_meas)
    
    if crossings:
        for zc in crossings:
            in_window = abs(zc - Z_CROSS) < Z_CROSS_ERR
            print(f"  Observed crossing at z = {zc:.3f}: {'WITHIN' if in_window else 'OUTSIDE'} prediction window")
    else:
        print("  No phantom crossing detected in data")

# ============================================================
# DISPLAY PREDICTIONS
# ============================================================
def show_predictions():
    print("="*72)
    print("PRE-REGISTERED w(z) PREDICTIONS")
    print("Developmental Cosmology: DE Consumption-Production Model")
    print("="*72)
    print()
    print(f"Parameters (fixed): f_prim = {F_PRIM}, gamma = {GAMMA}, R = {R_RETURN}")
    print(f"Phantom crossing: z = {Z_CROSS} +/- {Z_CROSS_ERR}")
    print()
    
    print(f"{'z':>6} | {'w_pred':>8} | {'tolerance':>10} | {'LCDM excl?':>11} | {'w_computed':>10}")
    print("-"*55)
    
    for z, w_pred, tol in PREDICTIONS:
        w_comp = w_of_z(z)
        lcdm_dist = abs(w_pred - (-1.0))
        lcdm_excluded = "YES" if lcdm_dist > tol else "no"
        print(f"  {z:4.2f} | {w_pred:+8.3f} | +/-{tol:6.3f} | {lcdm_excluded:>11} | {w_comp:+10.3f}")
    
    lcdm_excluded_count = sum(1 for _, w, t in PREDICTIONS if abs(w - (-1.0)) > t)
    print()
    print(f"LCDM (w=-1) excluded at {lcdm_excluded_count}/10 bins")
    print(f"Confirmation criterion: 6/10 bins within tolerance")
    print(f"Falsification criterion: 5/10 bins outside tolerance")
    print()
    print("CONFIRMATION/FALSIFICATION RULE:")
    print("  A bin is 'within tolerance' if:")
    print("    |w_measured - w_predicted| < tolerance + sigma_measured")
    print("  A bin is 'outside tolerance' if this condition is NOT met.")

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--data":
        if len(sys.argv) < 3:
            print("Usage: python test_preregistration.py --data <data_file.csv>")
            sys.exit(1)
        data_file = sys.argv[2]
        if not os.path.exists(data_file):
            print(f"File not found: {data_file}")
            sys.exit(1)
        test_against_data(data_file)
    else:
        show_predictions()
        print()
        print("To test against data:")
        print("  python test_preregistration.py --data measurements.csv")
        print()
        print("Data file format (CSV with header):")
        print("  z,w,sigma_w")
        print("  0.05,-0.92,0.08")
        print("  0.15,-0.95,0.06")
        print("  ...")
