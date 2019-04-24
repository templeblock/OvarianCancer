import torch.nn as nn
import torch


class SegVModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.m_dropoutProb = 0.2
        self.m_dropout3d = nn.Dropout3d(p=self.m_dropoutProb)
        self.m_dropout2d = nn.Dropout2d(p=self.m_dropoutProb)
        self.m_optimizer = None
        self.m_lossFuncList = []
        self.m_lossWeighList = []


    def forward(self, x):
        pass

    def setOptimizer(self, optimizer):
        self.m_optimizer = optimizer

    def appendLossFunc(self, lossFunc, weight = 1.0):
        self.m_lossFuncList.append(lossFunc)
        self.m_lossWeighList.append(weight)

    def batchTrain(self, inputs, labels):
        self.m_optimizer.zero_grad()
        outputs = self.forward(inputs)
        loss = torch.Tensor(0)
        for lossFunc, weight in zip(self.m_lossFuncList, self.m_lossWeighList):
            loss += lossFunc(outputs,labels)*weight
        loss.backward()
        self.m_optimizer.step()
        return loss.item()

    def batchTest(self, inputs, labels):
        outputs = self.forward(inputs)
        loss = torch.Tensor(0)
        for lossFunc, weight in zip(self.m_lossFuncList, self.m_lossWeighList):
            loss += lossFunc(outputs, labels) * weight
        return loss.item(), outputs

    def printParametersScale(self):
        sumPara = 0
        params = self.parameters()
        for param in params:
            sumPara += param.nelement()
        print(f"Network has total {sumPara} parameters.")

    def setDropoutProb(self, prob):
        self.m_dropoutProb = prob
        print(f"Info: network dropout rate = {self.m_dropoutProb}")
