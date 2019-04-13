import torch
import torch.nn as nn
import torch.nn.functional as F

from SegVModel import SegVModel

#  3D model

class SegV3DModel (SegVModel):
    def __init__(self):
        super().__init__()

        self.m_conv1 = nn.Conv3d(1, 32, (5, 5, 5), stride=(2, 2, 2))  # inputSize: 21*281*281; output:32*9*139*139
        self.m_bn1 = nn.BatchNorm3d(32)
        self.m_conv2 = nn.Conv3d(32, 64, (5, 3, 3), stride=(2, 2, 2))  # output: 64*3*69*69
        self.m_bn2 = nn.BatchNorm3d(64)
        self.m_conv3 = nn.Conv3d(64, 128, (3, 5, 5), stride=(2, 2, 2))  # output: 128*1*33*33
        self.m_bn3 = nn.BatchNorm3d(128)
        self.m_conv4 = nn.Conv2d(128, 256, (5, 5), stride=(2, 2))  # output: 256*15*15
        self.m_bn4 = nn.BatchNorm2d(256)
        self.m_conv5 = nn.Conv2d(256, 512, (3, 3), stride=(2, 2))  # output: 512*7*7
        self.m_bn5 = nn.BatchNorm2d(512)
        self.m_conv6 = nn.Conv2d(512, 512, (3, 3), stride=(2, 2))  # output: 512*3*3
        self.m_bn6 = nn.BatchNorm2d(512)

        self.m_convT6 = nn.ConvTranspose2d(512, 512, (3, 3), stride=(2, 2))  # output: 512*7*7
        self.m_bnT6 = nn.BatchNorm2d(512)
        self.m_convT5 = nn.ConvTranspose2d(1024, 256, (3, 3), stride=(2, 2))  # output: 256*15*15
        self.m_bnT5 = nn.BatchNorm2d(256)
        self.m_convT4 = nn.ConvTranspose2d(512, 128, (5, 5), stride=(2, 2))  # output: 128*33*33
        self.m_bnT4 = nn.BatchNorm2d(128)
        self.m_convT3 = nn.ConvTranspose3d(256, 64, (3, 5, 5), stride=(2, 2, 2))  # output: 64*3*69*69
        self.m_bnT3 = nn.BatchNorm3d(64)
        self.m_convT2 = nn.ConvTranspose3d(128, 32, (5, 3, 3), stride=(2, 2, 2))  # output:32*9*139*139
        self.m_bnT2 = nn.BatchNorm3d(32)
        self.m_convT1 = nn.ConvTranspose3d(64, 1, (5, 5, 5), stride=(2, 2, 2))  # output:21*281*281
        self.m_bnT1 = nn.BatchNorm3d(1)
        self.m_conv0 = nn.Conv2d(42, 4, (1, 1), stride=1)  # output:4*281*281

    def forward(self, x):

        # without residual link within layer

        x1 = self.m_dropout3d( F.relu(self.m_bn1(self.m_conv1(x ))))     #Conv->BatchNorm->ReLU will keep half postive input.
        x2 = self.m_dropout3d( F.relu(self.m_bn2(self.m_conv2(x1))))
        x3 = self.m_dropout3d( F.relu(self.m_bn3(self.m_conv3(x2))))
        x3 = x3.squeeze(dim=2)                         # from 3D to 2D, there is squeeze
        x4 = self.m_dropout2d( F.relu(self.m_bn4(self.m_conv4(x3))))
        x5 = self.m_dropout2d( F.relu(self.m_bn5(self.m_conv5(x4))))
        xc = self.m_dropout2d( F.relu(self.m_bn6(self.m_conv6(x5))))  # xc means x computing
            
        xc = self.m_dropout2d( F.relu(self.m_bnT6(self.m_convT6(xc))))
        xc = torch.cat((xc,x5),1)                 # batchsize is in dim 0, so concatenate at dim 1.
        xc = self.m_dropout2d( F.relu(self.m_bnT5(self.m_convT5(xc))))
        xc = torch.cat((xc, x4), 1)
        xc = self.m_dropout2d( F.relu(self.m_bnT4(self.m_convT4(xc))))
        xc = torch.cat((xc, x3), 1)               # first concatenate with squeezed x3, then unsqueeze
        xc = xc.unsqueeze(2)
        xc = self.m_dropout3d( F.relu(self.m_bnT3(self.m_convT3(xc))))
        xc = torch.cat((xc, x2), 1)
        xc = self.m_dropout3d( F.relu(self.m_bnT2(self.m_convT2(xc))))
        xc = torch.cat((xc, x1), 1)
        xc = self.m_dropout3d( F.relu(self.m_bnT1(self.m_convT1(xc))))
        xc = torch.cat((xc, x), 2) # here concatenate at dim=2 is for further reducing dimension.
        xc = xc.squeeze(dim=1)

        xc = self.m_conv0(xc)


        #with residual link within layer: the expeiriment result is not good.
        '''
        x1 = self.m_conv1(x)
        x1 = self.m_dropout3d(F.relu(x1 + self.m_bn1(x1)))  # Conv->BatchNorm->ReLU will keep half postive input.
        x2 = self.m_conv2(x1)
        x2 = self.m_dropout3d(F.relu(x2 + self.m_bn2(x2)))
        x3 = self.m_conv3(x2)
        x3 = self.m_dropout3d(F.relu(x3 + self.m_bn3(x3)))
        x3 = x3.squeeze(dim=2)  # from 3D to 2D, there is squeeze

        x4 = self.m_conv4(x3)
        x4 = self.m_dropout2d(F.relu(x4 + self.m_bn4(x4)))
        x5 = self.m_conv5(x4)
        x5 = self.m_dropout2d(F.relu(x5 + self.m_bn5(x5)))
        xc = self.m_conv6(x5)
        xc = self.m_dropout2d(F.relu(xc + self.m_bn6(xc)))  # xc means x computing

        xc = self.m_convT6(xc)
        xc = self.m_dropout2d(F.relu(xc + self.m_bnT6(xc)))
        xc = torch.cat((xc, x5), 1)  # channel is in dim 0, so concatenate at dim 1.

        xc = self.m_convT5(xc)
        xc = self.m_dropout2d(F.relu(xc + self.m_bnT5(xc)))
        xc = torch.cat((xc, x4), 1)

        xc = self.m_convT4(xc)
        xc = self.m_dropout2d(F.relu(xc + self.m_bnT4(xc)))
        xc = torch.cat((xc, x3), 1)  # first concatenate with squeezed x3, then unsqueeze
        xc = xc.unsqueeze(2)

        xc = self.m_convT3(xc)
        xc = self.m_dropout3d(F.relu(xc + self.m_bnT3(xc)))
        xc = torch.cat((xc, x2), 1)

        xc = self.m_convT2(xc)
        xc = self.m_dropout3d(F.relu(xc + self.m_bnT2(xc)))
        xc = torch.cat((xc, x1), 1)

        xc = self.m_convT1(xc)
        xc = self.m_dropout3d(F.relu(xc + self.m_bnT1(xc)))
        xc = torch.cat((xc, x), 2)
        xc = xc.squeeze(dim=1)

        xc = self.m_conv0(xc)
        
        '''

        # return output
        return xc