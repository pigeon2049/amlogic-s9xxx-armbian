#!/bin/sh
if [ "$(id -u)" = 0 ] && [ -f /root/.not_logged_in_yet ] && [ -t 0 ]; then
    /usr/local/sbin/w103d-first-login
fi
