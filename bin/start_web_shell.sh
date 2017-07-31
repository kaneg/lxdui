#!/usr/bin/env bash
./gotty -w -p 9090 --permit-arguments sh ./lxc_exec_bash.sh 1>/dev/null 2>&1