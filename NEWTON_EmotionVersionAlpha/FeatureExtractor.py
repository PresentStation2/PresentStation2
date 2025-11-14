from sharedComponents.Utils import InitConfig, GetAudio

from F0.F0Extractor import F0Xtractor
from Intenzita.Intenzita import SoundIntensity
from Intenzita.SoundFiltering import SoundFiltering
from Formanty.FormantExtractor import FormantXtractor
from IPU.IPUs import IPUs

from sharedComponents.Gender import Gender

from FeatureHolder.Features import Features
import re
import pickle
import numpy
import scipy.signal

#===============================================================================
# import pickle
# import re
#===============================================================================
import os
import codecs
import sys
import traceback


class FeatureExtractor():
    def __init__(self, logger, config):
        self.config = config
        self.logger = logger
        
        self.Features = Features(logger)
        
        self.F0_f1 = 0.0
        self.F0_f2 = 0.0
        self.F0_H1 = 0.0 
        self.F0_H2 = 0.0
        
        self.Frmnt_f1 = 0.0
        self.Frmnt_f2 = 0.0
        self.Frmnt_f3 = 0.0
        self.Frmnt_A1 = 0.0
        self.Frmnt_A2 = 0.0
        self.Frmnt_A3 = 0.0


    def preprocessAudio(self, audioIn):
        #===================================================
        # base pre-processing is BandPass Filter 80-8000 Hz
        # filter for fixed FS is stored in ConfigHolder
        #===================================================
        
        # apply filter
        nCoeff = len(self.config.FeatExt_filter)
        filtered = scipy.signal.convolve(audioIn, self.config.FeatExt_filter, mode='full', method='auto')

        # compensate filter delay        
        if nCoeff // 2 > 0:
            filtered = numpy.delete(filtered, range(nCoeff // 2))
        
        self.Features.Duration = float(filtered.shape[0]) / float(self.config.ffmpeg_FS)

        return filtered[:audioIn.shape[0]] 
        
        
    def getClosestF0Point(self, timeSec):        
        position = timeSec * self.config.ffmpeg_FS
        return int(numpy.around( float(position - self.F0XTract.windowSize // 2) / float(self.F0XTract.sampleShift) ))
        
        
    def ExtractFeatures(self, rawMonoAudio, tellStatus = False):
        #========================================
        # start sub-extractors ... resets for job
        #========================================        
        self.startComponents()
        
        #========================================
        # BandPass Filtering (speech relevant)
        #========================================        
        filteredMono = self.preprocessAudio(rawMonoAudio)
        
        #========================================
        # extract F0 trajectory
        #========================================
        if tellStatus:
            print('  .. getting F0')
        self.F0XTract.ComputeF0Path(filteredMono)
        self.Features.TakeF0Stats(self.F0XTract)

        #========================================
        # extract energy and speechRate
        #========================================
        if tellStatus:
            print('  .. getting Energy')        
        self.Intensity.GetIntensity_dB(filteredMono, self.config.ffmpeg_FS)
        silThreshold = self.Intensity.RemoveSilence(self.config)
        self.Intensity.FindPeaks(self.config.Intens_minDip_dB, silThreshold)
        self.removeEPeaksByF0()
        self.Intensity.findIPUs()
        
        self.Features.TakeIntensity(self.Intensity)
        
        #========================================
        # extract formant information
        #========================================
        if tellStatus:
            print('  .. getting Formants')
        self.Formants.ComputeFormants(filteredMono, audioFS=self.config.ffmpeg_FS)
        
        #========================================
        # extract formant information
        # VoiceColor(quality) per IPU
        #========================================
        if tellStatus:
            print('  .. getting IPU features')
        self.IPUs.GetTimeIntervals(self.Intensity)
        self.IPUs.GetF0(self.F0XTract)
        self.IPUs.GetFormants(self.Formants)
        self.IPUs.GetSpectra(filteredMono)
        
        self.Features.TakeVoiceColor(self.IPUs)


    def removeEPeaksByF0(self):
        mx2remove = []
        for i,maxIndex in enumerate(self.Intensity.maxima):
            j = self.getClosestF0Point(self.Intensity.timeCenters[maxIndex])
            if j < len(self.F0XTract.F0Path):
                if self.F0XTract.F0Path[j] < 1.0:
                    mx2remove.append(i)
            else:
                mx2remove.append(i)

        mx2remove.reverse()
        for x in mx2remove:
            del(self.Intensity.maxima[x])


    def startComponents(self):
        # also ensures component reset if extractor is re-used
        self.F0XTract = F0Xtractor(self.logger, self.config)
        self.Intensity = SoundIntensity(self.config.Intens_minPitch)
        self.Formants = FormantXtractor(self.logger, self.config)
        self.IPUs = IPUs(self.logger, self.config)
        
        self.Features = Features(self.logger)
    
    
    def TakeChosenFeatures(self):
        keyOrder = [ 'minF0', 'maxF0', 'meanF0', 'F0range', 'F0std', 'F0q10', 'F0q90', 'meanF1',
            'meanF2', 'meanF3', 'meanF2+3', 'H1-H2', 'H1-H2std', 'H1-A1', 'H1-A1std', 'H1-A2', 'H1-A2std', 
            'H1-A3', 'H1-A3std', 'pauseCount', 'meanPauseDuration', 'meanSpeakingRate', 'RMSmean', 'RMSstd']
        features = {
            'minF0': self.Features.F0.Min,
            'maxF0': self.Features.F0.Max,
            'meanF0': self.Features.F0.Mean,
            'F0range': self.Features.F0.SemitoneRange,
            'F0std': self.Features.F0.Std,
            'F0q10': self.Features.F0.Q10,
            'F0q90': self.Features.F0.Q90,
            'meanF1': self.Features.VoiceColor.F1,
            'meanF2': self.Features.VoiceColor.F2,
            'meanF3': self.Features.VoiceColor.F3,
            'meanF2+3': self.Features.VoiceColor.F2plusF3,
            'H1-H2': self.Features.VoiceColor.H1minusH2,
            'H1-H2std': self.Features.VoiceColor.H1minusH2_std,
            'H1-A1': self.Features.VoiceColor.H1minusA1,
            'H1-A1std': self.Features.VoiceColor.H1minusA1_std,
            'H1-A2': self.Features.VoiceColor.H1minusA2,
            'H1-A2std': self.Features.VoiceColor.H1minusA2_std,
            'H1-A3': self.Features.VoiceColor.H1minusA3,
            'H1-A3std': self.Features.VoiceColor.H1minusA3_std,
            'pauseCount': self.Features.Intensity.NPause,
            'meanPauseDuration': self.Features.Intensity.MeanPauseDuration,
            'meanSpeakingRate': self.Features.getArticulationRate(),
            'RMSmean': self.Features.Intensity.RMSMean,
            'RMSstd': self.Features.Intensity.RMSStd
            }
        
        return keyOrder, features


def ProcessDirectory(srcPath, pattern, trgPath):
    data = {}
    MyConfigHolder, logger = InitConfig('FE_Setup.json', 'log2.log') 
    FE = FeatureExtractor(logger, MyConfigHolder)
    print('path: ',srcPath)
            
    for fName in os.listdir(srcPath):
        if re.match(pattern, fName):
            print('  processing:', fName)

            try:
                rawMono = GetAudio(os.path.join(srcPath, fName), MyConfigHolder, logger)
                FE.ExtractFeatures(rawMono, tellStatus=False)
                keys, dta = FE.TakeChosenFeatures()
                nomen = os.path.splitext(fName)[0]
                data[nomen] = dta
            except:
                print('  !!! failed')
    pickle.dump(data, open(os.path.join(trgPath, os.path.split(srcPath)[-1])+'.pkl','wb'))
    out = ['fileName'+'\t'+'\t'.join(keys)]
    for N in data.keys():
        featureVector = featuresToArray(data[N], keys)
        out.append(N+'\t'+'\t'.join(featureVector))

    f = codecs.open(os.path.join(trgPath, os.path.split(srcPath)[-1]+'.txt'), 'w', 'utf-8')
    f.write('\r\n'.join(out))
    f.flush()
    f.close()
    
    
def featuresToArray(dta,ks):
    out = []
    for k in ks:
        out.append(str(dta[k]))
    return out
    
    
def ProcessSingleFile(fIn, logName, setupJson):
    MyConfigHolder, logger = InitConfig(setupJson, logName)
    try:    
        FE = FeatureExtractor(logger, MyConfigHolder)
        rawMono = GetAudio(fIn, MyConfigHolder, logger)
        FE.ExtractFeatures(rawMono, tellStatus=False)
        keys, dta = FE.TakeChosenFeatures()
        
        out = ['features:'+'\t'+'\t'.join(keys)]    
        featureVector = featuresToArray(dta, keys)
        out.append('values:'+'\t'+'\t'.join(featureVector))

        f = codecs.open(fIn+'.txt', 'w', 'utf-8')
        f.write('\r\n'.join(out))
        f.flush()
        f.close()
    except:
        logger.error(str(traceback.format_exc(limit=None, chain=True)))


def findAudioRecordings(path, exts):
    items = os.scandir(path)
    out = []
    for item in items:
        if item.is_file and os.path.splitext(item.name)[-1] in exts:
            out.append(item.path)
    return out
    
    
def processRecordingList(items, logName, setupJson):
    data = {}
    MyConfigHolder, logger = InitConfig(setupJson,logName) 
    FE = FeatureExtractor(logger, MyConfigHolder)

    for i,item in enumerate(items):
        print('  processing item ',i+1,'/',len(items),' :',item)
        try:
            rawMono = GetAudio(os.path.join(item), MyConfigHolder, logger)
            FE.ExtractFeatures(rawMono, tellStatus=False)
            keys, dta = FE.TakeChosenFeatures()
            nomen = os.path.splitext(os.path.split(item)[-1])[0]
            data[nomen] = dta
        except:
            logger.error(str(traceback.format_exc(limit=None, chain=True)))
            print('    !!! failed (check log please)')
        
        try:
            out = ['fileName'+'\t'+'\t'.join(keys)]
            for N in data.keys():
                featureVector = featuresToArray(data[N], keys)
                out.append(N+'\t'+'\t'.join(featureVector))

            wDir = os.path.split(items[0])[0]
            wDirName = os.path.split(wDir)[-1]
            f = codecs.open(os.path.join(wDir, wDirName+'.txt'), 'w', 'utf-8')
            f.write('\r\n'.join(out))
            f.flush()
            f.close()        
                
        except:
            err = str(traceback.format_exc(limit=None, chain=True))
            logger.error(err)
            print('    !!! failed to dump results')
            print(err)

    
def ProcessGivenPath(dataPath):
    if not os.path.exists(dataPath):
        print('Invalid input path: "',dataPath+'"')
    else:
        validExtensions = ['.mp3', '.wav']
        setupJson = 'FE_Setup.json'
        
        try:
        
            if os.path.isfile(dataPath):
                ex = os.path.splitext(dataPath)[-1]
                if not ex in validExtensions:
                    print('File extension not supported "'+ex+'"')
                else:
                    print('  ... processing: ', dataPath)
                    logName = os.path.join(os.path.split(dataPath)[0], 'featureExtractor.log')
                    ProcessSingleFile(dataPath, logName, setupJson)           
                    print('  ... done')
            else:
                print('Scanning directory: "'+dataPath+'"')
                items = findAudioRecordings(dataPath, validExtensions)
                print('  ',len(items),'files with .wav or .mp3 extensions will be processed:')
                processRecordingList(items, os.path.join(dataPath,'featureExtractor.log'), setupJson)
                print('  ... done')
        
        except:
            print( str(traceback.format_exc(limit=None, chain=True)) )
            

if __name__ == '__main__':
    trgPath = ""
    
    src = "C:\\NEWTON_EmotionVersionAlpha\\_src"
    ProcessGivenPath(src)
    
    # *sys.argv[1:]
    # ProcessSingleFile(src, 'filename.wav', trgPath)
