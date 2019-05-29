from DataMgr import DataMgr
import json

class ResponseDataMgr(DataMgr):
    def __init__(self, inputsDir, labelsPath, logInfoFun=print):
        super().__init__(inputsDir, labelsPath, logInfoFun)
        self.m_labelsList = []
        self.getLabelsList()

    def getLabelsList(self):
        with open(self.m_labelsDir) as f:
            allPatientRespsDict = json.load(f)

        for latent in self.m_inputFilesList:
            patientID = self.getStemName(latent, "_Latent.npy")
            if len(patientID)>8:
                patientID = patientID[0:8]
            self.m_labelsList.append(allPatientRespsDict[patientID])


    def getCEWeight(self):
        labelPortion = [0.3, 0.7]  # this is portion of 0,1 label, whose sum = 1
        ceWeight = [0.0, 0.0]
        for i in range(2):
            ceWeight[i] = 1.0/labelPortion[i]
        self.m_logInfo(f"Infor: Cross Entropy Weight: {ceWeight} for label[0, 1]")
        return ceWeight
