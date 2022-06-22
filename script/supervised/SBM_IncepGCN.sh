#!/bin/bash

for i in $(seq 0.05 0.05 0.05)
do
echo $i
python ./src/train_new.py \
    --debug \
    --datapath data// \
    --seed 42 \
    --dataset SBM \
    --type inceptiongcn \
    --nhiddenlayer 1 \
    --nbaseblocklayer 0 \
    --hidden 128 \
    --epoch 400 \
    --lr 0.01 \
    --weight_decay 0.001 \
    --early_stopping 400 \
    --sampling_percent $i \
    --dropout 0.5 \
    --normalization AugNormAdj 
done
