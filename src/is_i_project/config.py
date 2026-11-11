import os


class Config:
    '''Configuración base compartida.'''

    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    '''Configuración para desarrollo con SQLite.'''

    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DEV_DATABASE_URL',
        'sqlite:///dev.db',
    )


class TestingConfig(Config):
    '''Configuración para testing con otra base de datos SQLite.'''

    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'sqlite:///test.db',
    )


class ProductionConfig(Config):
    '''Configuración para producción (pendiente de implementación).'''


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
