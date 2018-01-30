""" Хранение настроек приложения """

import os
import csv
import configparser

class Config:
    
    def __init__(self,namefile_cfg = "config.ini"):
        self.namefile_cfg = namefile_cfg
        self.token=None
        if not os.path.exists(self.namefile_cfg):
            return
        config = configparser.ConfigParser()
        config.read(self.namefile_cfg)
        self.token = str(config['BOT']['token'])







