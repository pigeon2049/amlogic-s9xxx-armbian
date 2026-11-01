#!/bin/bash
for s in $(awk '/^\/dev\/zram/ {print $1}' /proc/swaps); do
    swapoff "$s" 2>/dev/null || true
done
