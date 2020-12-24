import logging
import logging.config

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'normal': {
            'format': '%(asctime)s - %(process)d %(levelname)s / %(message)s'
        },
        'simple': {
            'format': '%(message)s'
        },
    },
    'handlers': {
        'console1': {  
            'class': 'logging.StreamHandler',  # emit to sys.stderr(default)
            'formatter': 'normal', 
        },
        'console2': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple', 
        },
        'debug': {
            'class': 'logging.FileHandler',  # emit to disk file
            'filename': 'listener.log',  
            'formatter': 'normal', 
        },
        'error': {
            'class': 'logging.FileHandler',
            'filename': 'listener_error.log',
            'formatter': 'normal',
        },
    },
    'loggers': {
        'console': {
            'handlers': ['console2'],
            'level': 'INFO',
        },
        'DebugLogger': {
            'handlers': ['debug'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'ErrorLogger': {
            'handlers': ['error'],
            'level': 'ERROR',
            'propagate': True,
        },

    },
}

