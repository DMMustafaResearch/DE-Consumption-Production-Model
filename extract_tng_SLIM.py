#!/usr/bin/env python3
"""
SLIM TNG EXTRACTION - produces files small enough to upload (~5-20 MB each)

Strategy:
  1. Keep only the 3 fields we need: SubhaloPos, SubhaloMass, SubhaloGrNr
  2. Filter to the top N most massive subhalos (default 100,000)
  3. Save as float32 (half the size of float64)
  4. Also extract Group data (top 50,000 groups)

Run: python extract_tng_SLIM.py

BEFORE RUNNING: pip install numpy h5py
"""
import numpy as np
import h5py
import os
import glob
import sys

# ============================================================
# ADJUST THESE PATHS TO YOUR ACTUAL FOLDERS
# ============================================================
PATHS = {
    "full_99": r"C:\Users\Dudu\Documents\Heavens and Earth docs\data\TNG3001-datacat-99",
    "full_67": r"C:\Users\Dudu\Documents\Heavens and Earth docs\data\TNG3001 -datacat -67",
    "dark_99": r"C:\Users\Dudu\Documents\Heavens and Earth docs\data\TND3001-Dark-datacat-99",
}

# How many subhalos/groups to keep (top N by mass)
N_SUBHALOS = 100000
N_GROUPS = 50000

OUTPUT_DIR = r"C:\Users\Dudu\Documents\Heavens and Earth docs\data\extracted"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def find_hdf5_files(folder):
    files = []
    for p in ["*.hdf5", "*.h5"]:
        files.extend(glob.glob(os.path.join(folder, p)))
    files.sort()
    return files

def read_field_chunked(files, group_name, field_name):
    """Read a single field from all chunk files and concatenate."""
    chunks = []
    for f in files:
        try:
            with h5py.File(f, 'r') as hf:
                if group_name in hf and field_name in hf[group_name]:
                    chunks.append(hf[group_name][field_name][:])
        except:
            continue
    if chunks:
        return np.concatenate(chunks, axis=0)
    return None

def extract_slim(folder, label):
    files = find_hdf5_files(folder)
    if not files:
        print(f"  ERROR: No HDF5 files found in {folder}")
        print(f"  Check the path and try again.")
        # List what IS in the parent directory
        parent = os.path.dirname(folder)
        if os.path.exists(parent):
            print(f"  Contents of {parent}:")
            for item in os.listdir(parent):
                print(f"    {item}")
        return
    
    print(f"  Found {len(files)} chunk files")
    
    # First, peek at what fields exist
    with h5py.File(files[0], 'r') as hf:
        print(f"  Top-level groups: {list(hf.keys())}")
        if 'Subhalo' in hf:
            print(f"  Subhalo fields: {list(hf['Subhalo'].keys())[:10]}...")
        if 'Group' in hf:
            print(f"  Group fields: {list(hf['Group'].keys())[:10]}...")
    
    # Read the 3 essential subhalo fields
    print(f"  Reading SubhaloPos...")
    pos = read_field_chunked(files, 'Subhalo', 'SubhaloPos')
    print(f"  Reading SubhaloMass...")
    mass = read_field_chunked(files, 'Subhalo', 'SubhaloMass')
    print(f"  Reading SubhaloGrNr...")
    grNr = read_field_chunked(files, 'Subhalo', 'SubhaloGrNr')
    
    # Try to get SFR (only exists in full-physics run, not dark)
    sfr = read_field_chunked(files, 'Subhalo', 'SubhaloSFR')
    halfR = read_field_chunked(files, 'Subhalo', 'SubhaloHalfmassRad')
    
    if pos is None or mass is None:
        print(f"  ERROR: Could not read SubhaloPos or SubhaloMass")
        return
    
    print(f"  Total subhalos loaded: {len(pos)}")
    
    # Sort by mass, keep top N
    order = np.argsort(-mass)[:N_SUBHALOS]
    
    data = {
        'pos': pos[order].astype(np.float32),
        'mass': mass[order].astype(np.float32),
        'grNr': grNr[order].astype(np.int32) if grNr is not None else np.zeros(len(order), dtype=np.int32),
    }
    if sfr is not None:
        data['sfr'] = sfr[order].astype(np.float32)
    if halfR is not None:
        data['halfR'] = halfR[order].astype(np.float32)
    
    print(f"  Kept top {len(order)} subhalos by mass")
    print(f"  Mass range: {mass[order[0]]:.2e} to {mass[order[-1]]:.2e} (code units)")
    
    # Now read Group (halo) data
    print(f"  Reading GroupPos...")
    gpos = read_field_chunked(files, 'Group', 'GroupPos')
    
    # Try multiple possible mass field names
    gmass = None
    for mass_field in ['Group_M_Crit200', 'Group_M_Mean200', 'GroupMass']:
        gmass = read_field_chunked(files, 'Group', mass_field)
        if gmass is not None:
            print(f"  Using group mass field: {mass_field}")
            break
    
    gnsubs = read_field_chunked(files, 'Group', 'GroupNsubs')
    
    if gpos is not None and gmass is not None:
        gorder = np.argsort(-gmass)[:N_GROUPS]
        data['group_pos'] = gpos[gorder].astype(np.float32)
        data['group_mass'] = gmass[gorder].astype(np.float32)
        if gnsubs is not None:
            data['group_nsubs'] = gnsubs[gorder].astype(np.int32)
        print(f"  Kept top {len(gorder)} groups by mass")
    
    # Save compressed
    outfile = os.path.join(OUTPUT_DIR, f"tng_slim_{label}.npz")
    np.savez_compressed(outfile, **data)
    size_mb = os.path.getsize(outfile) / 1e6
    print(f"  SAVED: {outfile} ({size_mb:.1f} MB)")
    
    if size_mb > 50:
        print(f"  Still too large! Reducing to top 50K subhalos...")
        order2 = order[:50000]
        data2 = {k: v[:50000] if len(v) > 50000 else v for k, v in data.items()}
        data2['pos'] = pos[order2].astype(np.float32)
        data2['mass'] = mass[order2].astype(np.float32)
        data2['grNr'] = grNr[order2].astype(np.int32) if grNr is not None else np.zeros(50000, dtype=np.int32)
        outfile2 = os.path.join(OUTPUT_DIR, f"tng_slim_{label}_50k.npz")
        np.savez_compressed(outfile2, **data2)
        size2 = os.path.getsize(outfile2) / 1e6
        print(f"  SAVED: {outfile2} ({size2:.1f} MB)")

# ============================================================
print("="*60)
print("SLIM TNG EXTRACTION")
print("="*60)

for label, path in PATHS.items():
    print(f"\n--- {label} ---")
    
    # Try the path as-is first
    if os.path.exists(path):
        extract_slim(path, label)
        continue
    
    # Try common variations (spaces, typos)
    found = False
    variations = [
        path,
        path.replace(" -", "-"),
        path.replace("- ", "-"),
        path.replace("TND", "TNG"),
        path.replace("TNG3001", "TNG300-1"),
        path.replace("TND3001", "TNG300-1"),
        path.replace("datacat", "groupcat"),
        path.replace("datacat", "GroupCat"),
    ]
    for alt in variations:
        if os.path.exists(alt):
            print(f"  Found at: {alt}")
            extract_slim(alt, label)
            found = True
            break
    
    if not found:
        print(f"  PATH NOT FOUND: {path}")
        print(f"  Tried variations: {[v for v in variations if v != path][:3]}")
        parent = os.path.dirname(path)
        if os.path.exists(parent):
            print(f"  Contents of parent ({parent}):")
            for item in sorted(os.listdir(parent)):
                print(f"    {item}")
        print()
        print(f"  Please edit this script and fix the path for '{label}'")

print()
print("="*60)
print("UPLOAD THESE FILES TO CLAUDE:")
for label in PATHS:
    for suffix in ["", "_50k"]:
        f = os.path.join(OUTPUT_DIR, f"tng_slim_{label}{suffix}.npz")
        if os.path.exists(f):
            s = os.path.getsize(f) / 1e6
            print(f"  {os.path.basename(f):30s}  {s:6.1f} MB")
print("="*60)
