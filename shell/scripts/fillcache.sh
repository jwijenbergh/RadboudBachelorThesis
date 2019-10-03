#!/usr/bin/env bash

echo "Filling cache...."
~/Repos/flamethrower/build/flame -n 1 -Q 100 -c 2 -P udp -f ~/measuring/queryfile dns1.jwijenbergh.com &>/dev/null &
~/Repos/flamethrower/build/flame -n 1 -Q 100 -c 2 -P udp -f ~/measuring/queryfile dns2.jwijenbergh.com &>/dev/null &

wait
echo "Done filling the cache"
