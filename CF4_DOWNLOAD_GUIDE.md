# Cosmicflows-4 H0-by-Environment Test
## Step-by-step download and analysis

### What you're testing

The framework predicts that dark energy varies spatially: voids have less DE,
so the local expansion rate should be ~4% lower in voids than filaments.
Standard cosmology predicts: H0 is the same everywhere.

### Step 1: Download the data (5 minutes)

Go to this URL in your browser:

**https://vizier.cds.unistra.fr/viz-bin/VizieR-3?-source=J/ApJ/944/94**

You'll see a page listing the Cosmicflows-4 tables. You need **table3** (CF4 All Groups).

1. Click on **table3** ("CF4 All Groups, 38057 groups")
2. At the top, set **max rows** to **unlimited**
3. Under **Output layout**, choose **tab-separated values**
4. Click **Submit query**
5. When the data appears, save the page as:
   `C:\Users\Dudu\Documents\Heavens and Earth docs\data\cf4\cf4_groups.tsv`

That's it. One file, ~38,000 rows.

### Step 2: Install dependencies

Open Command Prompt:
```
pip install numpy pandas scipy astropy
```

### Step 3: Run the analysis

```
cd "C:\Users\Dudu\Documents\Heavens and Earth docs\data\cf4"
python cf4_h0_environment_test.py
```

The script will:
- Load the 38,057 CF4 groups
- Filter to groups with reliable distances (3000-15000 km/s)
- Classify each group as void or filament by local density
- Compute H0 = velocity / distance for each group
- Compare H0 in voids vs filaments
- Run a bootstrap test for statistical significance
- Report whether the ratio matches the framework's 0.96 prediction

### What to look for in the output

```
H0 by environment:
  Void:     median = XX.XX km/s/Mpc
  Filament: median = YY.YY km/s/Mpc
  Ratio H0_void / H0_fil = Z.ZZZZ

  FRAMEWORK PREDICTION: ratio = 0.96
  LCDM PREDICTION:      ratio = 1.00
```

If the ratio is significantly below 1.0 (and the bootstrap CI excludes 1.0),
that's evidence for spatially varying DE. If it's consistent with 1.0,
LCDM is sufficient.

### Columns in the CF4 Groups table

The key columns you need (names may vary slightly):
- **Nest**: Group ID number
- **Vgp**: Group velocity in CMB frame (km/s)
- **Dgp**: Group distance (Mpc)
- **GLon**: Galactic longitude (degrees)
- **GLat**: Galactic latitude (degrees)
- **Ngal**: Number of galaxies in group

### Alternative: download from EDD directly

If VizieR doesn't work:
1. Go to https://edd.ifa.hawaii.edu/
2. Click on the catalog list
3. Select "CF4 All Groups"
4. Download all columns
5. Save as cf4_groups.tsv

### Upload the results

After running the script, copy-paste the output into our conversation
and I'll interpret the results.
