from BasicModel import BasicModel
from BuildingBlocks import *
import torch

# SkyWatcher Model, simultaneously train segmentation and treatment response

class SkyWatcherModel(BasicModel):
    def __init__(self):
        super().__init__()

    def encoderForward(self, inputx):
        x = self.m_input(inputx)
        for down in self.m_downList:
            x = down(x)
        # here x is the output at crossing point of sky watcher
        return x

    def responseForward(self, crossingx):
        # xr means x rightside output, or response output
        xr = crossingx
        xr = self.m_11Conv(xr)
        xr = torch.reshape(xr, (xr.shape[0], xr.numel()//xr.shape[0]))
        xr = self.m_fc11(xr)
        return xr

    def decoderForward(self, crossingx):
        # xup means the output using upList
        xup = crossingx
        for up in self.m_upList:
            xup = up(xup)
        xup = self.m_upOutput(xup)
        return xup


    def forward(self, inputx, bPurePrediction=False):
        x = self.encoderForward(inputx)
        xr = self.responseForward(x)
        if bPurePrediction:
            return xr
        else:
            xup = self.decoderForward(x)
            return xr, xup

