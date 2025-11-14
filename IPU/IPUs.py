from IPU.IPUobject import IPUobject

class IPUs():
    def __init__(self, logger, cfg):
        #=======================================================================
        # IntensityPeakUnit ... word/syllable like part of speech
        # for IPUs ranges mean spectrum will be extracted
        # F0 and formants make sense inside IPUs ...
        #=======================================================================
        self.logger = logger
        self.config = cfg
        self.IPUobjects = []
                

    
    def GetTimeIntervals(self, IntensityObject):
        for bg,nd in IntensityObject.IPUs:
            start, end = IntensityObject.timeCenters[bg], IntensityObject.timeCenters[nd]
            self.IPUobjects.append(IPUobject(start, end, self.config))
    
    def GetF0(self, F0Xtractor):        
        lastStart = 0
        for ipu in self.IPUobjects:
            lastStart = ipu.getF0data(F0Xtractor, lastStart) 
            
    def GetFormants(self, FormantXtractor):
        lastStart = 0
        for ipu in self.IPUobjects:
            lastStart = ipu.getFormant(FormantXtractor, lastStart)

    def GetSpectra(self, audio):
        for ipu in self.IPUobjects:
            if ipu.IsRelevant():
                ipu.ProcessSpectrum(audio)

        