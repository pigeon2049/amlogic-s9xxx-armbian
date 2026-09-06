#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
"""Remove only the imported generic hook; keep other rc.local customizations."""
import pathlib,sys
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/')
path=root/'etc/rc.local'
if path.exists():
    content=path.read_text()
    lines=content.splitlines(keepends=True)
    updated=''.join(line for line in lines if line.strip()!='bash /etc/custom_service/start_service.sh &')
    if updated!=content:
        path.write_text(updated)
        print('Removed the failing generic startup hook; W103D uses its systemd services.')
