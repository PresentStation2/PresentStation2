import logging, datetime

class Logger():
    def __init__(self, logName='theTrue.log'):
        handler = logging.FileHandler(logName)
        logger = logging.getLogger('configHolderBckpLog')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        self.logger = logger
    def LogEvent(self,text,typ,printIt=False):
        msg = str(datetime.datetime.now())+' : '+str(text)
        if typ == logging.INFO:
            msg = '[INFO] '+msg
            self.logger.info(msg)
        elif typ == logging.ERROR:
            msg = '[ERROR] '+msg
            self.logger.error(msg)
        else:
            msg = '[???] '+msg
            self.logger.error(msg)

        if printIt:
            print(msg)