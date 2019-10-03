echo "Doing udp on dns1.jwijenbergh.com and https GET on dns2.jwijenbergh.com"
echo "flamethrower command: -q $1 -Q $2 -c $3 -o $4"
~/Repos/flamethrower/build/flame -n 1 -q $1 -Q $2 -c $3 -P udp -f ~/measuring/queryfile dns1.jwijenbergh.com -o $4/udp.json &>/dev/null &
~/Repos/flamethrower/build/flame -n 1 -q $1 -Q $2 -c $3 -P https -M GET -f ~/measuring/queryfile dns2.jwijenbergh.com -o $4/https-get.json &>/dev/null &

wait
echo "First round done"
echo "Waiting 10 secs..."
sleep 10s


echo "Doing udp on dns1.jwijenbergh.com and https POST on dns2.jwijenbergh.com"
echo "flamethrower command: -q $1 -Q $2 -c $3 -o $4"

~/Repos/flamethrower/build/flame -n 1 -q $1 -Q $2 -c $3 -P udp -f ~/measuring/queryfile dns1.jwijenbergh.com &>/dev/null &
~/Repos/flamethrower/build/flame -n 1 -q $1 -Q $2 -c $3 -P https -M POST -f ~/measuring/queryfile dns2.jwijenbergh.com -o $4/https-post.json &>/dev/null &

wait
echo 'Done!'
