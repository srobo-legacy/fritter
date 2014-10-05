
from os.path import abspath, dirname, exists, join

def root():
    return dirname(test_root())

def test_root():
    return dirname(abspath(__file__))

def test_data(file_name = ''):
    file_path = join(test_root(), 'data', file_name)
    assert exists(file_path), "Data file '{0}' doesn't exist!".format(file_name)
    return file_path
