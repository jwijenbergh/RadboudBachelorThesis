#!/usr/bin/env bash

if [ -d "$1" ]; then
	echo "DIRECTORY ALREADY EXISTS, EXITING..."
	exit
fi

mkdir -p $1

# Array declarations
declare -a concurrent_generators=(1 2 4 5 10 20 25 50 100)
declare -a batch_counts=(100 50 25 20 10 5 4 2 1)
declare -a test_names=("test1" "test2" "test3" "test4" "test5" "test5" "test6" "test7" "test8" "test9")

total_tests=${#test_names[@]}

for (( i=0; i<${total_tests}; i++ ));
do
	mkdir -p "$1/${test_names[$i]}"
	echo "STARTING EXPERIMENT" $((i+1))
	./scripts/send.sh "${batch_counts[$i]}" 100 "${concurrent_generators[$i]}" "$1/${test_names[$i]}"
	echo "WAITING..."
	sleep 10s
done
