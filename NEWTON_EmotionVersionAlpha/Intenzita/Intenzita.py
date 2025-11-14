import numpy
import scipy.signal
import copy

class SoundIntensity():
    def __init__(self, minPitch=50.0, timeStep=0.0, subtractMean=True, silenceDb=-25.0):
        minPitch = 2.0*minPitch
        self.minPitch = minPitch

        if timeStep <= 0.0:
            self.timeStep = 0.8 / minPitch 
        else:
            self.timeStep = timeStep
        
        self.subtractMean = subtractMean
        self.physicalWindowDuration = 6.4 / minPitch
        self.silenceDb = silenceDb
        
        self.intensities = []
        self.intensities_dB = []
        self.timeCenters = []
        
        self.dt = 0.0
        self.T = self.physicalWindowDuration
        
        self.maxima = []
        self.minima = []
        
        self.frameRMS = []
        self.RMSs = []
        self.Pauses = []
        self.VoicedIntervals = []
        
        self.PhonationTimeRatio = 0.0
        
        self.SpeechRate = 1.0
        self.ArticulationRate = 0.0

        self.VoicedDuration = 0.0
        self.soundDuration = 0.01

        self.IPUs = []
        
    def GetIntensity(self, sound, soundFS):
        self.dt = 1/float(soundFS)
        
        self.intensities = []
        windowLength = int(self.physicalWindowDuration * soundFS)
        if windowLength % 2 == 0:
            windowLength += 1
        windowCentreSampleNumber = (windowLength-1) / 2
        
        window = self.getWindow(windowLength, windowCentreSampleNumber, 1.0/float(soundFS))
        
        nFrames = int( ((float(sound.shape[0]) / float(soundFS)) - self.physicalWindowDuration) / self.timeStep )
        self.soundDuration = float(sound.shape[0]) / float(soundFS)
        
        for iFrame in range(nFrames):
            od = int( iFrame*self.timeStep * float(soundFS) )
            do = od + windowLength
            
            self.timeCenters.append(0.5*(od+do)/float(soundFS))

            audioChunk = sound[od:do]
            if self.subtractMean:
                audioChunk -= numpy.mean(audioChunk)
                
            self.frameRMS.append(sum(numpy.multiply(audioChunk, audioChunk)) / audioChunk.shape[0])
            
            windowed = numpy.multiply(audioChunk, window)

            STE = numpy.dot( windowed, windowed )
            
            # self.intensities.append( IntensityInfo( (od+do)*0.5/soundFS , STE) )
            self.intensities.append( STE )
    def getWindow(self, winLen, winCnt, dx):
        window = numpy.zeros(winLen)
        pom = dx / float(winCnt-1)
        for i in range(winLen):
            x = (1 + i - winCnt) * pom
            root = numpy.sqrt(max(0.0, 1.0-numpy.square(x)))
            window [i] = self.NUMbessel_i0_f((2.0 * numpy.pi * numpy.pi + 0.5) * root)
        
        return window        
    def NUMbessel_i0_f(self, x):
        if x < 0.0: 
            return self.NUMbessel_i0_f(-x)
        
        elif x < 3.75:
            t = x / 3.75
            return 1.0 + t * (3.5156229 + t * (3.0899424 + t * (1.2067492 + t * (0.2659732 + t * (0.0360768 + t * 0.0045813)))))
        
        else:
            t = 3.75 / x 
            return numpy.exp (x) / numpy.sqrt (x) * (0.39894228 + t * (0.01328592 + t * (0.00225319 + t * (-0.00157565 + t * (0.00916281 + t * (-0.02057706 + t * (0.02635537 + t * (-0.01647633 + t * 0.00392377))))))));
    
    def getIntensity_dB(self, sumX2):
        #=======================================================================
        # self.dt ... 1/FS of the signal
        # self.T  ... duration of 1 window
        #=======================================================================
        
        P0 = 0.00002
        return 10.0*numpy.log10( self.dt * sumX2 / self.T * P0 )
    
    def EstimateSilenceThreshold(self):
        # minIntensity = min(self.intensities)
        Intensity99 = numpy.percentile(self.intensities, 99)
        I99dB = self.getIntensity_dB(Intensity99)
        
        return I99dB - 25.0
        
    def GetIntensity_dB(self, sound, soundFS):
        self.GetIntensity(sound, soundFS)
        self.intensities_dB = []
        for intx in self.intensities:
            self.intensities_dB.append(self.getIntensity_dB(intx))

    def RemoveSilence(self, CFG):
        minSilDur, minVoicedDur = CFG.Intens_minSilentDuration, CFG.Intens_minVoicedDuration
        silThreshold = self.GetFilteredTreshold(CFG.Intens_VoiceSildB)
        # print(silThreshold)        
        self.RemoveEnergyNonSpeech(minSilDur, minVoicedDur, silThreshold)
        
        return(silThreshold)
        
    def GetFilteredTreshold(self, SilVoiceThresh):
        Intensity98 = numpy.percentile(self.intensities, 98)
        I98dB = self.getIntensity_dB(Intensity98)
         
        return I98dB - SilVoiceThresh

    def RemoveEnergyNonSpeech(self, minSilDur, minVoicedDur, silThreshold):
        # first: remove too short speechs blocks, then set too short non-speech as speech
        isVoiced = self.intensities_dB > silThreshold
        
        # find voiced part starts
        onsets = []
        if isVoiced[0] > 0.0:
            onsets.append(0)
        for i in range(len(isVoiced)-1):
            if isVoiced[i] == 0.0 and isVoiced[i+1] == 1.0:
                onsets.append(i)  
        
        if len(onsets) > 0 and onsets[-1] == len(isVoiced)-2:
            del(onsets[-1])
            isVoiced[-2] = 0.0
            isVoiced[-1] = 0.0
        
        # find voiced part ends     
        for onSet in onsets:
            for j in range(onSet+1, len(isVoiced)-1):
                end = j
                if isVoiced[j] == 1.0 and isVoiced[j+1] == 0.0:
                    break
                
            frameCount = end-onSet
            duration = (frameCount-1)*self.timeStep + self.physicalWindowDuration
            if duration < minVoicedDur:
                for k in range(onSet, end+1):
                    isVoiced[k] = 0.0
        
        # find unvoiced onsets
        onsets = []
        if isVoiced[0] == 0.0:
            onsets.append(0)

        for i in range(len(isVoiced)-1):
            if isVoiced[i] == 1.0 and isVoiced[i+1] == 0.0:
                onsets.append(i)
        
        # find unvoiced part ends
        for onSet in onsets:
            for j in range(onSet+1, len(isVoiced)-1):
                end = j
                if isVoiced[j] == 0.0 and isVoiced[j+1] == 1.0:
                    break
            
            frameCount = end-onSet
            duration = (frameCount-1)*self.timeStep + self.physicalWindowDuration
            if duration < minSilDur:
                for k in range(onSet, end+1):
                    isVoiced[k] = 1.0
                
        self.intensities_dB = numpy.multiply(self.intensities_dB, isVoiced)
        
    def FindPeaks(self, minDip, silThreshold):
        # origIntensity = self.intensities_dB
        self.intensities_dB = self.applySmallIntensityFilter([0.1, 0.2, 0.4, 0.2, 0.1])
        
        if len(self.intensities_dB) < 10:
            return
        
        potentialMaxima, self.minima = [], []
        dips = []
        
        for i in range(5):
            if self.intensities_dB[i] == min(self.intensities_dB[i:i+3]) and self.intensities_dB[i] < silThreshold:
                dips.append(i)
        
        for i in range(3,len(self.intensities_dB)-3):
            if self.intensities_dB[i] < 1.0:
                pass
            elif self.intensities_dB[i] == max(self.intensities_dB[i-3:i+4]):
                if self.intensities_dB[i] > silThreshold:
                    potentialMaxima.append(i)
            elif self.intensities_dB[i] == min(self.intensities_dB[i-2:i+3]):
                dips.append(i)
                
            # dips as borders of unvoiced
            elif self.intensities_dB[i] == min(self.intensities_dB[i-3:i+1]) and self.intensities_dB[i+1] == 0.0:
                dips.append(i)
            elif self.intensities_dB[i] == min(self.intensities_dB[i:i+4]) and self.intensities_dB[i-1] == 0.0:
                dips.append(i)
                
        for i in range(len(self.intensities_dB)-5, len(self.intensities_dB)):
            if self.intensities_dB[i] == max(self.intensities_dB[i:i+5]) and self.intensities_dB[i] < silThreshold:
                dips.append(i)

        self.maxima = potentialMaxima
        self.minima = dips
        
        self.ClearFalseIntensityPeaks(minDip)
        
        # merging of neibour peaks duplicates the winner
        self.maxima = list(set(self.maxima))
        self.maxima.sort()
        
        self.EvalPauseAndRMS()
    
    def ClearFalseIntensityPeaks(self, minDip):
        chosenMaxima = []
        self.unusedMinima = copy.deepcopy(self.minima)

        for mx in self.maxima:

            dipL, dipR = self.findMinLeft(mx, minDip), self.findMinRight(mx, minDip)
                
            if dipL == None or dipR == None:
                pass    # peak is not surrounded by sufficient dips
            else:
                peaksInDipRange = []
                
                for mrx in self.maxima:
                    if mx <= mrx < dipR:
                        peaksInDipRange.append(mrx)
                        
                winner, height = peaksInDipRange[0], self.intensities_dB[peaksInDipRange[0]]
                for p in peaksInDipRange:
                    if self.intensities_dB[p] > height:
                        winner, height = p, self.intensities_dB[p]
                
                if self.intensities_dB[dipL] < self.intensities_dB[winner]-minDip > self.intensities_dB[dipR]:
                    chosenMaxima.append(winner)
                
                    trmv = []
                    for i,mn in enumerate(self.unusedMinima):
                        if mn < winner:
                            trmv.append(i)
                    trmv.reverse()
                    for x in trmv:
                        del(self.unusedMinima[x])

        self.maxima = chosenMaxima        
        
    def findMinLeft(self, mx, minDip):
        firstDipAfter = None
        for i,mn in enumerate(self.unusedMinima):
            if mn > mx:
                firstDipAfter = i
                break
        
        if firstDipAfter == None:
            return None
    
        for potMin in range(firstDipAfter-1, -1, -1):
            pmn = self.unusedMinima[potMin]
            if (self.intensities_dB[mx] - self.intensities_dB[pmn]) > minDip:
                chosenLeft = pmn
                for j in range(potMin-1, -1, -1):
                    if self.unusedMinima[j] < mx:
                        del(self.unusedMinima[j])
                return chosenLeft
        
        return None
    
    
    def findMinRight(self, mx, minDip):
        firstDipBefore = None
        for i,mn in enumerate(self.unusedMinima):
            if mn > mx:
                break
            firstDipBefore = i

        if firstDipBefore == None:
            return None
            
        # must find dip as differnce of closest maxima and dip (not as actual maxima and dip)
        maximaToRight = []
        for mm in self.maxima:
            if mm >= mx:
                maximaToRight.append(mm)
                if mm - mx > 70 or len(maximaToRight) > 10:
                    break
            
        for potMin in range(firstDipBefore+1, min(len(self.unusedMinima), firstDipBefore+10) ):
            pmn = self.unusedMinima[potMin]
            
            actualClosePeak = mx
            for mtr in maximaToRight:
                if mtr < pmn:
                    actualClosePeak = mtr
                else:
                    break
            
            dipBase = self.intensities_dB[mx] - self.intensities_dB[pmn]
            dipActual = self.intensities_dB[actualClosePeak] - self.intensities_dB[pmn] 
            if dipBase > minDip or dipActual > minDip:
                return pmn
        
        return None
    
    def applySmallIntensityFilter(self, filtr):
        nCoeff = len(filtr)
        filtered = scipy.signal.convolve(self.intensities_dB, filtr, mode='full', method='auto')
                
        if nCoeff // 2 > 0:
            filtered = numpy.delete(filtered, range(nCoeff // 2))

        pom = filtered[:self.intensities_dB.shape[0]]

        return numpy.multiply(pom, self.intensities_dB > 0.0)
        
    def EvalPauseAndRMS(self):
        self.Pauses = self.getPauses()
        self.PhonationTimeRatio = numpy.sum(self.intensities_dB > 0.0) / float(len(self.timeCenters)) 
        
        self.VoicedIntervals = self.getVoicedIntervals()
        self.RMSs = []
        for vInt in self.VoicedIntervals:
            self.RMSs.append( numpy.mean(self.frameRMS[vInt[0]: vInt[1]+1]) )

        
    def getPauses(self):
        # get pauses without signal borders
        pauses = []
        
        firstDecrease = None
        for i in range(len(self.intensities_dB)-1):
            if self.intensities_dB[i] > 0.0 and self.intensities_dB[i+1] == 0.0:
                firstDecrease = i
                break
        
        if firstDecrease == None or firstDecrease > len(self.intensities_dB) - 10:
            return pauses
    
        lastDecrease = firstDecrease
        for i in range(firstDecrease, len(self.intensities_dB)-1):
            if self.intensities_dB[i] > 0.0 and self.intensities_dB[i+1] == 0.0:
                lastDecrease = i
            elif self.intensities_dB[i] == 0.0 and self.intensities_dB[i+1] > 0.0:
                pauses.append((lastDecrease, i))
        
        out = []
        for p in pauses:
            out.append(self.timeCenters[p[1]] - self.timeCenters[p[0]])
        
        return out
        
    def getVoicedIntervals(self):
        intervals = []
        
        firstStart = None
        if self.intensities_dB[0] > 0.0:
            firstStart = 0
        else:
            for i in range(len(self.intensities_dB)-1):
                if self.intensities_dB[i] == 0.0 and self.intensities_dB[i+1] > 0.0:
                    firstStart = i 
                    break                 
                 
        if firstStart == None:
            return(intervals)
        
        lastStart, lastDumped = firstStart, False
        for i in range(lastStart, len(self.intensities_dB)-1):
            if self.intensities_dB[i] == 0.0 and self.intensities_dB[i+1] > 0.0:
                lastStart = i
                lastDumped = False
            elif self.intensities_dB[i] > 0.0 and self.intensities_dB[i+1] == 0.0:
                intervals.append((lastStart, i))
                lastDumped = True
        
        if self.intensities_dB[-1] > 0.0 and not lastDumped:
            intervals.append((lastStart, len(self.intensities_dB)-1))
        
        return intervals
    
    def findIPUs(self):
        #==============================================
        # this should find IntensityPeakUnits ... 
        # areas around peaks with dips at least 17 dB 
        # therefore peak-count can be reduced
        #==============================================
        
        minima = copy.deepcopy(self.minima)
        revMinima = copy.deepcopy(minima)
        revMinima.reverse()
        maxima = copy.deepcopy(self.maxima)
        dipSize = 17.0
        self.IPUs = []
        if len(maxima) == 0:
            return
        
        stMx = maxima[0]
        stVal = self.intensities_dB[stMx]
        startDip = 0
        lastDip = -1
        for mn in revMinima:
            if mn >= lastDip and mn < stMx:
                mnVal = self.intensities_dB[mn]
                if stVal-mnVal > dipSize:
                    startDip = mn
                    break
                
        lastMax = -1
        
        for mx in maxima:
            mxVal = self.intensities_dB[mx]
            startingDip = lastDip
            if mx < lastMax:
                pass
            else:
                for mn in revMinima:
                    if lastDip <= mn < mx:
                        if mxVal - self.intensities_dB[mn] > dipSize:
                            startingDip = mn
                            break
                
                endingDip = None
                for mn in minima:
                    if mn > mx:
                        
                        mxVal = max(self.intensities_dB[mx:mn])
                        if mxVal - self.intensities_dB[mn] > dipSize:
                            endingDip = mn
                            break
                
                if endingDip == None:
                    endingDip = minima[-1]
                                
                self.IPUs.append(self.findLoudPart(mx, startingDip, endingDip, dipSize))

                for mx in maxima:
                    if mx < endingDip:
                        lastMax = mx+1 
                lastDip = endingDip

    def findLoudPart(self, mx, startingDip, endingDip, dBValue):
        # here we choose part of potencial IPU that is loud enough
        bgn,nd = mx-1, mx+1
        thresh = self.intensities_dB[mx]-dBValue
        for i in range(mx-1, startingDip-1, -1):
            if self.intensities_dB[i] > thresh:
                bgn = i
            else:
                break
        
        for i in range(mx+1, endingDip):
            if self.intensities_dB[i] > thresh:
                nd = i
            else:
                break

        return (bgn,nd)
        
        
        
        