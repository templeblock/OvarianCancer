import torch.nn.functional as F
from torch.nn.modules.loss import _WeightedLoss, _Loss
from torch._jit_internal import weak_module, weak_script_method
import torch
from scipy import ndimage
from scipy.ndimage.morphology import binary_dilation
import numpy as np


@weak_module
class FocalCELoss(_WeightedLoss):
    """
    Focal Loss, please refer paper: "Focal Loss for Dense Object Detection" in link: https://arxiv.org/abs/1708.02002
    """
    __constants__ = ['weight', 'ignore_index', 'reduction']

    def __init__(self, weight=None, gamma =2.0, size_average=None, ignore_index=-100, reduce=None, reduction='mean'):
        super().__init__(weight, size_average, reduce, reduction)
        self.gamma = gamma
        self.ignore_index = ignore_index

    @weak_script_method
    def forward(self, inputx, target):
        focalFactor = (1 - F.softmax(inputx, 1)) ** self.gamma
        return F.nll_loss(focalFactor * F.log_softmax(inputx, 1), target, self.weight, None, self.ignore_index, None, self.reduction)

    def setGamma(self,gamma):
        self.gamma = gamma


@weak_module
class BoundaryLoss(_Loss):
    """
    Boundary Loss, please refer paper: Boundary Loss for highly Unbalanced Segmentation, in link: https://arxiv.org/abs/1812.07032
    outside boundary, it is positive distance, a penalty to increase loss;
    inside  boundary, it is negative distance, a reward to reduce loss;
    Only support binary classification case now.
    """
    __constants__ = ['reduction']

    def __init__(self, lambdaCoeff=0.001, k=2, size_average=None, reduce=None, reduction='mean'):
        super().__init__(size_average, reduce, reduction)
        self.m_lambda=lambdaCoeff # weight coefficient
        self.m_k = k              # k classes classification, m_k=2 is for binary classification, etc


    @weak_script_method
    def forward(self, inputx, target):
        softmaxInput = F.softmax(inputx, 1)
        targetNumpy = target.cpu().numpy().astype(int)
        shape = targetNumpy.shape
        ndim = targetNumpy.ndim
        N = shape[0]     # batch Size
        dilateFilter = np.ones((3, 3), dtype=int)  # dilation filter for for 4-connected boundary
        ret = torch.tensor.zeros(N,1).cuda()

        for k in range(1,self.m_k):
            segProb = torch.narrow(softmaxInput,1, k,1)
            segProb = torch.squeeze(segProb, 1)

            targetk = (targetNumpy == k)
            targetkNot = (targetNumpy != k)
            levelSet = np.zeros(shape)

            for i in range(N):
                if np.count_nonzero(targetk) == 0:
                    continue
                boundary = binary_dilation(targetkNot[i],dilateFilter) & targetk[i]
                inside = targetk[i] - boundary
                signMatrix = inside*(-1)+ targetkNot[i]
                levelSet[i] = ndimage.distance_transform_edt(boundary==0)*signMatrix

            levelSetTensor = torch.from_numpy(levelSet).float().cuda()
            ret += torch.mean(segProb * levelSetTensor, dim=tuple([i for i in range(1,ndim)]))

        if self.reduction != 'none':
            ret = torch.mean(ret) if self.reduction == 'mean' else torch.sum(ret)
        return ret*self.m_lambda

