import numpy

class FeaturesVoiceColor:
    def __init__(self):
        self.F1 = 0.0
        self.F2 = 0.0
        self.F3 = 0.0
        self.F2plusF3 = 0.0
        self.H1minusH2 = 0.0
        self.H1minusH2_std = 0.0
        self.H1minusA1 = 0.0
        self.H1minusA1_std = 0.0
        self.H1minusA2 = 0.0
        self.H1minusA2_std = 0.0        
        self.H1minusA3 = 0.0
        self.H1minusA3_std = 0.0
        
    
    def TakeStats(self, IPUHolder):
        F1, F2, F3 = [],[],[]
        F2plusF3 = []
        H1minusH2 = []
        H1minusA1 = []
        H1minusA2 = []
        H1minusA3 = []
         
        for ipu in IPUHolder.IPUobjects:
            if ipu.IsRelevant():
                f1,f2,f3 = ipu.F1, ipu.F2, ipu.F3
                F1.append(f1)
                F2.append(f2)
                F3.append(f3)
                F2plusF3.append(f2+f3)
                
                h1, h2, a1, a2, a3 = ipu.H1, ipu.H2, ipu.A1, ipu.A2, ipu.A3
                 
                H1minusH2.append(h1-h2)
                H1minusA1.append(h1-a1)
                H1minusA2.append(h1-a2)
                H1minusA3.append(h1-a3)
        
        self.F1 = numpy.mean(F1)
        self.F2 = numpy.mean(F2)
        self.F3 = numpy.mean(F3)
        self.F2plusF3 = numpy.mean(F2plusF3)
        self.H1minusH2 = numpy.mean(H1minusH2)
        self.H1minusH2_std = numpy.std(H1minusH2)
        self.H1minusA1 = numpy.mean(H1minusA1)
        self.H1minusA1_std = numpy.std(H1minusA1)
        self.H1minusA2 = numpy.mean(H1minusA2)
        self.H1minusA2_std = numpy.std(H1minusA2)
        self.H1minusA3 = numpy.mean(H1minusA3)
        self.H1minusA3_std = numpy.std(H1minusA3)

        
