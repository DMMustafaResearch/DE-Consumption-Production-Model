#!/usr/bin/env python3
"""
COSMICFLOWS-4: H0-BY-ENVIRONMENT TEST
======================================

WHAT THIS TESTS:
  Framework predicts DE is spatially varying. If voids have less DE,
  the local expansion rate (H0) should be LOWER in voids than in
  filaments. Predicted: H_void / H_filament ~ 0.96 (4% deficit).

  LCDM predicts: H0 is the same everywhere (uniform Lambda).

DATA NEEDED:
  1. CF4 galaxy distances + redshifts (from VizieR or EDD)
  2. A void catalog (to classify environment)

=== HOW TO GET THE DATA ===

OPTION A: VizieR (easiest, no account needed)
---------------------------------------------
1. Go to: https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=J/ApJ/944/94
2. You'll see three tables:
     Table 2: "All CF4 Individual Distances" (55,877 galaxies)
     Table 3: "CF4 All Groups" (38,057 groups)
     Table 4: "CF4 All Group Velocities"
3. For each table:
   - Set "max rows" to "unlimited"
   - Click "Submit"
   - At the top of the results, click the download icon
   - Choose format: "tab-separated values" or "VOTable"
   - Save as: cf4_galaxies.tsv, cf4_groups.tsv, cf4_velocities.tsv

   OR use the direct FTP links:
     https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94/table2.dat
     https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94/table3.dat
     https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94/table4.dat
     https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94/ReadMe

   Download the ReadMe too - it describes all columns.

OPTION B: EDD (Extragalactic Distance Database)
------------------------------------------------
1. Go to: https://edd.ifa.hawaii.edu/
2. Click "Get Data" or "Catalogs"
3. Select catalog: "All CF4 Individual Distances"
4. Set output: "all columns"
5. Click "Submit" -> download the result
6. Repeat for "CF4 All Groups" and "CF4 All Group Velocities"

OPTION C: TOPCAT (GUI tool for astronomers)
-------------------------------------------
1. Install TOPCAT: https://www.star.bris.ac.uk/~mbt/topcat/
2. Open TOPCAT
3. VO > VizieR catalog service
4. Search for "J/ApJ/944/94"
5. Load tables 2, 3, 4
6. Save as CSV

VOID CATALOG (for environment classification):
  Option 1: Use the CF4 data itself (classify by local density)
  Option 2: Download BOSS DR12 void catalog from:
    http://www.cosmicvoids.net/
    Click "Catalogs" -> "BOSS DR12 voids" -> download

=== AFTER DOWNLOADING ===

Place the files in:
  C:\\Users\\Dudu\\Documents\\Heavens and Earth docs\\data\\cf4\\

Then run this script. It will:
  1. Load the CF4 group catalog
  2. Classify groups as void/filament by local density
  3. Compute H0 = v_CMB / d for each group
  4. Compare H0 in void vs filament environments
  5. Test whether the difference is significant

BEFORE RUNNING: pip install numpy pandas scipy astropy
"""

import numpy as np
import os
import sys

# ============================================================
# CONFIGURATION - adjust these paths
# ============================================================
DATA_DIR = r"C:\Users\Dudu\Documents\Heavens and Earth docs\data\cf4"

# If you downloaded from VizieR FTP (fixed-width format):
GROUPS_FILE = os.path.join(DATA_DIR, "table3.dat")
GALAXIES_FILE = os.path.join(DATA_DIR, "table2.dat")
README_FILE = os.path.join(DATA_DIR, "ReadMe")

# If you downloaded as TSV/CSV from VizieR web interface:
GROUPS_TSV = os.path.join(DATA_DIR, "cf4_groups.tsv")
GALAXIES_TSV = os.path.join(DATA_DIR, "cf4_galaxies.tsv")


def load_cf4_vizier_fixed(filename, readme_file=None):
    """Load a VizieR fixed-width .dat file using astropy."""
    try:
        from astropy.io import ascii as astro_ascii
        print(f"Loading {filename} with astropy...")
        if readme_file and os.path.exists(readme_file):
            table = astro_ascii.read(filename, format='cds', readme=readme_file)
        else:
            table = astro_ascii.read(filename, format='cds')
        return table.to_pandas()
    except Exception as e:
        print(f"  astropy CDS reader failed: {e}")
        print(f"  Trying pandas read_fwf...")
        import pandas as pd
        return pd.read_fwf(filename, comment='#')


def load_cf4_tsv(filename):
    """Load a VizieR TSV download."""
    import pandas as pd
    print(f"Loading {filename}...")
    # VizieR TSV files sometimes have comment lines starting with #
    df = pd.read_csv(filename, sep='\t', comment='#', na_values=['', ' ', '---'])
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns[:10])}...")
    return df


def run_h0_test(groups_df):
    """
    Main analysis: compute H0 by environment.
    
    CF4 Groups table contains:
      - Nest: group ID
      - Vgp: group velocity (km/s, CMB frame)
      - Dgp: group distance (Mpc)
      - GLon, GLat: galactic coordinates
      - Ngal: number of galaxies in group
    """
    print("="*60)
    print("H0-BY-ENVIRONMENT TEST")
    print("="*60)
    print()
    
    # Identify the relevant columns
    # Column names vary depending on download format
    # Common names: Vgp or Vcmb (velocity), Dgp or Dist (distance)
    col_names = list(groups_df.columns)
    print(f"Available columns: {col_names}")
    print()
    
    # Try to identify velocity and distance columns
    v_col = None
    d_col = None
    ra_col = None
    dec_col = None
    
    for c in col_names:
        cl = c.lower().strip()
        if cl in ['vgp', 'vcmb', 'v_cmb', 'vmod', 'vls']:
            v_col = c
        elif cl in ['dgp', 'dist', 'd', 'dmod', 'dm']:
            d_col = c
        elif cl in ['glon', 'gl', 'l', '_glon']:
            ra_col = c  # using galactic longitude
        elif cl in ['glat', 'gb', 'b', '_glat']:
            dec_col = c  # using galactic latitude
    
    if v_col is None or d_col is None:
        print("ERROR: Could not identify velocity and distance columns.")
        print("Please check the column names and edit this script.")
        print(f"Columns found: {col_names}")
        return
    
    print(f"Using: velocity = '{v_col}', distance = '{d_col}'")
    if ra_col: print(f"  Position: '{ra_col}', '{dec_col}'")
    print()
    
    # Convert to numeric
    v = pd.to_numeric(groups_df[v_col], errors='coerce')
    d = pd.to_numeric(groups_df[d_col], errors='coerce')
    
    # Filter: need valid velocity AND distance, d > 0
    valid = np.isfinite(v) & np.isfinite(d) & (d > 0) & (v > 0)
    
    # Also filter by distance range where H0 measurement is meaningful
    # Too close: peculiar velocities dominate
    # Too far: distance errors blow up
    # Sweet spot: 3000 < v < 15000 km/s (roughly 40-200 Mpc)
    valid &= (v > 3000) & (v < 15000)
    
    v = v[valid].values
    d = d[valid].values
    
    print(f"Groups with valid v and d in range 3000-15000 km/s: {len(v)}")
    if len(v) < 100:
        print("Too few groups. Check data format.")
        return
    
    # Compute H0 for each group
    H0_local = v / d  # km/s/Mpc
    
    print(f"Overall H0: median = {np.median(H0_local):.1f}, mean = {np.mean(H0_local):.1f} km/s/Mpc")
    print()
    
    # ============================================================
    # ENVIRONMENT CLASSIFICATION
    # Method: use the CF4 group positions to compute local density
    # Groups in low-density regions = voids
    # Groups in high-density regions = filaments/clusters
    # ============================================================
    
    if ra_col and dec_col:
        gl = pd.to_numeric(groups_df[ra_col], errors='coerce')[valid].values
        gb = pd.to_numeric(groups_df[dec_col], errors='coerce')[valid].values
    else:
        # If no coordinates, we can't do spatial classification
        # Fall back to distance-based binning only
        print("No position columns found. Using distance bins only.")
        gl = None
        gb = None
    
    if gl is not None and gb is not None:
        # Convert galactic (l,b) to Cartesian for density calculation
        gl_rad = np.radians(gl)
        gb_rad = np.radians(gb)
        x = d * np.cos(gb_rad) * np.cos(gl_rad)
        y = d * np.cos(gb_rad) * np.sin(gl_rad)
        z = d * np.sin(gb_rad)
        pos = np.column_stack([x, y, z])
        
        # Local density: count neighbors within R_link Mpc
        from scipy.spatial import cKDTree
        R_link = 20  # Mpc
        tree = cKDTree(pos)
        n_neighbors = np.array(tree.query_ball_point(pos, R_link, return_length=True))
        
        # Classify: bottom 25% density = void, top 25% = filament
        q25, q75 = np.percentile(n_neighbors, [25, 75])
        void_mask = n_neighbors < q25
        fil_mask = n_neighbors > q75
        
        print(f"Environment classification (R_link = {R_link} Mpc):")
        print(f"  Void groups (bottom 25%): {void_mask.sum()}")
        print(f"  Filament groups (top 25%): {fil_mask.sum()}")
        print()
        
        H0_void = H0_local[void_mask]
        H0_fil = H0_local[fil_mask]
        
        print(f"H0 by environment:")
        print(f"  Void:     median = {np.median(H0_void):.2f} +/- {np.std(H0_void)/np.sqrt(len(H0_void)):.2f} km/s/Mpc (n={len(H0_void)})")
        print(f"  Filament: median = {np.median(H0_fil):.2f} +/- {np.std(H0_fil)/np.sqrt(len(H0_fil)):.2f} km/s/Mpc (n={len(H0_fil)})")
        print(f"  Ratio H0_void / H0_fil = {np.median(H0_void)/np.median(H0_fil):.4f}")
        print()
        
        from scipy import stats
        
        # Mann-Whitney test
        mw = stats.mannwhitneyu(H0_void, H0_fil, alternative='two-sided')
        print(f"  Mann-Whitney test: U={mw.statistic:.0f}, p={mw.pvalue:.4e}")
        
        # Bootstrap confidence interval on the ratio
        np.random.seed(42)
        n_boot = 10000
        ratios = np.zeros(n_boot)
        for i in range(n_boot):
            v_boot = np.random.choice(H0_void, len(H0_void), replace=True)
            f_boot = np.random.choice(H0_fil, len(H0_fil), replace=True)
            ratios[i] = np.median(v_boot) / np.median(f_boot)
        
        ci_lo, ci_hi = np.percentile(ratios, [2.5, 97.5])
        print(f"  Bootstrap 95% CI on ratio: [{ci_lo:.4f}, {ci_hi:.4f}]")
        print()
        
        # Framework prediction
        print(f"  FRAMEWORK PREDICTION: ratio = 0.96 (4% DE depletion in voids)")
        print(f"  LCDM PREDICTION:      ratio = 1.00 (uniform Lambda)")
        print()
        
        if ci_lo < 1.0 < ci_hi:
            print(f"  RESULT: ratio is CONSISTENT WITH 1.0 (LCDM)")
            print(f"  Cannot distinguish from uniform Lambda")
        elif ci_hi < 1.0:
            print(f"  RESULT: H0_void < H0_fil at 95% confidence")
            print(f"  SUPPORTS framework's DE depletion prediction")
        elif ci_lo > 1.0:
            print(f"  RESULT: H0_void > H0_fil at 95% confidence")
            print(f"  OPPOSITE to framework prediction")
        
        if 0.96 > ci_lo and 0.96 < ci_hi:
            print(f"  The predicted ratio of 0.96 IS within the 95% CI")
        else:
            print(f"  The predicted ratio of 0.96 is OUTSIDE the 95% CI")
        
        # Also test in distance shells to check for systematics
        print()
        print("H0 ratio by distance shell (checking for systematics):")
        for v_lo, v_hi in [(3000, 5000), (5000, 8000), (8000, 12000), (12000, 15000)]:
            shell = (v > v_lo) & (v < v_hi)
            if (shell & void_mask).sum() > 20 and (shell & fil_mask).sum() > 20:
                h_v = np.median(H0_local[shell & void_mask])
                h_f = np.median(H0_local[shell & fil_mask])
                print(f"  {v_lo}-{v_hi} km/s: void={h_v:.1f}, fil={h_f:.1f}, ratio={h_v/h_f:.3f}")
    
    print()
    print("="*60)
    print("DONE")
    print("="*60)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    import pandas as pd
    
    groups_df = None
    
    # Try different file formats
    for filepath in [GROUPS_TSV, GROUPS_FILE]:
        if os.path.exists(filepath):
            if filepath.endswith('.tsv') or filepath.endswith('.csv'):
                groups_df = load_cf4_tsv(filepath)
            elif filepath.endswith('.dat'):
                groups_df = load_cf4_vizier_fixed(filepath, README_FILE)
            break
    
    if groups_df is None:
        print("="*60)
        print("DATA FILES NOT FOUND")
        print("="*60)
        print()
        print("Please download the CF4 data first.")
        print()
        print("QUICKEST METHOD:")
        print("  1. Open your browser to:")
        print("     https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=J/ApJ/944/94")
        print()
        print("  2. Click on 'table3' (CF4 All Groups)")
        print()
        print("  3. Set 'max' to 'unlimited'")
        print()
        print("  4. Under 'Preferences', choose output as:")
        print("     'tab-separated values' or 'CSV'")
        print()
        print("  5. Click 'Submit'")
        print()
        print("  6. Save the result as:")
        print(f"     {GROUPS_TSV}")
        print()
        print("  Then re-run this script.")
        sys.exit(1)
    
    run_h0_test(groups_df)
