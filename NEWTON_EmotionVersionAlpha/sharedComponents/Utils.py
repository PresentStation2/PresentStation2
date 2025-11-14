from sharedComponents.ConfigHolder import ConfigHolder
from sharedComponents.RawAudioMonoProvider import RawAudioMonoProvider

import pathlib
import logging
import os

def CreateLogger(logPath):
    absPth = os.path.abspath(logPath)
    pth = os.path.split(absPth)[0]
    if not os.path.exists(pth):
        pathlib.Path( pth ).mkdir(parents=True, exist_ok=True)

    handler = logging.FileHandler(absPth)
    logger = logging.getLogger('FeatureExtractorLogger'+str(handler))
    logger.setLevel(level=logging.DEBUG)
    logger.addHandler(handler)
    
    return logger

def InitConfig(jsn, log):
    logger = CreateLogger(log)
    MyConfigHolder = ConfigHolder(logger) 
    MyConfigHolder.loadConfiguration(jsn)

    return MyConfigHolder, logger

def GetAudio(audioIn, MyConfigHolder, logger):
    RawMonoProvider = RawAudioMonoProvider(logger, MyConfigHolder)
    rawMono = RawMonoProvider.GetWholeRecording(audioIn)
    del(RawMonoProvider)

    return rawMono