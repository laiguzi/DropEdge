import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from layers import *
from torch.nn.parameter import Parameter

device = torch.device("cuda:0")


class GCNModel(nn.Module):
    """
       The model for the single kind of deepgcn blocks.

       The model architecture likes:
       inputlayer(nfeat)--block(nbaselayer, nhid)--...--outputlayer(nclass)--softmax(nclass)
                           |------  nhidlayer  ----|
       The total layer is nhidlayer*nbaselayer + 2.
       All options are configurable.
    """

    def __init__(self,
                 nfeat, # 1433
                 nhid,  # 128
                 nclass, # 7
                 nhidlayer, # 1
                 dropout, # 0.5
                 baseblock="multigcn",
                 inputlayer="gcn",
                 outputlayer="gcn",
                 nbaselayer=0, # 6
                 activation=lambda x: x,
                 withbn=True,  # False
                 withloop=True, # False
                 aggrmethod="add", # default
                 mixmode=False,
                 sampler=None,
                 percent=None,
                 normalization=None,
                 use_cuda=False):
        """
        Initial function.
        :param nfeat: the input feature dimension.
        :param nhid:  the hidden feature dimension.
        :param nclass: the output feature dimension.
        :param nhidlayer: the number of hidden blocks.
        :param dropout:  the dropout ratio.
        :param baseblock: the baseblock type, can be "multigcn", "resgcn", "densegcn" and "inceptiongcn".
        :param inputlayer: the input layer type, can be "gcn", "dense", "none".
        :param outputlayer: the input layer type, can be "gcn", "dense".
        :param nbaselayer: the number of layers in one hidden block.
        :param activation: the activation function, default is ReLu.
        :param withbn: using batch normalization in graph convolution.
        :param withloop: using self feature modeling in graph convolution.
        :param aggrmethod: the aggregation function for baseblock, can be "concat" and "add". For "resgcn", the default
                           is "add", for others the default is "concat".
        :param mixmode: enable cpu-gpu mix mode. If true, put the inputlayer to cpu.
        """
        super(GCNModel, self).__init__()
        self.mixmode = mixmode
        self.dropout = dropout
        self.percent = percent
        self.normalization = normalization
        self.use_cuda = use_cuda

        if baseblock == "resgcn":
            self.BASEBLOCK = ResGCNBlock
        elif baseblock == "densegcn":
            self.BASEBLOCK = DenseGCNBlock
        elif baseblock == "multigcn":
            self.BASEBLOCK = MultiLayerGCNBlock
        elif baseblock == "inceptiongcn":
            self.BASEBLOCK = InceptionGCNBlock
        else:
            raise NotImplementedError("Current baseblock %s is not supported." % (baseblock))
        if inputlayer == "gcn":
            # input gc
            self.ingc = GraphConvolutionBS(nfeat, nhid, activation, withbn, withloop)
            baseblockinput = nhid
        elif inputlayer == "none":
            self.ingc = lambda x: x
            baseblockinput = nfeat
        else:
            self.ingc = Dense(nfeat, nhid, activation)
            baseblockinput = nhid

        outactivation = lambda x: x
        if outputlayer == "gcn":
            self.outgc = GraphConvolutionBS(baseblockinput, nclass, outactivation, withbn, withloop)
        # elif outputlayer ==  "none": #here can not be none
        #    self.outgc = lambda x: x
        else:
            self.outgc = Dense(nhid, nclass, activation)

        # hidden layer
        self.midlayer = nn.ModuleList()
        # Dense is not supported now.
        # for i in xrange(nhidlayer):
        for i in range(nhidlayer): # 1
            gcb = self.BASEBLOCK(in_features=baseblockinput, # 128
                                 out_features=nhid, # 128
                                 nbaselayer=nbaselayer, # 6
                                 withbn=withbn, # False
                                 withloop=withloop, # False
                                 activation=activation, # x:x
                                 dropout=dropout, # 0.5
                                 dense=False,
                                 aggrmethod=aggrmethod) # concat
            self.midlayer.append(gcb)
            baseblockinput = gcb.get_outdim()
        # output gc
        outactivation = lambda x: x  # we donot need nonlinear activation here.
        self.outgc = GraphConvolutionBS(baseblockinput, nclass, outactivation, withbn, withloop)

        self.reset_parameters()
        if mixmode:
            self.midlayer = self.midlayer.to(device)
            self.outgc = self.outgc.to(device)

        if sampler:
            self.sampler = sampler

    def reset_parameters(self):
        pass

    def forward(self, fea, adj):

        #adj0, _ = self.sampler.curv_sampler(self.percent, self.normalization, self.use_cuda)

        # input
        if self.mixmode:
            x = self.ingc(fea, adj.cpu())
        else:
            x = self.ingc(fea, adj)

        x = F.dropout(x, self.dropout, training=self.training)
        if self.mixmode:
            x = x.to(device)
        # x: 2708 x 128

        # mid block connections
        # for i in xrange(len(self.midlayer)):
        for i in range(len(self.midlayer)): # 1
            midgc = self.midlayer[i]
            #adj0, _ = self.sampler.curv_sampler(self.percent, self.normalization, self.use_cuda)
            x = midgc(x, adj) # -> x: 2708 x 896
        # output, no relu and dropput here.
        #adj0, _ = self.sampler.curv_sampler(self.percent, self.normalization, self.use_cuda)
        x = self.outgc(x, adj) # -> x: 2708 x 7
        x = F.log_softmax(x, dim=1)
        return x


# Modified GCN
class GCNFlatRes(nn.Module):
    """
    (Legacy)
    """
    def __init__(self, nfeat, nhid, nclass, withbn, nreslayer, dropout, mixmode=False):
        super(GCNFlatRes, self).__init__()

        self.nreslayer = nreslayer
        self.dropout = dropout
        self.ingc = GraphConvolution(nfeat, nhid, F.relu)
        self.reslayer = GCFlatResBlock(nhid, nclass, nhid, nreslayer, dropout)
        self.reset_parameters()

    def reset_parameters(self):
        # stdv = 1. / math.sqrt(self.attention.size(1))
        # self.attention.data.uniform_(-stdv, stdv)
        # print(self.attention)
        pass

    def forward(self, input, adj):
        x = self.ingc(input, adj)
        x = F.dropout(x, self.dropout, training=self.training)
        x = self.reslayer(x, adj)
        # x = F.dropout(x, self.dropout, training=self.training)
        return F.log_softmax(x, dim=1)


