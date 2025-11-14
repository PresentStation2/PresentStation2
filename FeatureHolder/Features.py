import traceback

from FeatureHolder.Features_F0 import FeaturesF0
from FeatureHolder.Features_Intensity import FeaturesIntensity
from FeatureHolder.Features_VoiceColor import FeaturesVoiceColor

from F0.GenderEstimator import GenderEstimator
from sharedComponents.Gender import Gender


class Features:
    def __init__(self, logger):
        self.logger = logger
        self.F0 = FeaturesF0()
        self.Intensity = FeaturesIntensity()
        self.VoiceColor = FeaturesVoiceColor()
        
        # global and derived features
        self.Duration = 0.0
        self.Gender = Gender.X
        self.SpeechRate = 0.0
        self.ArticulationRate = 0.0

    
    def SetGender(self, G):
        self.Gender = G
    
    def TakeF0Stats(self, F0Obj):
        try:
            self.F0.TakeStats(F0Obj)
            GEst = GenderEstimator()
            self.Gender = GEst.LenkaTree(self.F0.Mean, self.F0.Min, self.F0.Q10)            
        except:
            self.logger.error( str(traceback.format_exc(limit=None, chain=True)) )
    
    def TakeIntensity(self, InteneseObj):
        try:
            self.Intensity.TakeStats(InteneseObj, self.Duration) 
            self.SpeechRate = self.getSpeechRate()
            self.ArticulationRate = self.getArticulationRate()           
        except:
            self.logger.error( str(traceback.format_exc(limit=None, chain=True)) )    

    def getSpeechRate(self):
        return float(self.Intensity.NSyll) / self.Duration
    def getArticulationRate(self):
        return float(self.Intensity.NSyll) / self.Intensity.PhonationTime
    
    
    def TakeVoiceColor(self, IPUHolder):
        try:
            self.VoiceColor.TakeStats(IPUHolder)            
        except:
            self.logger.error( str(traceback.format_exc(limit=None, chain=True)) )        
        
        