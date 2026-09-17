#!/usr/bin/env python3
import glob,hashlib,sys
parts=sorted(glob.glob('batch2-all-approved-cleaned-20260917.zip.part-*'))
out='batch2-all-approved-cleaned-20260917.zip'
with open(out,'wb') as o:
    for p in parts: o.write(open(p,'rb').read())
print('rebuilt',out,hashlib.sha256(open(out,'rb').read()).hexdigest())
