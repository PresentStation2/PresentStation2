import numpy

class FeaturesF0:
    def __init__(self):
        self.Mean = 0.0
        self.Min = 0.0
        self.Max = 0.0
        self.Std = 0.0
        self.Q10 = 0.0
        self.Q90 = 0.0
        self.SemitoneRange = 0.0 
    
    def TakeStats(self, FOXtractor):
        f0Stats = FOXtractor.GetF0Stats()
        
        self.Mean = f0Stats['mean']
        self.Min = f0Stats['min']
        self.Max = f0Stats['max']
        self.Std = f0Stats['std']
        self.Q10 = f0Stats['q10']
        self.Q90 = f0Stats['q90']
        self.SemitoneRange = 12.0 * numpy.log(self.Max / self.Min) / numpy.log(2)
        
