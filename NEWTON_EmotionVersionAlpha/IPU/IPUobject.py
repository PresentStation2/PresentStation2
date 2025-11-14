import numpy


class IPUobject():
    def __init__(self, start, end, cfg):
        self.start = start
        self.end = end
        
        self.frameSize = cfg.IPU_frameSize
        self.frameShift = cfg.IPU_frameShift
        self.window = numpy.hanning(self.frameSize)
        self.FS = float(cfg.ffmpeg_FS)
        self.validNBins = int(cfg.Formant_maxFmtFreq / (self.FS / self.frameSize)) + 10
        self.df = float(self.FS) / float(self.frameSize)
        
        self.F0s = []
        self.formants = []
        self.preparedPeaks = []

        #=======================================================================
        # consisten with Oli's naming convention:
        # f0 is fundamental frequency, H1 is its amplitude
        # F1 is first formant, A1 is its amplitude
        #=======================================================================

        self.f0 = 0.0
        self.f1 = 0.0
        self.H1 = 0.0
        self.H2 = 0.0
        
        self.F1 = 0.0
        self.F2 = 0.0
        self.F3 = 0.0
        self.A1 = 0.0
        self.A2 = 0.0
        self.A3 = 0.0
        
        self.f0Known = False
        self.fmntKnown = False
         
        
    def getF0data(self, F0Xtractor, strt):
        self.f0s = []
        for ifrm in range(strt, len(F0Xtractor.frames)):
            output = ifrm
            if self.start < F0Xtractor.frames[ifrm].TimeCenter < self.end:
                self.f0s.append(F0Xtractor.F0Path[ifrm])
            elif F0Xtractor.frames[ifrm].TimeCenter >= self.end:
                break
        
        if len(self.f0s) > 0:
            self.f0 = numpy.mean(self.f0s)
            self.f0Known = True
        
        return output
    
    def getFormant(self, FormantXtractor, strt):
        self.formants = []
        perFrame = FormantXtractor.FormantsPerFrame
        
        for ifrm in range(strt, len(perFrame)):
            output = ifrm
            if self.start < perFrame[ifrm].timeCenter < self.end:
                self.formants.append(perFrame[ifrm].formants)
            elif perFrame[ifrm].timeCenter >= self.end:
                break
        
        set1, set2, set3 = [], [], []
        for F in self.formants:
            if len(F) > 2:
                set1.append(F[0].frequency)
                set2.append(F[1].frequency)
                set3.append(F[2].frequency)
        
        if len(set1) > 0:
            self.fmntKnown = True
                 
            self.F1 = numpy.mean(set1)
            self.F2 = numpy.mean(set2)
            self.F3 = numpy.mean(set3)
        
        return output        
        
    def IsRelevant(self):
        return self.f0Known and self.fmntKnown
        
    def ProcessSpectrum(self, audio):
        self.maxIndex = audio.shape[0]-1
        spectra = []
        if not self.IsRelevant():
            pass

        for indBg, indNd in self.FindDataFrames(self.start, self.end):
            try:
                spectra.append(self.getSpectrum(audio, indBg, indNd))
            except:
                pass
        
        if len(spectra) == 0:
            self.fmntKnown = False
            return
        elif len(spectra) == 1:
            self.spectrum = spectra[0]
        else:
            self.spectrum = numpy.mean(numpy.array(spectra),0)

        self.PSD = self.getPSD(self.spectrum)
        self.preparePeaks()
        
        self.evaluateF0()
        self.evaluateFormant()
        
        
    def evaluateFormant(self):
        try:
            self.A1 = self.FindCloseFormant(self.F1)
            self.A2 = self.FindCloseFormant(self.F2)
            self.A3 = self.FindCloseFormant(self.F3)
        except:
            self.fmntKnown = False
        
    def evaluateF0(self):
        try:
            f0Index = self.getCloseIndex(self.f0)
            F0, self.H1 = self.getPeakAround(f0Index)
            F1, self.H2 = self.getPeakAround(2*F0)
            self.f1 = self.df*F1
        except:
            self.f0Known = False
        
    def FindCloseFormant(self, f):
        i = self.getCloseIndex(f)
        j,val = self.preparedPeaks[0]
        dist, winner, mx = abs(j-i), j, val 
        
        for j,val in self.preparedPeaks:
            if (abs(j-i) < dist) or (abs(j-i) == dist and val > mx):
                dist, winner, mx = abs(j-i), j, val
            elif abs(j-i) > dist:
                break
        del(winner)
        
        return mx

    def FindDataFrames(self, timeFrom, timeTo):
        frames = []
        indStart, indEnd = int(self.FS*timeFrom), int(self.FS*timeTo)
        
        if not( 0 <= indStart <= self.maxIndex ):
            self.logger.error('IPU/FindDataFrames: Invalid startTime: '+str(timeFrom))
            indStart = None

        if not( 0 <= indEnd <= self.maxIndex ):
            self.logger.error('IPU/FindDataFrames: Invalid endTime: '+str(timeTo))
            indEnd = None            

        if indStart == None or indEnd == None:
            raise Exception('IPU: Invalid interval: '+str(timeFrom)+' : '+str(timeTo)+
                    ' for recording of duration: '+str(float(self.maxIndex)/float(self.FS)))
        
        for i in range((indEnd-indStart-self.frameSize)//self.frameShift +1):
            b = indStart + i * self.frameShift
            e = b + self.frameSize
            frames.append((b,e))
        
        if len(frames) == 0:
            frames.append((indStart,indStart+self.frameSize))
        
        return frames

    def getSpectrum(self, audio, indBg, indNd):
        rect = audio[ indBg : indNd ]
        S = numpy.abs(numpy.fft.rfft( numpy.multiply(rect, self.window) ))
                
        filtr = numpy.hamming(13)
        filtr = filtr/sum(filtr)

        x = numpy.convolve(S[:self.validNBins],filtr)
        
        return(x[6:-6])

    def getPSD(self, dta):
        psd = 2.0 * numpy.multiply(dta, dta) / self.FS
        Pref = 0.00002
        PSD = 10.0 * numpy.log10(psd / (Pref*Pref))
        
        return PSD
    
    def preparePeaks(self):
        for i in range(3,self.validNBins-3):
            x = self.spectrum[i]
            if x == max(self.spectrum[i-2:i+3]):
                self.preparedPeaks.append((i,x))

    def getCloseIndex(self, f):
        i = int(f / self.df)
        
        if i < 10:
            return 10
        elif i > self.validNBins - 10:
            return self.validNBins - 10
        else:
            return i
        
    def getPeakAround(self,index):
        # find closest peak, if 2 in same dist, take higher one
        peaks = []
        for c in range(index-5,index+6):
            if self.spectrum[c] == max(self.spectrum[c-2:c+3]):
                peaks.append((c,self.spectrum[c]))
        
        if len(peaks) == 0:
            # must find a maximum of close range
            winner, val = c, self.spectrum[c]
            for c in range(index-3,index+4):
                if self.spectrum[c] > val:
                    winner, val = c, self.spectrum[c]
                return(winner, self.PSD[winner])
        elif len(peaks) == 1:
            return(peaks[0][0], self.PSD[peaks[0][0]])
        else:
            minPeakDistance = abs(index-peaks[0][0])
            for peak in peaks:
                if abs(index-peak[0]) < minPeakDistance:
                    minPeakDistance = abs(index-peak[0]) 
            
            closePeaks = []
            for peak in peaks:
                if abs(index-peak[0]) == minPeakDistance:
                    closePeaks.append(peak)
            
            if len(closePeaks) == 1:
                return(closePeaks[0][0], self.PSD[closePeaks[0][0]])
            else:
                chosen = closePeaks[0]
                for cpk in closePeaks:
                    if cpk[1] > chosen[1]:
                        chosen = cpk
                
                return(chosen[0][0], self.PSD[chosen[0][0]])
            
