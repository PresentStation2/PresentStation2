import traceback
import subprocess
import os
import numpy
import logging

class FFMPegConnector():
    def __init__(self,LogFunction,settings):
        self.LogEvent = LogFunction
        try:
            self.ffmpeg = settings.ffmpeg
            self.FS = settings.workingFS
            self.longChunk = settings.chunk_size
        
        except:
            err = str(traceback.format_exc(limit=None, chain=True))
            self.LogEvent(err, logging.ERROR)
        
        self.ffmpeg_status = 'idle'
        
    def connect_to_audio(self,media_source):
        try:
            if os.path.exists(media_source):
                self.ffmpeg_connection = subprocess.Popen([self.ffmpeg, "-i", media_source,
                     "-loglevel", "panic", "-vn", "-ar", str(self.FS),
                     "-ac", "1", "-f",  "s16le", "pipe:1"],
                     stdout=subprocess.PIPE)
                self.ffmpeg_status = 'connected'
                self.time_data_buffer = numpy.zeros((1,0))
            else:
                self.log_event("ffmpegConnector couldn't find media source: "+str(media_source),'error',printIt=True)
                self.ffmpeg_status ='failed'
        except:
            err = str(traceback.format_exc(limit=None, chain=True))
            self.log_event('ffmpeg connection failed: '+err,'error')
            self.ffmpeg_status ='failed'
    def get_next_time_data(self,NSamples):
        try:
            if self.ffmpeg_status == 'connected':
                while NSamples >= self.time_data_buffer.shape[1] and self.ffmpeg_status == 'connected':
                    chunk = self.ffmpeg_connection.stdout.read(self.longChunk)
                    if len(chunk) > 0:
                        tdta = (numpy.fromstring(chunk, dtype="int16"))
                        self.time_data_buffer = numpy.concatenate( (self.time_data_buffer , tdta.reshape((1,tdta.size))) , axis=1)
                    else:
                        TimeData = numpy.zeros((1,0))
                        self.ffmpeg_status = 'media finished'
                        return TimeData

                TimeData = self.time_data_buffer[:,:NSamples]
                self.time_data_buffer = self.time_data_buffer[:,NSamples:]
                return TimeData
            else:
                self.out_of_data = True
                return None
        except:
            err = str(traceback.format_exc(limit=None, chain=True))
            self.log_event('get_next_time_data failed: '+err,'error')
            self.ffmpeg_status ='failed'
            self.out_of_data = True
            return None

 
class BandPass_TimeData_Provider():
    def __init__(self, FIR_filter_coeffs, chunkSize, shiftSize, demandData):

            self.ready = True
            self.sourceDepleted = False
            self.FIR = numpy.array(FIR_filter_coeffs)
            self.chunkSize = chunkSize
            self.shiftSize = shiftSize
 
            if len(self.FIR) > self.chunkSize:
                self.log_event('FIR filter set too long for implemented overlap!','error',printIt=True)
                self.ready = False
 
            self.out_buffer = []
            self.filter_sum_buffer = numpy.zeros(len(self.FIR)-1)
            self.tdta_buffer = []
 
            self.demandData = demandData
 
            self.frameStartPosition = 0
    def acceptTimeData(self,tdta):
        if tdta is None:
            self.sourceDepleted = True
        elif tdta.shape[1] > 0:
            self.tdta_buffer += list(tdta[0,:])
            while len(self.tdta_buffer) >= self.chunkSize:
                tdta = self.tdta_buffer[:self.chunkSize]
 
                cnv = numpy.convolve(tdta, self.FIR, mode='full')
                toBuff,overlap = cnv[:self.chunkSize],cnv[self.chunkSize:]
 
                toBuff[:len(self.FIR)-1] += self.filter_sum_buffer
                self.filter_sum_buffer = overlap
 
                self.out_buffer.append( ( self.frameStartPosition,toBuff ) )
                self.frameStartPosition += self.shiftSize
 
                del(self.tdta_buffer[:self.shiftSize])
    def getNextBuffer(self):
        if len(self.out_buffer) > 0:
            nextBuff = self.out_buffer[0]
            del(self.out_buffer[0])
            return nextBuff
        elif self.sourceDepleted:
            return ((None,None))
        else:
            while not self.sourceDepleted:
                self.demandData()
 
                if len(self.out_buffer) > 0:
                    nextBuff = self.out_buffer[0]
                    del(self.out_buffer[0])
                    return nextBuff
                elif self.sourceDepleted:
                    return ((None,None))
