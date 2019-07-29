# ResNeXt Block
import torch.nn as nn
import torch.nn.functional as F

class ResNeXtBlock(nn.Module):
    """
    RexNeXt bottleneck type C (https://github.com/facebookresearch/ResNeXt/blob/master/models/resnext.lua)
    """
    def __init__(self, inChannels, outChannels, nGroups, poolingLayer=None, stride=1):
        super().__init__()

        self.m_poolingLayer = poolingLayer

        self.m_reduceConv = nn.Conv2d(inChannels, inChannels, kernel_size=1, stride=1, padding=0, bias=False)
        self.m_reduceBN = nn.BatchNorm2d(inChannels)

        self.m_groupConv = nn.Conv2d(inChannels, inChannels, kernel_size=3, stride=stride, padding=1, groups=nGroups, bias=False)
        self.m_groupBN = nn.BatchNorm2d(inChannels)

        self.m_expandConv = nn.Conv2d(inChannels, outChannels, kernel_size=1, stride=1, padding=0, bias=False)
        self.m_expandBN = nn.BatchNorm2d(outChannels)

        if inChannels != outChannels or stride != 1:
            self.m_identityConv = nn.Conv2d(inChannels, outChannels, kernel_size=1 if stride==1 else 3, stride=stride, padding=0 if stride==1 else 1, bias=False)
            self.m_identityBN = nn.BatchNorm2d(outChannels)
        else:
            self.m_identityConv = None
            self.m_identityBN = None

    def forward(self, x):
        if self.m_poolingLayer:
            x = self.m_poolingLayer(x)

        y = self.m_reduceConv(x)
        y = F.relu(self.m_reduceBN(y), inplace=True)

        y = self.m_groupConv(y)
        y = F.relu(self.m_groupBN(y), inplace=True)

        y = self.m_expandConv(y)
        y = self.m_expandBN(y)

        if self.m_identityConv and self.m_identityBN:
            x = self.m_identityConv(x)
            x = self.m_identityBN(x)

        return F.relu(x + y, inplace=True)
