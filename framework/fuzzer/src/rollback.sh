#!/bin/bash
telnet localhost 3133 <<EOF
{"execute" : "qmp_capabilities"}
{"execute":"human-monitor-command","arguments":{"command-line":"loadvm 1"}}
EOF
