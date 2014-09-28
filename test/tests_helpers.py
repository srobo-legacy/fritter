
from os.path import abspath, dirname

def root():
    return dirname(dirname(abspath(__file__)))
