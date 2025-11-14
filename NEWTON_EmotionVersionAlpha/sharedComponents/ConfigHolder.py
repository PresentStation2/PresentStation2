'''
Object holding complete configuration for ChannelMerger and all its components

05. 10. 2020 - separated into single file ... basic version (v 0.1.0)
06. 10. 2020 - adder serverconfiguration to ConfigHolder
'''

import os
import json
import traceback
from pathlib import Path


class ConfigHolder():
    def __init__(self, logger):
        self.ready = False
        self.version = '0.1.0'
        self.logger = logger
        
    def loadConfiguration(self,jsonFile):
        jsonFile = os.path.normpath(jsonFile)
        if os.path.exists(jsonFile):
            try:
                with open(jsonFile) as f:
                    dta = json.load(f)
                self.update_config_values(dta)
            except:
                err = str(traceback.format_exc(limit=None, chain=True))
                self.logger.error("configHolder: loading failed: "+str(jsonFile))
                self.logger.error(err)
        else:
            self.logger.error("configHolder: given json config-file doesn't exist: "+str(jsonFile))

        self.log_config()
        self.verify_config()
    def update_config_values(self,dta):
        # ffmpeg related settings:
        self.ffmpeg_ffPath = ''
        self.ffmpeg_FS = 16000
        self.ffmpeg_tdtaChunk = 1600
        self.ffmpeg_bigChunk = 32768

        if 'ffmpegSetup' in dta:
            ffConfig = dta['ffmpegSetup']
            if 'ffmpegPath' in ffConfig and isinstance(ffConfig['ffmpegPath'],str):
                self.ffmpeg_ffPath = os.path.normpath(ffConfig['ffmpegPath'])
                if self.ffmpeg_ffPath == '.':
                    self.ffmpeg_ffPath = ''
            else:
                self.logger.error('invalid value of ffmpegPath: '+str(ffConfig['ffmpegPath']))

            if 'workingFS' in ffConfig and isinstance(ffConfig['workingFS'],int):
                self.ffmpeg_FS = ffConfig['workingFS']
            else:
                self.logger.error('invalid value of workingFS: '+str(ffConfig['workingFS']))


            if 'tdta_chunk' in ffConfig and isinstance(ffConfig['tdta_chunk'],int):
                self.ffmpeg_tdtaChunk = ffConfig['tdta_chunk']
            else:
                self.logger.error('invalid value of tdta_chunk: '+str(ffConfig['tdta_chunk']))

            if 'chunk_size' in ffConfig and isinstance(ffConfig['chunk_size'],int):
                self.ffmpeg_bigChunk = ffConfig['chunk_size']
            else:
                self.logger('invalid value of chunk_size: '+str(ffConfig['chunk_size']))

        else:
            self.logger.error('"ffmpegSetup" configuration part not in loaded setup json!')

            
        self.F0_minF0 = 75.0
        self.F0_maxF0 = 400.0
        self.F0_timeStep = 0.01

        if 'F0Setup' in dta:
            try:
                self.F0_minF0 = dta['F0Setup']['minF0']
                self.F0_maxF0 = dta['F0Setup']['maxF0']
                self.F0_timeStep = dta['F0Setup']['timeShift']
            except:
                self.logger.error(str(traceback.format_exc(limit=None, chain=True)))
        else:
            self.logger.error('"F0Setup" configuration part not in loaded setup json!')

        self.FeatExt_filter = [1.0]
        if 'featureExtractor' in dta:
            try:
                self.FeatExt_filter = dta['featureExtractor']['filterCoeffs']
            except:
                self.logger.error(str(traceback.format_exc(limit=None, chain=True)))
        else:
            self.logger.error('"featureExtractor" configuration part not in loaded setup json!')


        self.Intens_minPitch = 80.0
        self.Intens_minSilentDuration = 0.3
        self.Intens_minVoicedDuration = 0.1
        self.Intens_minDip_dB = 2.0
        self.Intens_VoiceSildB = 25.0
        if 'IntensitySetup' in dta:
            try:
                self.Intens_minPitch = dta['IntensitySetup']['minPitch']
                self.Intens_minSilentDuration = dta['IntensitySetup']['minSilentDuration']
                self.Intens_minVoicedDuration = dta['IntensitySetup']['minVoicedDuration']
                self.Intens_minDip_dB = dta['IntensitySetup']['minDip_dB']
                self.Intens_VoiceSildB = dta['IntensitySetup']['VoiceSildB']
            except:
                self.logger.error(str(traceback.format_exc(limit=None, chain=True)))
        else:
            self.logger.error('"IntensitySetup" configuration part not in loaded setup json!')

        
        self.IPU_frameSize = 5600
        self.IPU_frameShift = 2800
        self.IPU_filter = [0.1, 0.2, 0.4, 0.2, 0.1]
        if 'IPUSetup' in dta:
            try:
                self.IPU_frameSize = dta['IPUSetup']['frameSize']
                self.IPU_frameShift = dta['IPUSetup']['frameShift']
                self.IPU_filter = dta['IPUSetup']['filter']
            except:
                self.logger.error(str(traceback.format_exc(limit=None, chain=True)))
        else:
            self.logger.error('"IPUSetup" configuration part not in loaded setup json!')


        self.Formant_timeStep = 0.00625
        self.Formant_maxNofFmts = 6.0
        self.Formant_maxFmtFreq = 5500
        self.Formant_winLength = 0.025
        self.Formant_preemFreq = 50.0
        self.Formant_freqMargin = 50.0
        if 'FormantSetup' in dta:
            try:
                self.Formant_timeStep = dta['FormantSetup']['timeStep']
                self.Formant_maxNofFmts = dta['FormantSetup']['maximumNumberOfFormants']
                self.Formant_maxFmtFreq = dta['FormantSetup']['maximumFormantFrequency']
                self.Formant_winLength = dta['FormantSetup']['windowLength']
                self.Formant_preemFreq = dta['FormantSetup']['preemphasisFrequency']
                self.Formant_freqMargin = dta['FormantSetup']['safetyMargin']
            except:
                self.logger.error(str(traceback.format_exc(limit=None, chain=True)))
        else:
            self.logger.error('"FormantSetup" configuration part not in loaded setup json!')

    def log_config(self):
        lines = []
        lines.append('  configHolderVersion:    '+str(self.version))

        lines.append('  ffmpeg/ffPath:      '+'"'+str(self.ffmpeg_ffPath)+'"')
        lines.append('  ffmpeg/FS:          '+str(self.ffmpeg_FS))
        lines.append('  ffmpeg/tdtaChunk:   '+str(self.ffmpeg_tdtaChunk))
        lines.append('  ffmpeg/bigChunk:    '+str(self.ffmpeg_bigChunk))

        lines.append('  F0/minF0:           '+str(self.F0_minF0))
        lines.append('  F0/maxF0:           '+str(self.F0_maxF0))
        lines.append('  F0/timeStep:        '+str(self.F0_timeStep))
        
        lines.append('  FeatExt/filter:     '+str(self.FeatExt_filter))
        
        lines.append('  Intens/minPitch:    '+str(self.Intens_minPitch))
        lines.append('  Intens/mSilDur:     '+str(self.Intens_minSilentDuration))
        lines.append('  Intens/mVoicDur:    '+str(self.Intens_minVoicedDuration))
        lines.append('  Intens/minDip:      '+str(self.Intens_minDip_dB))
        lines.append('  Intens/SilVoice:    '+str(self.Intens_VoiceSildB))

        lines.append('  Formant/timeStep:   '+str(self.Formant_timeStep))
        lines.append('  Formant/maxNofFmts: '+str(self.Formant_maxNofFmts))
        lines.append('  Formant/maxFmtFreq: '+str(self.Formant_maxFmtFreq))
        lines.append('  Formant/winLength:  '+str(self.Formant_winLength))
        lines.append('  Formant/preemFreq:  '+str(self.Formant_preemFreq))
        lines.append('  Formant/freqMargin: '+str(self.Formant_freqMargin))

        lines.append('  IPU/frameSize:      '+str(self.IPU_frameSize))
        lines.append('  IPU/frameShift:     '+str(self.IPU_frameShift))
        lines.append('  IPU/filter:         '+str(self.IPU_filter))


        msg = ('====== FE setup: =======\n'+
               '\n'.join(lines)+'\n'+
               '========================')
        self.logger.info('\n'+msg)
    def verify_config(self):
        ready = True
        if not os.path.exists(self.ffmpeg_ffPath) and self.ffmpeg_ffPath != '':
            self.logger.error('invalid ffPath: '+str(self.ffmpeg_ffPath))
            ready = False
        if not 8000 <= self.ffmpeg_FS <= 48000:
            self.logger.error('invalid FS: not in range 8k-48k Hz: '+str(self.ffmpeg_FS))
            ready = False
        if not 400 <= self.ffmpeg_tdtaChunk <= 4000:
            self.logger.error('invalid tdtaChunk Size: not in range 400-4000: '+str(self.ffmpeg_tdtaChunk))
            ready = False
        if not 4000 <= self.ffmpeg_bigChunk <= 300000:
            self.logger.error('invalid bigChunk: not in range 8k-300k: '+str(self.ffmpeg_bigChunk))
            ready = False


                   

        self.logger.info('ConfigHolder ready: '+str(ready))
        self.ready = ready
    def validPath_creatable(self,pthIn):
        P = os.path.abspath(pthIn)
        part0 = Path(P).parts[0]
        return(os.path.exists(part0))
