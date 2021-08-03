#!/usr/bin/env python

#In termina:
	#conda activate NormCheck
	#cd ~/home/katie/SNAP/Projects/fMRIPrep/katie/Code/NormCheck.py
	#python NormCheck.py filepath/filename1.nii.gz
	
import sys
import numpy as np
import nibabel as nb


def test(img):
    zooms = np.array([img.header.get_zooms()[:3]])
    A = img.affine[:3, :3]
    
    cosines = A / zooms
    diff = A - cosines * zooms.T

    return not np.allclose(diff, 0), np.max(np.abs(diff))


if __name__ == "__main__":
    for fname in sys.argv[1:]:
        affected, severity = test(nb.load(fname))
        print(f"{fname} is affected ({severity=})")
        if affected:
            print(f"{fname} is affected ({severity=})")

