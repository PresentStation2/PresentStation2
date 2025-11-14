from sharedComponents.Gender import Gender

class GenderEstimator:
    def __init__(self):
        pass
    
    def LenkaTree(self, meanF0, minF0, q10F0):
        Mpoints = 0.0
        Fpoints = 0.0
        
        if meanF0 <= 138.5:
            Mpoints += 100.0
        elif 138.5 < meanF0 <= 151.7:
            Mpoints += 93.3
            Fpoints +=  6.7
        elif 151.7 < meanF0 <= 172.9:
            Mpoints += 56.7
            Fpoints += 43.3
        elif 172.9 < meanF0 <= 211.0:
            Mpoints += 15.6
            Fpoints += 84.5
        else:# if meanF0 > 211.0:
            Mpoints +=  1.1
            Fpoints += 98.9
        
        
        if minF0 > 118.2:
            Mpoints +=  4.4
            Fpoints += 95.6
        else:
            Mpoints += 55.2
            Fpoints += 44.8                       

    
        if q10F0 <= 124.5:
            Mpoints += 75.0
            Fpoints += 25.0
        elif 124.5 < q10F0 <= 135.7:
            Mpoints += 53.3
            Fpoints += 46.7                    
        elif 135.7 < q10F0 <= 163.4:
            Mpoints += 20.0
            Fpoints += 80.0
        else:# if q10F0 > 163.4:
            Mpoints +=  2.2
            Fpoints += 97.8
        
        if Fpoints > Mpoints:
            return Gender.F
        else:
            return Gender.M