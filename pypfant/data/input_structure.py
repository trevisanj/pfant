"""
Ancestor class for all classes that represent an input file.
"""

__all__ = ["input_structure"]

class input_structure(object):
    default_filename = None  ## Descendants shoulds set this

    def save(self, filename):
        raise NotImplementedError()

    def load(self, filename):
        raise NotImplementedError()