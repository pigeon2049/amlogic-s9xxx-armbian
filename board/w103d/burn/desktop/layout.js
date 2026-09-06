// SPDX-License-Identifier: GPL-2.0-only
// Applied once to the factory desktop account, never on subsequent logins.
panels().forEach(function (panel) { panel.remove(); });
var top = new Panel;
top.location = 'top'; top.height = 34; top.floating = false;
top.addWidget('org.kde.plasma.kickoff');
top.addWidget('org.kde.plasma.windowlist');
top.addWidget('org.kde.plasma.appmenu');
top.addWidget('org.kde.plasma.panelspacer');
var clock = top.addWidget('org.kde.plasma.digitalclock');
clock.currentConfigGroup = ['Appearance'];
clock.writeConfig('showSeconds', 0);
clock.writeConfig('showDate', true);
clock.writeConfig('dateFormat', 'shortDate');
top.addWidget('org.kde.plasma.panelspacer');
top.addWidget('org.kde.plasma.systemtray');
var dock = new Panel;
dock.location = 'bottom'; dock.height = 58;
dock.alignment = 'center'; dock.lengthMode = 'fit'; dock.floating = true;
dock.hiding = 'dodgewindows';
var tasks = dock.addWidget('org.kde.plasma.icontasks');
tasks.currentConfigGroup = ['General'];
tasks.writeConfig('launchers', ['applications:org.kde.dolphin.desktop', 'applications:firefox-esr.desktop', 'applications:org.kde.konsole.desktop', 'applications:org.kde.kate.desktop', 'applications:systemsettings.desktop']);
function colorize(panel, settings) {
    var widget = panel.addWidget('luisbocanegra.panel.colorizer');
    widget.currentConfigGroup = ['General'];
    widget.writeConfig('hideWidget', true);
    widget.writeConfig('globalSettings', JSON.stringify(settings));
}
// The pinned upstream presets are substituted by prepare-layout.py.
colorize(top, TOP_SETTINGS);
colorize(dock, DOCK_SETTINGS);
desktops().forEach(function (desktop) {
    desktop.wallpaperPlugin = 'org.kde.image';
    desktop.currentConfigGroup = ['Wallpaper', 'org.kde.image', 'General'];
    desktop.writeConfig('Image', 'file:///usr/share/wallpapers/W103D.png');
});
