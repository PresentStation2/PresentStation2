import os
import numpy
from sharedComponents.FFmpegConnector import FFMPegConnector


class RawAudioMonoProvider():
    def __init__(self, logger, configHolder):
        
        self.logger = logger
        self.ConfigHolder = configHolder
        if not self.ConfigHolder.ready:
            logger.error('ConfigHolder not ready!')
            raise Exception('ConfigHolder not ready!')
        
        self.FS = self.ConfigHolder.ffmpeg_FS
        self.tdtaFrameSize = self.ConfigHolder.ffmpeg_tdtaChunk
        
    def GetWholeRecording(self, media):
        self.ffmpegConnector = FFMPegConnector(self.ConfigHolder.ffmpeg_ffPath , self.logger, self.FS)
        self.ffmpegConnector.connect_to_audio(media)
        
        # find sample size...
        duration = 0
        tdta = self.ffmpegConnector.get_next_time_data(self.tdtaFrameSize)
        

        while not self.ffmpegConnector.out_of_data:
            duration += tdta.shape[1]                
            tdta = self.ffmpegConnector.get_next_time_data(self.tdtaFrameSize)       
        
        del(self.ffmpegConnector)

        # get data: 
        return self.GetMonoInTimeSpan(media, 0.0, float(duration)/float(self.FS))
        
    
    def GetMonoInTimeSpan(self, media, begin, end):
        begIndex = int(begin*self.FS)
        endIndex = int(end*self.FS)
                
        if endIndex <= begIndex:
            err = "GetMonoInTimeSpan: begin "+str(begin)+" must be smaller than end "+str(end)
            self.logger.error(err)
            raise Exception(err)
        
        if not os.path.exists(media):
            err = "GetMonoInTimeSpan: media not available: "+str(media)
            self.logger.error(err)
            raise Exception(err)
        
        self.ffmpegConnector = FFMPegConnector(self.ConfigHolder.ffmpeg_ffPath , self.logger, self.FS)
        self.ffmpegConnector.connect_to_audio(media)
        
        outOfRange = True
        
        outPut = numpy.zeros(endIndex-begIndex)
        offset = 0        
        tdta = self.ffmpegConnector.get_next_time_data(self.tdtaFrameSize)

        while offset < endIndex and not self.ffmpegConnector.out_of_data:
            
            if offset <= endIndex and offset+self.tdtaFrameSize > begIndex:
                outOfRange = False
                
                for i in range(tdta.shape[1]):
                    realIndex = offset+i
                    if begIndex <= realIndex <= endIndex:
                        outPut[realIndex-begIndex] = tdta[0,i]                
                
            tdta = self.ffmpegConnector.get_next_time_data(self.tdtaFrameSize)

            try:
                offset += tdta.shape[1]
            except:
                pass
        
        if outOfRange:
            err = "GetMonoInTimeSpan: demanded time interval not in recording range"
            self.logger.error(err)
            raise Exception(err)    
        
        del self.ffmpegConnector

        return outPut


