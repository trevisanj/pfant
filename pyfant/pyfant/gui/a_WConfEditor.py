"""Widget to edit a Conf object."""

__all__ = ["WFileMain"]

from PyQt4.QtCore import *
from PyQt4.QtGui import *
# from ._guiaux import *
# from .guimisc import *
from pyfant import FileMain

# Color for labels indicating a star parameter
COLOR_STAR = "#2A8000"
# Color for labels indicating a software configuration parameter
COLOR_CONFIG = "#BD6909"

def _enc_name_descr(name, descr, color="#FFFFFF"):
    # Encodes html given name and description
    return _enc_name(name, color)+"<br>"+descr

def _enc_name(name, color="#FFFFFF"):
    # Encodes html given name and description
    return "<span style=\"color: %s; font-weight: bold\">%s</span>" % \
           (color, name)

class WFileMain(QWidget):
    """
    FileMain editor widget.

    Arguments:
      parent=None
    """

    # Emitted whenever any value changes
    edited = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        # Whether all the values in the fields are valid or not
        self.flag_valid = True
        # Internal flag to prevent taking action when some field is updated programatically
        self.flag_process_changes = False
        self.f = None # FileMain object

        la = self.formLayout = QGridLayout()
        la.setVerticalSpacing(4)
        la.setHorizontalSpacing(5)
        self.setLayout(la)
        # field map: [(label widget, edit widget, field name, short description,
        #              field name color, long description), ...]
        pp = self._map = []

        x = self.label_titrav = QLabel()
        y = self.lineEdit_titrav = QLineEdit()
        # y.editingFinished.connect(self._on_editing_finished)
        y.textEdited.connect(self._on_edited)
        y.installEventFilter(self)
        x.setBuddy(y)
        pp.append((x, y, "t&itrav", "star name", COLOR_STAR,
         "Name of the star."))

        x = self.label_teff = QLabel()
        y = self.lineEdit_teff = QLineEdit()
        y.textEdited.connect(self._on_edited)
        y.installEventFilter(self)
        y.setValidator(QDoubleValidator(0, 1e10, 0))
        x.setBuddy(y)
        pp.append((x, y, "&teff", "effective temperature", COLOR_STAR,
         "Sun: 5777"))

        x = self.label_glog = QLabel()
        y = self.lineEdit_glog = QLineEdit()
        y.textEdited.connect(self._on_edited)
        y.installEventFilter(self)
        y.setValidator(QDoubleValidator(0, 1e10, 5))
        x.setBuddy(y)
        pp.append((x, y, "&glog", "gravity", COLOR_STAR,
         "Sun: 4.44"))

        x = self.label_asalog = QLabel()
        y = self.lineEdit_asalog = QLineEdit()
        y.textEdited.connect(self._on_edited)
        y.installEventFilter(self)
        y.setValidator(QDoubleValidator(-10, 10, 5))
        x.setBuddy(y)
        pp.append((x, y, "&asalog", "metallicity", COLOR_STAR,
         "Sun: 0"))

        x = self.label_nhe = QLabel()
        y = self.lineEdit_nhe = QLineEdit()
        y.textEdited.connect(self._on_edited)
        y.installEventFilter(self)
        y.setValidator(QDoubleValidator(0, 10, 5))
        x.setBuddy(y)
        pp.append((x, y, "&nhe", "abundance of Helium", COLOR_STAR,
         "Sun: 0.1"))

        x = self.label_ptdisk = QLabel()
        y = self.checkBox_ptdisk = QCheckBox()
        y.setTristate(False)
        y.installEventFilter(self)
        # y.stateChanged.connect(self._on_edited)
        x.setBuddy(y)
        pp.append((x, y, "pt&disk", "point of disk?", COLOR_CONFIG,
         "This option is used to simulate a spectrum acquired "
         "out of the center of the star disk.<br><br>"
         "This is useful if the synthetic spectrum will be compared with an "
         "observed spectrum acquired out of the center of the star disk."))

        x = self.label_mu = QLabel()
        y = self.lineEdit_mu = QLineEdit()
        y.installEventFilter(self)
        y.textEdited.connect(self._on_edited)
        y.setValidator(QDoubleValidator(-1, 1, 5))
        x.setBuddy(y)
        pp.append((x, y, "&mu", "cosine of angle", COLOR_CONFIG,
         "This is the cosine of the angle formed by center of "
         "the star disk, the point of observation, and the Earth as vertex. "
         "<br><br>This value will be used only if "+_enc_name("ptdisk", COLOR_CONFIG)+" is True."))


        x = self.label_flprefix = QLabel()
        y = self.lineEdit_flprefix = QLineEdit()
        # y.editingFinished.connect(self._on_editing_finished)
        y.textEdited.connect(self._on_edited)
        y.installEventFilter(self)
        x.setBuddy(y)
        pp.append((x, y, "flprefi&x", "prefix of filename", COLOR_CONFIG,
         "pfant will create three output files:<ul>"
         "<li>"+_enc_name("flprefix", COLOR_CONFIG)+".cont (continuum),"
         "<li>"+_enc_name("flprefix", COLOR_CONFIG)+".norm (normalized spectrum), and"
         "<li>"+_enc_name("flprefix", COLOR_CONFIG)+".spec (continuum*normalized)</ul>"))



        x = self.label_pas = QLabel()
        y = self.lineEdit_pas = QLineEdit()
        y.installEventFilter(self)
        y.textEdited.connect(self._on_edited)
        y.setValidator(QDoubleValidator(0, 10, 5))
        x.setBuddy(y)
        pp.append((x, y, "&pas", "calculation step (&Aring;)", COLOR_CONFIG,
         "The synthetic spectrum will have points "+_enc_name("pas", COLOR_CONFIG)+" &Aring; distant from "
         "each other.<br><br>Use this to specify the resolution of the synthetic spectrum."))

        # KKK is a repeated description
        KKK = "The calculation interval for the synthetic spectrum is given by "\
              "["+_enc_name("llzero", COLOR_CONFIG)+", "+_enc_name("llfin", COLOR_CONFIG)+"]"
        x = self.label_llzero = QLabel()
        y = self.lineEdit_llzero = QLineEdit()
        y.installEventFilter(self)
        y.textEdited.connect(self._on_edited)
        y.setValidator(QDoubleValidator(0, 10, 5))
        x.setBuddy(y)
        pp.append((x, y, "ll&zero", "calculation beginning (&Aring;)", COLOR_CONFIG, KKK))

        x = self.label_llfin = QLabel()
        y = self.lineEdit_llfin = QLineEdit()
        y.installEventFilter(self)
        y.textEdited.connect(self._on_edited)
        y.setValidator(QDoubleValidator(0, 10, 5))
        x.setBuddy(y)
        pp.append((x, y, "ll&fin", "calculation calculation end (&Aring;)", COLOR_CONFIG, KKK))

        x = self.label_aint = QLabel()
        y = self.lineEdit_aint = QLineEdit()
        y.installEventFilter(self)
        y.textEdited.connect(self._on_edited)
        y.setValidator(QDoubleValidator(0, 10, 5))
        x.setBuddy(y)
        pp.append((x, y, "&aint", "length of sub-interval (&Aring;)", COLOR_CONFIG,
         "This is length of each calculation sub-interval "
         "(the calculation interval ["+_enc_name("llzero", COLOR_CONFIG)+", "+_enc_name("llfin", COLOR_CONFIG)+"] is split in sub-intervals of roughly "+_enc_name("aint", COLOR_CONFIG)+" &Aring;)."
         "<br><br>Note: "+_enc_name("aint", COLOR_CONFIG)+" must be a multiple of "+_enc_name("pas", COLOR_CONFIG)+"."))

        x = self.label_fwhm = QLabel()
        y = self.lineEdit_fwhm = QLineEdit()
        y.installEventFilter(self)
        y.textEdited.connect(self._on_edited)
        y.setValidator(QDoubleValidator(0, 10, 5))
        x.setBuddy(y)
        pp.append((x, y, "&fwhm", "convolution full-width-half-maximum", COLOR_CONFIG,
         "This parameter specifies the full-width-half-maximum "
         "of a Gaussian curve to convolve the synthetic spectrum with. <br><br>It is "
         "used by <em>nulbad</em> (Fortran code that calculates such convolution)."))


        for i, (label, edit, name, short_descr, color, long_descr) in enumerate(pp):
            # label.setStyleSheet("QLabel {text-align: right}")
            assert isinstance(label, QLabel)
            label.setText(_enc_name_descr(name, short_descr, color))
            label.setAlignment(Qt.AlignRight)
            la.addWidget(label, i, 0)
            la.addWidget(edit, i, 1)
            edit.setToolTip(long_descr)

        x = self.textEditDescr = QTextEdit(self)
        x.setEnabled(False)
        # x.setGeometry(0, 0, 100, 0)
        # x.setWordWrap(True)
        x.setStyleSheet("QTextEdit {color: #333333}")
        la.addWidget(x, la.rowCount(), 0, 1, 2)

        self.labelError = QLabel(self)
        self.labelError.setStyleSheet("color: #AA0000")
        la.addWidget(self.labelError, la.rowCount(), 0, 1, 2)

        self.flag_process_changes = True


    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Interface

    def load(self, x):
        assert isinstance(x, FileMain)
        self.f = x
        self._update_from_file_main()
        # this is called to perform file validation upon loading
        self._update_file_main()

    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Qt override

    def setFocus(self, reason=None):
        """Sets focus to first field. Note: reason is ignored."""
        self.lineEdit_titrav.setFocus()

    def eventFilter(self, obj_focused, event):
        if event.type() == QEvent.FocusIn:
            text = ""
            for label, obj, name, short_descr, color, long_descr in self._map:
                if obj_focused == obj:
                    text = "%s<br><br>%s" % \
                           (_enc_name(name.replace("&", ""), color), long_descr)
                    break
            self._set_descr_text(text)
        return False

    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Slots

    def _on_edited(self):
        self._update_file_main()
        self.edited.emit()

    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Internal gear

    def _update_from_file_main(self):
        self.flag_process_changes = False
        try:
            o = self.f
            self.lineEdit_titrav.setText(o.titrav)
            self.lineEdit_teff.setText(str(o.teff))
            self.lineEdit_glog.setText(str(o.glog))
            self.lineEdit_asalog.setText(str(o.asalog))
            self.lineEdit_nhe.setText(str(o.nhe))
            self.checkBox_ptdisk.setChecked(o.ptdisk)
            self.lineEdit_mu.setText(str(o.mu))
            self.lineEdit_flprefix.setText(o.flprefix)
            self.lineEdit_pas.setText(str(o.pas))
            self.lineEdit_llzero.setText(str(o.llzero))
            self.lineEdit_llfin.setText(str(o.llfin))
            self.lineEdit_aint.setText(str(o.aint))
            self.lineEdit_fwhm.setText(str(o.fwhm))
        finally:
            self.flag_process_changes = True

    def _set_error_text(self, x):
        """Sets text of labelError."""
        self.labelError.setText(x)

    def _set_descr_text(self, x):
        """Sets text of labelDescr."""
        self.textEditDescr.setText(x)

    def _update_file_main(self):
        o = self.f
        emsg, flag_error = "", False
        ss = ""
        try:
            ss = "titrav"
            o.titrav = self.lineEdit_titrav.text()
            ss = "teff"
            o.teff = float(self.lineEdit_teff.text())
            ss = "glog"
            o.glog = float(self.lineEdit_glog.text())
            ss = "asalog"
            o.asalog = float(self.lineEdit_asalog.text())
            ss = "nhe"
            o.nhe = float(self.lineEdit_nhe.text())
            ss = "ptdisk"
            o.ptdisk = self.checkBox_ptdisk.isChecked()
            ss = "mu"
            o.mu = float(self.lineEdit_mu.text())
            ss = "flprefix"
            o.flprefix = self.lineEdit_flprefix.text()
            ss = "pas"
            o.pas = float(self.lineEdit_pas.text())
            ss = "llzero"
            o.llzero = float(self.lineEdit_llzero.text())
            ss = "llfin"
            o.llfin = float(self.lineEdit_llfin.text())
            ss = "aint"
            o.aint = float(self.lineEdit_aint.text())
            ss = "fwhm"
            o.fwhm = float(self.lineEdit_fwhm.text())

            # Some error checks
            ss = ""
            if o.llzero >= o.llfin:
                raise RuntimeError("llzero must be lower than llfin!")
            if not (-1 <= o.mu <= 1):
                raise RuntimeError("mu must be between -1 and 1!")
        except Exception as E:
            flag_error = True
            if ss:
                emsg = "Field \"%s\": %s" % (ss, str(E))
            else:
                emsg = str(E)
            emsg = "<b>Invalid</b>: "+emsg
            # ShowError(str(E))
        self.flag_valid = not flag_error
        self._set_error_text(emsg)
