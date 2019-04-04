import sys
import os
import datetime
import torch
import torch.nn as nn
import torch.optim as optim

torchSummaryPath = "/home/hxie1/Projects/pytorch-summary/torchsummary"
sys.path.append(torchSummaryPath)
from torchsummary import summary

from DataMgr import DataMgr
from SegVModel import SegVModel
from NetMgr  import NetMgr

def printUsage(argv):
    print("============Test Ovarian Cancer Segmentation V model=============")
    print("read all test files, and output their segmentation results.")
    print("Usage:")
    print(argv[0], "<netSavedPath> <fullPathOfTestImages>  <fullPathOfTestLabels>")

def main():
    curTime = datetime.datetime.now()
    print('Program starting Time: ', str(curTime))

    if len(sys.argv) != 4:
        print("Error: input parameters error.")
        printUsage(sys.argv)
        return -1

    netPath = sys.argv[1]
    testDataMgr = DataMgr(sys.argv[2], sys.argv[3])
    testDataMgr.setDataSize(32, 21, 281, 281, 4)  # batchSize, depth, height, width, k


    net= SegVModel()
    net.printParametersScale()

    lossFunc = nn.CrossEntropyLoss()
    net.setLossFunc(lossFunc)

    netMgr = NetMgr(net)
    if 0 != len(os.listdir(netPath)):
        netMgr.loadNet(netPath, False)  # False for train
    else:
        print(f"Program can not find trained network in path: {netPath}")
        sys.exit()

    useDataParallel = True

    # print model
    print("\n====================Net Architecture===========================")
    summary(net.cuda(), testDataMgr.getInputSize())
    print("===================End of Net Architecture =====================\n")

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    if useDataParallel:
        nGPU = torch.cuda.device_count()
        if nGPU >1:
            print(f'Info: program will use {nGPU} GPUs.')
            net = nn.DataParallel(net)
    net.to(device)

    K = testDataMgr.getNumClassification()
    print("Hints: TestDice_0 is the dice coeff for all non-zero labels")
    print("Hints: TestDice_1 is for primary cancer(green), testDice_2 is for metastasis(yellow), and testDice_3 is for invaded lymph node(brown).\n")
    diceHead = (f'TestDice_{i}' for i in range(K))
    print(f"Epoch \t TrainingLoss \t TestLoss \t\t", '\t\t'.join(diceHead))   # print output head

    net.eval()
    nSamples = 0
    with torch.no_grad():
        diceList = [0 for _ in range(K)]
        testLoss = 0.0
        batches = 0
        for inputs, labelsCpu in testDataMgr.dataLabelGenerator(False):
            nSamples += inputs.shape[0]  # for dynamic batchSize
            inputs, labels = torch.from_numpy(inputs), torch.from_numpy(labelsCpu)
            inputs, labels = inputs.to(device, dtype=torch.float), labels.to(device, dtype=torch.long)  # return a copy

            outputs = net.forward(inputs)
            loss = lossFunc(outputs, labels)
            batchLoss = loss.item()

            # TODO: add output files
            outputs = outputs.cpu().numpy()

            diceSumBatch = testDataMgr.getDiceSumList(outputs, labelsCpu)
            diceList = [x+y for x,y in zip(diceList, diceSumBatch)]
            testLoss += batchLoss
            batches += 1
            #print(f'batch={batches}: batchLoss = {batchLoss}')

    #===========print train and test progress===============
    testLoss /= batches
    diceList = [x/nSamples for x in diceList]
    print(f'{0} \t\t {0:.7f} \t\t {testLoss:.7f} \t\t', '\t\t\t'.join( (f'{x:.4f}' for x in diceList)))

    print(f'\nTotal test {nSamples} images in {sys.argv[2]}.')

    torch.cuda.empty_cache()
    print("=============END of Test of Ovarian Cancer Segmentation V Model =================")

if __name__ == "__main__":
    main()