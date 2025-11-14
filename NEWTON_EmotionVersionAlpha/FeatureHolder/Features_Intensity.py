import numpy

class FeaturesIntensity:
    def __init__(self):
        self.NSyll = 0 
        self.PhonationTime = 0.0 
        self.NPause = 0
        self.MeanPauseDuration = 0.0 
        
        self.RMSList = []
        self.RMSMean = 0.0
        self.RMSStd = 0.0
    
    def TakeStats(self, IntenseObj, SoundDuration):
        self.NSyll = len(IntenseObj.maxima)
        
        self.RMSList = IntenseObj.RMSs
        if len(self.RMSList) > 0.0:
            self.RMSMean = numpy.mean(self.RMSList)
            self.RMSStd = numpy.std(self.RMSList)
        
        self.NPause = len(IntenseObj.Pauses)
        if self.NPause > 0:
            self.MeanPauseDuration = numpy.mean(IntenseObj.Pauses)
            
        self.PhonationTime = IntenseObj.PhonationTimeRatio * SoundDuration
        
        
        
        
        