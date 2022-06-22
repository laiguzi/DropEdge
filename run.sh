#!/bin/bash

for i in $(seq 0 1 2)
do
echo 'run '$i >> 'test.txt'
sh ./script/supervised/SBM_IncepGCN.sh 
done
