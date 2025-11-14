import logging
import os
import json
import platform
import subprocess

class SettingHolder():
    def __init__(self, logEvent, jsnSetting=None):
        self.LogEvent = logEvent
        self.InitContent()
        if jsnSetting and self.JsonExists(jsnSetting):
            self.JsonOverride(jsnSetting)
        self.LogSettings()
        self.setFFPaths()
        
    def InitContent(self):
        self.status = 'initializing'
        self.ffmpegPath = ""
        self.workingFS = 16000
        self.tdta_chunk = 800
        self.chunk_size = 32768
        
        self.FilterCoeffs = [0.3, 0.3, 0.3]
        
        
        #=======================================================================
        # noises: ["0","1","2","3","4","5","6","7","8","9","-","E"]
        # noiseCodes: {
        #     "[n::silence]":"-",
        #     "[n::click]":"1",
        #     "[n::rustle]":"2",
        #     "[h::breath]":"3",
        #     "[n::rumble]":"4",
        #     "[h::ehm]":"5",
        #     "[n::longnoise]":"9",
        #     "[h::stroke]":"8",
        #     "":"-"   }
        #=======================================================================
    def JsonExists(self, jsn):
        if not isinstance(jsn, str):
            return False
        if not os.path.exists(jsn):
            self.LogEvent("given json path not found: "+jsn, logging.ERROR)
            return False
        return True
    def JsonOverride(self, jsn):
        self.LogEvent("loading json override: "+jsn, logging.INFO)
        with open(jsn, 'r', encoding='utf-8') as jsonFile:
            overRide = json.load(jsonFile)
        
        if "ffmpegSetup" in overRide:
            ffs = overRide["ffmpegSetup"]
            if "ffmpegPath" in ffs:
                self.ffmpegPath = ffs['ffmpegPath']
            else:
                self.LogEvent("'ffmpegPath' not in ffmpegSetup override", logging.INFO)

            if "workingFS" in ffs:
                self.workingFS = int(ffs['workingFS'])
            else:
                self.LogEvent("'workingFS' not in ffmpegSetup override", logging.INFO)

            if "tdta_chunk" in ffs:
                self.tdta_chunk = int(ffs['tdta_chunk'])
            else:
                self.LogEvent("'tdta_chunk' not in ffmpegSetup override", logging.INFO)            
            
            if "chunk_size" in ffs:
                self.chunk_size = ffs['chunk_size']
            else:
                self.LogEvent("'chunk_size' not in ffmpegSetup override", logging.INFO)
            
        else:
            self.LogEvent("ffmpegSetup override not in json override", logging.INFO)
        
        
        if "featureExtractor" in overRide:
            fes = overRide["featureExtractor"]
            if "FilterCoeffs" in fes:
                self.FilterCoeffs = fes['FilterCoeffs']
            else:
                self.LogEvent("'ffmpFilterCoeffsegPath' not in featureExtractor override", logging.INFO)

            
        else:
            self.LogEvent("featureExtractor override not in json override", logging.INFO)
    def setFFPaths(self):
        oscd = platform.system()
            
        ff_set = False
        if oscd == 'Windows':
            if len(self.ffmpegPath.strip()) > 0:
                self.ffmpeg =  os.path.join(self.ffmpegPath.strip(),'ffmpeg.exe')
                self.ffprobe = os.path.join(self.ffmpegPath.strip(),'ffprobe.exe')
            else:
                self.ffmpeg  = 'ffmpeg.exe'
                self.ffprobe = 'ffprobe.exe'
            ff_set = True
 
        elif oscd == 'Linux':
            if len(self.ffmpegPath.strip()) > 0:
                self.ffmpeg =  os.path.join(self.ffmpegPath.strip(),'ffmpeg')
                self.ffprobe = os.path.join(self.ffmpegPath.strip(),'ffprobe')
            else:
                self.ffmpeg =  'ffmpeg'
                self.ffprobe = 'ffprobe'
            ff_set = True
 
        else:
            self.status = 'failure'
            self.LogEvent('ff-path failure - unsupported platform: '+str(oscd), logging.ERROR)
 
        if ff_set:
            process = subprocess.Popen(self.ffmpeg +' version',stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
            ff_ver = process.communicate()[1]
            if 'ffmpeg version' in str(ff_ver):
                ff_active = True
 
            self.LogEvent(('ff-tools set:\r    ffmpeg: '+str(self.ffmpeg)+
                            '\r    ffprobe: '+str(self.ffprobe)+
                            '\r    ffmpeg available: '+str(ff_active)
                            ), logging.INFO)
            self.status = 'ready'
    def LogSettings(self):
        self.LogEvent("ffmpegPath:   '"+self.ffmpegPath+"'", logging.INFO)
        self.LogEvent("workingFS:    "+str(self.workingFS), logging.INFO)
        self.LogEvent("tdta_chunk:   "+str(self.tdta_chunk), logging.INFO)
        self.LogEvent("chunk_size:   "+str(self.chunk_size), logging.INFO)
        
        self.LogEvent("FilterCoeffs: "+str(len(self.FilterCoeffs))+" coeffs: "+str(self.FilterCoeffs)[:30], logging.INFO)
        
        self.LogEvent("Setting status: "+self.status, logging.INFO)
        

        