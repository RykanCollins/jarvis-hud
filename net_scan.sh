#!/bin/bash
# Quick LAN scan — runs nmap ping sweep, caches result for 60s
CACHE=/tmp/jarvis_netscan.txt
MAX_AGE=60

if [ -f "$CACHE" ]; then
    age=$(( $(date +%s) - $(stat -c %Y "$CACHE") ))
    [ "$age" -lt "$MAX_AGE" ] && cat "$CACHE" && exit 0
fi

result=$(sudo nmap -sn 192.168.12.0/24 --host-timeout 3s 2>/dev/null \
    | awk '
        /Nmap scan report for/ {
            # extract IP — handle "hostname (IP)" or just "IP"
            line = $0
            if (match(line, /\(([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\)/, arr))
                ip = arr[1]
            else
                ip = $NF
            vendor = ""
        }
        /MAC Address:/ {
            mac = $3
            # vendor is everything after the MAC
            vendor = substr($0, index($0, $4))
            gsub(/^\(|\)$/, "", vendor)
            vendor = substr(vendor, 1, 18)
            printf "  %-16s %s\n", ip, vendor
            ip = ""
        }
        /Host is up/ && ip != "" {
            # no MAC line will follow for this host (it is us), print on next report
        }
        END {}
    ' \
    | head -12)

[ -z "$result" ] && result="  NO HOSTS FOUND"
echo "$result" > "$CACHE"
cat "$CACHE"
