"""Miscellanea routines used by pyfant.

The rule here is *not* to import any pyfant module, except for errors. This is to
avoid cyclic imports.

Miscellanea routines that import pyfant modules should be put in util.py instead.
"""
__all__ = ["str_vector", "float_vector", "int_vector", "readline_strip",
 "multirow_str_vector", "ordinal_suffix", "path_to_default", "new_filename",
 "write_lf", "slugify", "adjust_atomic_symbol", "str2bool", "bool2str",
 "list2str", "chunk_string", "add_file_handler", "LogTwo", "SmartFormatter",
 "X", "HR", "log_noisy", "fmt_ascii_h1", "fmt_error", "print_error", "menu",
 "random_name", "format_BLB"
]
import os.path
import glob
import random
from threading import Lock
import logging
import sys
from matplotlib import rc
from .errors import *
import re
from argparse import *
# Logger for internal use
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())


# #################################################################################################
# I/O routines

def str_vector(f):
    """Reads next line of file and makes it a vector of strings

    Note that each str.split() already strips each resulting string of any whitespaces."""
    return f.readline().split()


def float_vector(f):
    """Reads next line of file and makes it a vector of floats."""
    return [float(s) for s in str_vector(f)]


def int_vector(f):
    """Reads next line of file and makes it a vector of floats."""
    return [int(s) for s in str_vector(f)]


def readline_strip(f):
    """Reads next line of file and strips the newline."""
    return f.readline().strip('\n')


def multirow_str_vector(f, n, r=0):
    """
    Assembles a vector that spans several rows in a text file.

    Arguments:
      f -- file-like object
      n -- number of values expected
      r (optional) -- Index of last row read in file (to tell which file row in
                      case of error)

    Returns:
      (list-of-strings, number-of-rows-read-from-file)
    """

    so_far = 0
    n_rows = 0
    v = []
    while True:
        temp = str_vector(f)
        n_rows += 1
        n_now = len(temp)

        if n_now+so_far > n:
            _logger.warning(('Reading multi-row vector: '
                'row %d should have %d values (has %d)') %
                (r+n_rows, n-so_far, n_now))

            v.extend(temp[:n-so_far])
            so_far = n

        elif n_now+so_far <= n:
            so_far += n_now
            v.extend(temp)

        if so_far == n:
            break

    return v, n_rows


def path_to_default(fn):
  """Returns full path to default data file."""
  p = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "default", fn)
  return p


def new_filename(prefix, extension=""):
  """Returns a file name that does not exist yet, e.g. prefix.0001.extension"""
  i = 0
  while True:
    ret = '%s.%04d.%s' % (prefix, i, extension) \
      if extension else '%s.%04d' % (prefix, i)
    if not os.path.exists(ret):
      break
    i += 1
    return ret


def write_lf(h, s):
  """Adds lf to end of string and writes it to file."""
  h.write(s+"\n")


def slugify(value, flagLower=True):
  """
  Converts to lowercase, removes non-alpha characters,
  and converts spaces to hyphens.

  Useful for making file names.

  Source: http://stackoverflow.com/questions/5574042/string-slugification-in-python
  """
  value = re.sub('[^\w\s.]', '', value).strip()
  if flagLower:
    value = value.lower()
  value = re.sub('[-\s]+', '-', value)
  return value


# #################################################################################################
# Conversion routines

def adjust_atomic_symbol(x):
    """Makes sure atomic symbol is right-aligned and upper case (PFANT convention)."""
    assert isinstance(x, str)
    return "%2s" % (x.strip().upper())


def str2bool(s):
  """Understands "T"/"F" only (case-sensitive). To be used for file parsing."""
  if s == "T":
    return True
  elif s == "F":
    return False
  raise ValueError("I don't understand '%s' as a logical value" % s)


def bool2str(x):
  """Converts bool variable to either "T" or "F"."""
  assert isinstance(x, bool)
  return "T" if x else "F"


def list2str(l):
  """Converts list to string without the brackets."""
  return " ".join([str(x) for x in l])


def chunk_string(string, length):
  """
  Splits a string into fixed-length chunks.
  
  This function returns a generator, using a generator comprehension. The
  generator returns the string sliced, from 0 + a multiple of the length
  of the chunks, to the length of the chunks + a multiple of the length
  of the chunks.

  Reference: http://stackoverflow.com/questions/18854620
  """
  return (string[0+i:length+i] for i in range(0, len(string), length))


def ordinal_suffix(i):
    """Returns 'st', 'nd', or 'rd'."""
    return 'st' if i == 1 else 'nd' if i == 2 else 'rd' if i == 3 else 'th'


# #################################################################################################
# Logging routines

def add_file_handler(logger, logFilename=None):
  """Adds file handler to logger."""

  assert isinstance(logger, logging.Logger)

  ch = logging.FileHandler(filename=logFilename)
  ch.setFormatter(logging._defaultFormatter) # todo may change to have same formatter as last handler of logger
  logger.addHandler(ch)


class LogTwo(object):
  """Logs messages to both stdout and file."""
  def __init__(self, filename):
    self.terminal = sys.stdout
    self.log = open(filename, "a")

  def write(self, message):
    self.terminal.write(message)
    self.log.write(message)


class SmartFormatter(RawDescriptionHelpFormatter):
    """
    Help formatter that will show default option values and also respect
    newlines in description. Neither are done in default help formatter.
    """

    def _get_help_string(self, action):
        help = action.help
        if '%(default)' not in action.help:
            if action.default is not SUPPRESS:
                defaulting_nargs = [OPTIONAL, ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += ' (default: %(default)s)'
        return help


        # # this is the RawTextHelpFormatter._split_lines
        # if text.startswith('R|'):
        #     return text[2:].splitlines()
        # return argparse.ArgumentDefaultsHelpFormatter._split_lines(self, text, width)


# character for boxing strings
X = "*"
HR = X*40
def log_noisy(logger, msg):
    """Prints string message with box around.

    This was designed to outstand in a long log dump.
    """

    xx = X*(len(msg)+4)
    logger.info("")
    logger.info(xx)
    logger.info("%s %s %s" % (X, msg, X))
    logger.info(xx)


# #################################################################################################
# Text interface routines - routines that are useful for building a text interface

def fmt_ascii_h1(s):
    """Returns string enclosed in an ASCII frame, with \n line separators. Does not end in \n."""
    n = len(s)
    return "/"+("-"*(n+2))+"\\\n"+ \
           "| "+s+" |\n"+ \
           "\\"+("-"*(n+2))+"/"

def fmt_error(s):
    """Standardized embellishment. Adds formatting to error message."""
    return "!! %s !!" % s

def print_error(s):
    """Prints string as error message."""
    print fmt_error(s)

def menu(title, options, cancel_label="Cancel", flag_allow_empty=False):
  """Text menu.

  Arguments:
    title
    options -- sequence of strings
    cancel_label='Cancel' -- label to show at last "zero" option
    flag_allow_empty=0 -- Whether to allow empty option

  Returns:
    option -- an integer: None; 0-Back/Cancel/etc; 1, 2, ...

  Adapted from irootlab menu.m"""

  no_options, flag_ok, ch, lt = len(options), 0, 'p', len(title)
  option = None  # result

  while True:
    print ""
    print "  "+ch*(lt+8)
    print "  "+ch*3+" "+title+" "+ch*3
    print "  "+ch*(lt+8)
    for i, s in enumerate(options):
      print "  %d - %s" % (i+1, s)
    print "  0 - << (*%s*)" % cancel_label
    s_option = raw_input('? ')

    n_try = 0
    while True:
      if n_try >= 10:
        print 'You are messing up!'
        break

      if len(s_option) == 0 and flag_allow_empty:
        flag_ok = True
        break

      try:
        option = int(s_option)
        if 0 <= option <= no_options:
          flag_ok = True
          break
      except ValueError:
        print "Invalid integer value!"

      print "Invalid option, range is [%d, %d]!" % (0, no_options)

      n_try += 1
      s_option = raw_input("? ")

    if flag_ok:
      break
  return option


# #################################################################################################
# Miscellanea of miscellanea

_forenames = ["Solomon", "John", "Loretta", "Stephen", "Harry", "Nancy", "Tracy", "Maggie", "Lafanda", "Napoleon", "Joe",
        "Ana", "Olivia", "Lucia", "Julien", "June", "Ada", "Blaise", "Platypus", "R2D2", "Obi-Wan",
        "Yoda", "Lancelot", "Shaun", "C3PO", "Luke", "George", "Martin", "Elvira", "Galileo", "Elizabeth",
        "Genie", "Mark", "Karl", "Henry-David", "Ludmilla", "Darth", "Bayden", "Plamen", "Margareth", "Javier",
        "Pouria", "Klen", "Lydiane", "Charlotte", "Edna", "Ricardo", "Francis", "Jemma", "Valon", "Imran", "Sian",
        "Hayat", "Taghreed", "Orla", "Michael", "Lourdes", "Weiyi", "Thomas", "Willian", "Miguel", "Rui",
        "Abdullah", "Angus", "Malcolm", "Donald", "Mickey", "Polona", "Rashmi", "Xiaowei", "Sasha", "Luciano",
        "Avinash", "Anthony", "Karen", "Matthew", "Tatiana", "Mariana", "Antonio", "Hamilton", "Pauderney"]
_surnames = ["Northupp", "Kanobi", "de Morgan", "de Vries", "van Halen", "McFly", "Wallace", "McLeod", "Skywalker", "Smith",
       "Silva", "da Silva", "Sexy", "Coupat", "Coupable", "Byron", "Lovelace", "Pascal", "Kareninski", "Dynamite",
       "Souza", "Ha", "Balboa", "Durden", "V.", "Li", "Manco", "Kelly", "Torquato", "Sampaio", "Bittencourt", "Parisi",
       "Oliveira", "Crap", "Copppercup", "Motherfucker", "Firehead", "Martin", "Papanicolau", "Galilei", "Stuart",
       "Bitch", "King", "Cleese", "Thoreau", "Twain", "Marx", "Yankovicz", "Vader", "Prado", "Teixeira", "Oliveira",
       "Nogueira", "Pereira", "Sant'anna", "Kerns", "Patel", "Ahmadzai", "Riding", "Llabjani", "Maus",
       "Liger", "Byrne", "Wood", "Angelov", "Andreu", "Sadeghi", "Gajjar", "Kara", "Wolstenholme", "Alghaith",
       "Young", "Scott", "Luz", "Copic", "Pucihar", "Zhou", "Dutta", "Baruah", "Singh", "Sauro", "do Nascimento",
       "Lee", "Trevisan", "Travisani", "Pereira", "Nandwani", "Moura", "Senna"]
_prefixes = ["Dr.", "Prof.", "Sir", "Ven."]
_suffixes = ["The 3rd", "Jr.", "Sobrinho", "Neto", "VIII", "XVI", "I", "II", "III", "IV"]
_PROB_PREF = 0.1
_PROB_SUFF = 0.1
def random_name():
  a = []

  # Prefix
  if random.random() < _PROB_PREF:
    a.append(_prefixes[random.randint(0, len(_prefixes)-1)])

  # Forename
  a.append(_forenames[random.randint(0, len(_forenames)-1)])

  # Surnames
  n = 2  # Number of surnames
  for i in range(n):
    a.append(_surnames[random.randint(0, len(_surnames)-1)])

  # Suffix
  if random.random() < _PROB_SUFF:
    a.append(_suffixes[random.randint(0, len(_suffixes)-1)])

  return " ".join(a)


# #################################################################################################
# Matplotlib-related routines

def format_BLB():
    """Sets some formatting options in Matplotlib."""
    rc('font', family = 'serif', serif = 'cmr10')
    rc('xtick', labelsize=14)
    rc('ytick', labelsize=14)
    #rc('text', usetex=True)

