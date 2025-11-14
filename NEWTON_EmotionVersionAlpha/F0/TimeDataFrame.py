import numpy

class ACPeak():
    def __init__(self,f,s):
        self.frequency = f
        self.strength = s
        
        self.score = 0.0
        self.reachedFrom_frame = None
        self.reachedFrom_peak = None

class TDTaFrame():
    def __init__(self, tdta, wndw, voicedLogE, tCenter):
        self.tdta = numpy.multiply(tdta, wndw)
        self.autocorr = []
        self.peaks = []
        
        self.voicedLogE = voicedLogE
        self.IsVoiced = False
        self.previousVoicedFrame = None
        
        self.TimeCenter = tCenter
    
    def ComputeAC(self):
        r2 = numpy.fft.ifft(numpy.abs(numpy.fft.fft(self.tdta))**2).real
        c=(r2/self.tdta.shape-numpy.mean(self.tdta)**2)/(numpy.std(self.tdta)**2+0.0000000001)
        self.autocorr = c[:len(self.tdta)//2]

        ELog = numpy.log(numpy.sum(numpy.square(self.tdta))+0.0000000001)
        self.IsVoiced = ELog > self.voicedLogE
               
    def FindPeaks(self, iFrom, iTo, FS, tryImprove=True):
        for pos in range(iFrom+1, iTo):
            if self.autocorr[pos-1] < self.autocorr[pos] and self.autocorr[pos] > self.autocorr[pos+1] and self.autocorr[pos] > 0.0:
                lag = pos if not tryImprove else self.ImprovePeak(pos, self.autocorr[pos-1], self.autocorr[pos], self.autocorr[pos+1])
    
                f = float(FS) / lag
                s = self.autocorr[pos]
                
                self.peaks.append(ACPeak(f,s))
        
    def ImprovePeak(self, pos, a, b, c):
        d1, d2 = b-a, b-c        
        rat = d1 / (d1+d2)        
        return pos-1+rat
    
    def ReducePeaks(self, minF0, maxF0):
        # remove weaker peaks (side maxima of sinc)
        self.Peaks_RemoveWeakNeighbours()
        # find freqs close to octaves and boost them
        self.Peaks_BoostByOctaves(boostFactor=0.1)
        # limit peaks to candidates in range
        self.Peaks_ApplyLimits(minF0, maxF0)              
    def Peaks_RemoveWeakNeighbours(self):
        if len(self.peaks) < 2:
            return
        
        lastAccepted = -1
        tempPeaks = sorted(self.peaks, key=lambda p: p.strength, reverse=True)
        
        while lastAccepted < len(tempPeaks)-1:
            lastAccepted += 1
            actualPeak = tempPeaks[lastAccepted]
            fFrom,fTo = 0.909*actualPeak.frequency, 1.1*actualPeak.frequency
            
            for i in range(len(tempPeaks)-1, lastAccepted, -1):
                if fFrom < tempPeaks[i].frequency < fTo and tempPeaks[i].strength < actualPeak.strength:
                    del(tempPeaks[i])
                    
        self.peaks = tempPeaks
    def Peaks_BoostByOctaves(self, boostFactor=0.5):
        
        for p in self.peaks:
            f1, f2 = 0.96*p.frequency, 1.04*p.frequency
            for b in self.peaks:
                for harm in range(2,5):
                    if f1 < harm*b.frequency < f2:
                        b.strength += boostFactor*p.strength
                        
    def Peaks_ApplyLimits(self, minF0, maxF0):
        for i in range(len(self.peaks)-1, -1, -1):
            if not (minF0 < self.peaks[i].frequency < maxF0):
                del(self.peaks[i])
    
    def addFramePeaks(self, newPeaks):
        for nP in newPeaks:
            closest,diff_x = 0.0, 100000.0
            for oP in self.peaks:
                diff = numpy.abs(nP.frequency-oP.frequency)
                if diff < diff_x:
                    closest = oP.frequency
                    diff_x = diff
            
            if closest == 0.0 or not (0.98 < nP.frequency/closest < 1.02):
                self.peaks.append( ACPeak(nP.frequency, nP.strength) )
    