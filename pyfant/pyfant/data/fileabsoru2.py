__all__ = ["FileAbsoru2"]

from .datafile import *


class FileAbsoru2(DataFile):
  default_filename = "absoru2.dat"

  def __init__(self):
    DataFile.__init__(self)

  def _do_load(self, filename):
    raise NotImplementedError("This class is a stub ATM")

  def _do_save_as(self, filename):
    raise NotImplementedError("This class is a stub ATM")
