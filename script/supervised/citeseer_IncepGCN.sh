#!/bin/bash

for i in $(seq 0.05 0.05 0.95)
do
echo $i
python ./src/train_new.py \
    --debug \
    --datapath data// \
    --seed 42 \
    --dataset citeseer \
    --type inceptiongcn \
    --nhiddenlayer 1 \
    --nbaseblocklayer 6 \
    --hidden 128 \
    --epoch 400 \
    --lr 0.002 \
    --weight_decay 0.005 \
    --early_stopping 400 \
    --sampling_percent $i \
    --dropout 0.5 \
    --normalization BingGeNormAdj \
    --withloop
done
