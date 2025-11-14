from F0.TimeDataFrame import TDTaFrame, ACPeak

import traceback
import numpy


class F0Xtractor():
    def __init__(self, logger, CFG, minPeriodCount=3.0, window='hanning', octaveCost=5.0):
        self.logger = logger
        self.CFG = CFG
        
        try:
            self.FS = CFG.ffmpeg_FS
            self.minF0 = CFG.F0_minF0
            self.maxF0 = CFG.F0_maxF0
            self.sampleShift = max( int(float(self.FS) * CFG.F0_timeStep), 10)            
        except:
            self.logger.error('F0XTractor: probably error in ConfigHolder:')
            self.logger.error(str(traceback.format_exc(limit=None, chain=True)))        
        
        self.windowSize = int(minPeriodCount / self.minF0 * float(self.FS))
        
        self.frames = []
        self.window = numpy.hanning(self.windowSize)
        
        self.accIndFromValid = int(numpy.ceil( float(self.FS) / self.maxF0 ))
        self.accIndFromBoost = int( 0.45 * self.accIndFromValid )
        self.accIndTo = int(numpy.ceil( float(self.FS) / self.minF0 ))
        
        self.voicedLogEnergy = 0.0
        
        self.voicedCount = 0
        self.firstVoiced = 0
        self.lastVoiced = 0
        
        self.octaveCost = octaveCost
        
        self.F0Path = numpy.zeros(0)
        self.PathScore = 0.0
        
    def MakeFrames(self, monoAudio:numpy.array):
        self.GetVoicedEnergy(monoAudio)
        
        frameCount = 1 + (monoAudio.shape[0]-self.windowSize-10) // self.sampleShift
        
        for i in range(frameCount):
            tCntr = float(i*self.sampleShift + self.windowSize//2) / float(self.FS)
            self.frames.append( TDTaFrame(monoAudio[ i*self.sampleShift : i*self.sampleShift+self.windowSize ], self.window, self.voicedLogEnergy, tCntr) )
    
    def GetVoicedEnergy(self, monoAudio):
        allEnergies = []
        halfWindow = self.windowSize // 2
        for i in range((monoAudio.shape[0]-self.windowSize-10) // halfWindow):
            wndw = monoAudio[ i*halfWindow : i*halfWindow+self.windowSize ]
            allEnergies.append(numpy.sum(numpy.square(wndw)))
        for i,e in enumerate(allEnergies):
            if e == 0.0:
                allEnergies[i] = 0.000000001
            
        allEnergies = numpy.log(allEnergies)
        
        srtd = sorted(allEnergies)
        if len(srtd) < 5:
            self.voicedLogEnergy = 0.5*numpy.mean(srtd)
        else:
            unv = max(1, len(srtd) // 10)
            vcd = len(srtd) - max(2, len(srtd) // 5)
            
            low, high = numpy.mean(srtd[:unv]), numpy.mean(srtd[vcd:])
            
            self.voicedLogEnergy = 0.5*(low+high)
        
    def RunAC(self):
        for frm in self.frames:
            frm.ComputeAC()
            frm.FindPeaks(self.accIndFromBoost, self.accIndTo, self.FS)
            frm.ReducePeaks(self.minF0, self.maxF0)
    
    def RunBackTrack(self):
        voicedCount, firstVoiced, lastVoiced = self.CountVoicedFrames()
        
        if voicedCount < 10:
            raise Exception ('F0Xtractor.RunBackTrack: too few voiced frames')
        
        self.ExtendBroderPeaks(firstVoiced, lastVoiced)

        self.MakeForwardPass(firstVoiced)

        self.MakeBackTrack(lastVoiced)

    def CountVoicedFrames(self):
        voicedCount, firstVoiced, lastVoiced = 0,None,0
        
        for i,frm in enumerate(self.frames):
            if frm.IsVoiced:
                voicedCount += 1
                if firstVoiced == None:
                    firstVoiced = i
                lastVoiced = i
        return voicedCount, firstVoiced, lastVoiced
     
    def ExtendBroderPeaks(self, firstVoiced, lastVoiced):
        # find first and last 3 voiced frames and add them to last and first voiced frame 
        # (make sure propper hypothesis has start and end)
        # better do it for first / last few frames (like 10)

        firstPeaks, added = [], 0
        for i in range(firstVoiced+1, firstVoiced+10):
            frm = self.frames[i]
            if frm.IsVoiced:
                firstPeaks += frm.peaks
                added += 1
            if added >= 2:
                break
        self.frames[firstVoiced].addFramePeaks(firstPeaks)
        
        lastPeaks, added = [], 0
        for i in range(lastVoiced-1, lastVoiced-10, -1):
            frm = self.frames[i]
            if frm.IsVoiced:
                lastPeaks += frm.peaks
                added += 1
            if added >= 2:
                break
        self.frames[lastVoiced].addFramePeaks(lastPeaks)            
        
    def MakeForwardPass(self, firstVoiced):
        for peak in self.frames[firstVoiced].peaks:
            peak.score = peak.strength

        # forward pass... put previousVoicedFrame to frame (for backTracking)
        previous = firstVoiced
        for i in range(previous+1, len(self.frames)):
            if self.frames[i].IsVoiced and len(self.frames[i].peaks) > 0:
                # xPeak ... aktuální; sPeak je "odkud skáču"
                for xPeak in self.frames[i].peaks:
                    best_src, best_score = 0,-10000.0
                    
                    for src,sPeak in enumerate(self.frames[previous].peaks):
                        factor, octave = self.GetTransitionPenalty(sPeak.frequency, xPeak.frequency)
                        score = sPeak.score + factor*xPeak.strength - octave
                        if score > best_score:
                            best_src, best_score = src, score
                    
                    xPeak.score = best_score
                    xPeak.reachedFrom_frame = previous
                    xPeak.reachedFrom_peak = best_src
                
                previous = i
           
    def GetTransitionPenalty(self, f1, f2):
        high, low = max(f1, f2), min(f1, f2)
        
        if high == 0.0 or low == 0.0:
            return 0.1, self.octaveCost
        
        else:
            ratio = low/high
    
            if ratio < 0.55:
                return 0.7, self.octaveCost                    
            elif ratio < 0.85:
                return 0.85, self.octaveCost
            else:
                return 1.0, 0.0
            
    def MakeBackTrack(self, lastVoiced):
        self.F0Path = numpy.zeros(len(self.frames))
        
        # get best end peak
        bestEnd, bestScore = 0, -10000.0
        for i,P in enumerate(self.frames[lastVoiced].peaks):
            if P.score > bestScore:
                bestEnd, bestScore = i, P.score
        
        self.PathScore = bestScore
        self.F0Path[lastVoiced] = self.frames[lastVoiced].peaks[bestEnd].frequency

        previousFrame = self.frames[lastVoiced].peaks[bestEnd].reachedFrom_frame
        previousPeak = self.frames[lastVoiced].peaks[bestEnd].reachedFrom_peak
        
        NextPeak = self.frames[previousFrame].peaks[previousPeak]           
        while NextPeak.reachedFrom_frame != None:
            self.F0Path[previousFrame] = NextPeak.frequency
            
            previousFrame = NextPeak.reachedFrom_frame
            previousPeak = NextPeak.reachedFrom_peak
            try:
                NextPeak = self.frames[previousFrame].peaks[previousPeak]
            except:
                break
            
            
        
        self.F0Path[previousFrame] = NextPeak.frequency

    def GetF0Stats(self):
        voicedF0 = []
        for f in self.F0Path:
            if f > 0.0:
                voicedF0.append(f)
                
        F0_mean = 0.0
        F0_min = 0.0
        F0_max = 0.0
        F0_std = 0.0
        F0_q10 = 0.0
        F0_q90 = 0.0
        
        if len(voicedF0) < 5:
            self.logger.error('F0Xtractor: No F0Path found, cannot export stats!')
        else:
            F0_mean = numpy.mean(voicedF0)
            F0_min = numpy.min(voicedF0)
            F0_max = numpy.max(voicedF0)
            F0_std = numpy.std(voicedF0)
            F0_q10 = numpy.percentile(voicedF0, 10)
            F0_q90 = numpy.percentile(voicedF0, 90)
            
            
        rslt = {
            'mean': F0_mean,
            'min': F0_min,
            'max': F0_max,
            'std': F0_std,
            'q10': F0_q10,
            'q90': F0_q90
            }
            
        return rslt    
        
    def ComputeF0Path(self, monoAudio:numpy.array):
        self.MakeFrames(monoAudio)
        self.RunAC()        
        self.RunBackTrack()

#===============================================================================
#     def CheckOctave(self):
#         HighPath = self.F0Path
#         HighEnergy = self.PathScore
#         
#         MatchedPeakCount = 0
#         voicedCount = 0
#         
#         LowTractor = F0Xtractor(self.logger, self.
#                                 timeShift=0.0, minPeriodCount=3.0)
#         fakeAudio, fakeWindow = numpy.zeros(1), numpy.zeros(1)
#         for i,F in enumerate(self.frames):
#             fLow = TDTaFrame(fakeAudio, fakeWindow, self.voicedLogEnergy)
#             fLow.IsVoiced = F.IsVoiced
#             
#             highFreq = self.F0Path[i] 
#             
#             peakMatched = False
#             ceiling = 0.8 * self.F0Path[i]
#             for peak in F.peaks:
#                 if peak.frequency < ceiling:
#                     fLow.peaks.append(peak)
#                 
#                 if 0.45*highFreq < peak.frequency < 0.55 *highFreq:
#                     peakMatched = True
#             
#             if not peakMatched:
#                 fLow.peaks.append(ACPeak(0.5*highFreq, 0.01))
#             else:
#                 MatchedPeakCount += 1
#                 
#             if F.IsVoiced:
#                 voicedCount += 1
#             
#             LowTractor.frames.append(fLow)      
#             
#         LowTractor.firstVoiced = self.firstVoiced
#         LowTractor.lastVoiced = self.lastVoiced
#         LowTractor.RunBackTrack()
# 
#         #=======================================================================
#         # pathLow = LowTractor.F0Path
#         # 
#         # print('matchedPeaks: ',MatchedPeakCount,'of',voicedCount,str(100.0*float(MatchedPeakCount)/float(voicedCount))[:5])
#         # print('High score:',HighEnergy)
#         # print('Low score: ',LowTractor.PathScore)
#         #=======================================================================
#         
#         matchRatio = str(100.0*float(MatchedPeakCount)/float(voicedCount))[:5]
#         scoreRatio = str(100.0*LowTractor.PathScore/HighEnergy)
#         
#         return matchRatio.replace('.',','), scoreRatio.replace('.',',')
#===============================================================================