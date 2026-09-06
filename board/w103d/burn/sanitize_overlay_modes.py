#!/usr/bin/env python3
"""Remove group/world write accidentally inherited from Windows root overlays.

Only root-owned paths on the root filesystem are considered. Sticky scratch
directories and mounted/runtime/user trees are excluded. Preserve all other
mode bits, including special bits on packaged executables.
"""
import argparse,json,os,pathlib,stat
p=argparse.ArgumentParser();p.add_argument('root',type=pathlib.Path);p.add_argument('--apply',action='store_true');a=p.parse_args()
root=a.root.resolve();dev=root.stat().st_dev
skip={'dev','proc','sys','run','tmp','mnt','media','home','lost+found','boot'}
changes=[]
for directory,dirs,files in os.walk(root,followlinks=False):
    d=pathlib.Path(directory)
    dirs[:]=[n for n in dirs if not (d/n).is_symlink() and (d/n).stat().st_dev==dev and not (d==root and n in skip)]
    for f in [d]+[d/n for n in files]:
        s=f.lstat();mode=stat.S_IMODE(s.st_mode)
        if s.st_uid or s.st_dev!=dev or not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):continue
        if not mode&0o002 or mode&stat.S_ISVTX:continue
        new=mode&~0o022
        changes.append(dict(path='/'+str(f.relative_to(root)),before=oct(mode),after=oct(new)))
        if a.apply:f.chmod(new)
print(json.dumps(dict(applied=a.apply,changes=changes),indent=2))
