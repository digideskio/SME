#! /usr/bin/python
from FB15k_exp import *

launch(datapath='./data/',
    dataset='NAACL', op='TransE', simfn='L1', ndim=50, nhid=50, marge=1., lremb=0.01, lrparam=1.,
    nbatches=100, totepochs=500, test_all=10, neval=1000, savepath='NAACL', Nent=28629, Nsyn=24518, Nrel=4111)

