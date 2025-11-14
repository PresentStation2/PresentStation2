import numpy
import scipy.signal


class SoundFiltering():
    def __init__(self):
        self.filter = [1]
        self.nCoeff = 1
    
    def design_FIR_BandPass(self, fPass, fStop, FS, nCoeff):
        self.nCoeff = nCoeff
        f1, f2 = float(fPass)/float(FS), float(fStop)/float(FS)
        a = scipy.signal.firwin(nCoeff, [f1, f2], pass_zero=False)
        self.filter = scipy.signal.firwin(nCoeff, [f1, f2], pass_zero=False) 
        
    def applyFilter(self, soundIn):
        # apply filter        
        filtered = scipy.signal.convolve(soundIn, self.filter, mode='full', method='auto')
        # compensate filter delay
        
        if self.nCoeff // 2 > 0:
            filtered = numpy.delete(filtered, range(self.nCoeff // 2))
        
        return filtered[:soundIn.shape[0]] 
        
