import numpy
from numpy import exp

from scipy.signal import resample
from scipy.fft import next_fast_len

from Formanty.FormantObject import FrameFromants
from Formanty.Burg.Burg import Burg



class FormantXtractor():
    def __init__(self, logger, config):
        timeStep = config.Formant_timeStep 
        maximumNumberOfFormants = config.Formant_maxNofFmts
        maximumFormantFrequency = config. Formant_maxFmtFreq
        windowLength = config.Formant_winLength
        preemphasisFrequency = config.Formant_preemFreq
        safetyMargin = config.Formant_freqMargin
        #=======================================================================
        # timeStep ... float [sec.] window hop
        # maximumNumberOfFormants 0.5...1 formant 2.5...5 formants (halfOfFormant number)
        # maximumFormantFrequency [Hz] max formant freq.
        # windowLength ... duration of analysis window?
        # safetyMargin ... LowStop freq
        #=======================================================================
        
        self.logger = logger
        
        self.dt = timeStep
        self.dx = 1.0 
        self.numberOfPoles = int(numpy.round(2.0*maximumNumberOfFormants))
        self.maximumFrequency = maximumFormantFrequency
        self.halfdt_window = windowLength
        self.preemphasisFrequency = preemphasisFrequency
        self.safetyMargin = safetyMargin        
        
        self.FormantsPerFrame = []
            
    def ComputeFormants(self, monoAudio:numpy.array, audioFS:int):        
        nyquist = 0.5 * float(audioFS)
        self.dx = 1.0 / float(audioFS)

        if self.maximumFrequency <= 0.0 or abs(self.maximumFrequency / nyquist - 1.0) < 0.00001:
            # no resampling
            self.resampledSound = monoAudio;
            resampledFS = audioFS
        else:
            # resampling (should be default)
            self.resampledSound = self.Resample(monoAudio, audioFS, self.maximumFrequency * 2.0)
            resampledFS = self.maximumFrequency * 2.0    
        
        dt_window = 2.0 * self.halfdt_window;
        nsamp_window = int(dt_window / self.dx)

        if nsamp_window < self.numberOfPoles + 1:
            raise Exception("FormantXtractor: Window too short.")
        
        self.RunPreEmphasis(resampledFS)
        HAM = self.GetGaussianWindow(nsamp_window)
        
        BURG = Burg(nyquistFrequency=self.maximumFrequency, safetyMargin=self.safetyMargin)
    
        nFrames = int( ((self.resampledSound.shape[0] / resampledFS) - dt_window) / self.dt )  
        actualFrameCenterPosition = 0.5 * self.halfdt_window
        
        for iframe in range(nFrames):
            
            iStart = int(iframe * self.dt * resampledFS)
            iEnd = iStart + nsamp_window
        
            audio = self.resampledSound[iStart:iEnd]
            if audio.shape[0] < nsamp_window:
                audio = numpy.pad(audio,(0,nsamp_window-audio.shape[0]), 'constant') 
            windowed = numpy.multiply(audio, HAM)
            
            isNonZero = False
            for i in range(windowed.shape[0]):
                if numpy.abs(windowed[i]) > 0.001:
                    isNonZero = True
                    break
            
            
            formants = []
            if isNonZero:
                formants = BURG.computeBurg(windowed, self.numberOfPoles)
             
             
            self.FormantsPerFrame.append(FrameFromants(timeCenter=actualFrameCenterPosition, formants=formants))
             
            actualFrameCenterPosition += self.dt

    def RunPreEmphasis(self, resampledFS):
        # y[n] = x[n] - α*x[n-1]
        alpha = numpy.exp(-2.0 * numpy.pi * self.preemphasisFrequency / float(resampledFS))
        
        lenRSS = self.resampledSound.shape[0]
        for i in range(lenRSS-1, 0, -1):
            self.resampledSound[i] -= alpha * self.resampledSound[i-1]    
        
    def GetGaussianWindow(self, nSamp):
        wndw = numpy.zeros(nSamp)
        
        imid, edge = 0.5 * (nSamp + 1), exp(-12.0)
        nsmpSqr = (nSamp + 1) * (nSamp + 1)
                
        for i in range(nSamp):
            wndw[i] = (exp(-48.0 * (i+1 - imid) * (i+1 - imid) / nsmpSqr) - edge) / (1.0 - edge)
        
        return wndw        
    
    
    def Resample(self, audio, audioFS, targetFS):
        # zero-padding should keep it fast ... then end is forgotten
        duration = float(audio.shape[0]) / float(audioFS)
        trgtSampleCount = int(numpy.floor(duration * float(targetFS)))
        
        actLen = audio.shape[0]
        nxt = next_fast_len(actLen)
        
        inpt = audio
        if nxt != actLen:            
            inpt = numpy.pad(audio, [(0,nxt-actLen)], mode='constant')
    
        resampled = resample(inpt, trgtSampleCount)
        
        resLen = resampled.shape[0] 
        if resLen < trgtSampleCount:
            trgtSampleCount = resLen
        
        return resampled[:trgtSampleCount]
