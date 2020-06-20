from . import Config


class ProductionConfig(Config):
    '''
        Configuration in development mode
    '''

    DEBUG = False
