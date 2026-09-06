#!/usr/bin/python3
# SPDX-License-Identifier: GPL-2.0-only
import json, pathlib, sys
src = pathlib.Path(__file__).parent
presets = pathlib.Path('/usr/share/plasma/plasmoids/luisbocanegra.panel.colorizer/contents/ui/presets')
top = json.loads((presets/'ChromeOS/settings.json').read_text())['globalSettings']
dock = json.loads((presets/'Translucent/settings.json').read_text())['globalSettings']
top['panel']['normal']['backgroundColor']['enabled'] = False
def light_foreground(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == 'foregroundColor' and isinstance(value, dict):
                value.update(enabled=True, sourceType=0, custom='#f5e7e5', alpha=1)
            else:
                light_foreground(value)
light_foreground(top)
for p in [top, dock]:
    p['panel']['normal']['blurBehind'] = False
text = (src/'layout.js').read_text().replace('TOP_SETTINGS',json.dumps(top)).replace('DOCK_SETTINGS',json.dumps(dock))
pathlib.Path(sys.argv[1]).write_text(text)
