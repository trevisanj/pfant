__all__ = ["FileAbsoru2"]

from .inputfile import *


class FileAbsoru2(InputFile):
  default_filename = "absoru2.dat"

  def __init__(self):
    pass

  def load(self, filename):
    raise NotImplementedError("This class is a stub ATM")

  def save(self, filename):
    raise NotImplementedError("This class is a stub ATM")
