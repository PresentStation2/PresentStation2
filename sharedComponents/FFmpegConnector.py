import traceback
import platform
import os
import subprocess
import numpy


class FFMPegConnector():
    def __init__(self, ffmpeg_path, logger, FS):
        self.logger = logger
        self.ffmpeg_path = ffmpeg_path
        self.init_ffmpeg()
        self.ffmpeg_status = 'idle'

        self.FS = FS
        self.shortChunk = 1600
        self.longChunk = 32768
        
        self.out_of_data = False

    def init_ffmpeg(self):
        oscd = platform.system()
        ff_active,ff_set = False,False
        if oscd == 'Windows':
            if len(self.ffmpeg_path.strip()) > 0:
                self.ffmpeg =  os.path.join(self.ffmpeg_path.strip(),'ffmpeg.exe')
                self.ffprobe = os.path.join(self.ffmpeg_path.strip(),'ffprobe.exe')
            else:
                self.ffmpeg  = 'ffmpeg.exe'
                self.ffprobe = 'ffprobe.exe'
            ff_set = True

        elif oscd == 'Linux':
            if len(self.ffmpeg_path.strip()) > 0:
                self.ffmpeg =  os.path.join(self.ffmpeg_path.strip(),'ffmpeg')
                self.ffprobe = os.path.join(self.ffmpeg_path.strip(),'ffprobe')
            else:
                self.ffmpeg =  'ffmpeg'
                self.ffprobe = 'ffprobe'
            ff_set = True

        else:
            self.status = 'failure'
            self.logger.error('ff-path failure - unsupported platform: '+str(oscd))

        if ff_set:
            process = subprocess.Popen(self.ffmpeg +' version',stdout=subprocess.PIPE,stderr=subprocess.PIPE, shell=True)
            ff_ver = process.communicate()[1]
            if 'ffmpeg version' in str(ff_ver):
                ff_active = True

            self.logger.info(('ff-tools set:\r    ffmpeg: '+str(self.ffmpeg)+
                            '\r    ffprobe: '+str(self.ffprobe)+
                            '\r    ffmpeg available: '+str(ff_active)
                            ))
        self.ready = ff_active

    def connect_to_audio(self, media_source):
        try:
            if os.path.exists(media_source):
                self.ffmpeg_connection = subprocess.Popen([self.ffmpeg, "-i", media_source,
                     "-loglevel", "panic", "-vn", "-ar", str(self.FS),
                     "-ac", "1", "-f",  "s16le", "pipe:1"],
                     stdout=subprocess.PIPE)
                self.ffmpeg_status = 'connected'
                self.time_data_buffer = numpy.zeros((1,0))
            else:
                self.logger.error("ffmpegConnector couldn't find media source: "+str(media_source))
                self.ffmpeg_status ='failed'
        except:
            err = str(traceback.format_exc(limit=None, chain=True))
            self.logger.error('ffmpeg connection failed: '+err)
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
                
                norm = 1.0 / float(32768)
                return norm*TimeData
            else:
                self.out_of_data = True
                return None
        except:
            err = str(traceback.format_exc(limit=None, chain=True))
            self.logger.error('get_next_time_data failed: '+err)
            self.ffmpeg_status ='failed'
            self.out_of_data = True
            return None