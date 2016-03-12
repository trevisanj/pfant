"""Widget to edit a Conf object."""

__all__ = ["WOptionsEditor"]

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from .guiaux import *
from pyfant import *
from .a_XText import *

_FROM_MAIN = ' (read from main configuration file)'
_NUM_MOL = 21
_EXE_NAMES = {"i": "innewmarcs", "h": "hydro2", "p": "pfant", "n": "nulbad"}


def _enc_name_descr(name, descr, color="#FFFFFF"):
    # Encodes html given name and description
    return _enc_name(name, color)+"<br>"+descr

def _enc_name(name, color="#FFFFFF"):
    # Encodes html given name and description
    return "<span style=\"color: %s; font-weight: bold\">%s</span>" % \
           (color, name)

@froze_it
class _Option(AttrsPart):
    attrs = ["name", "argname", "descr"]

    def __init__(self):
        AttrsPart.__init__(self)
        self.checkbox = None
        self.label = None
        self.edit = None
        self.name = None
        self.ihpn = None
        self.argname =  None
        self.default =  None
        self.short_descr = None
        self.long_descr = None
        # Whether or not the option overrides a value in main.dat
        self.flag_main = False
        self.color = COLOR_DESCR
        # other widgets to be shown/hidden (besides .checkbox, .label, .edit)
        self.other_widgets = []
        # Type (e.g. float, str). Only required for options whose default is None
        self.type = None

        self.flag_never_used = True

    def __clear_edit(self):
        if isinstance(self.edit, QCheckBox):
            self.edit.setChecked(False)
        else:
            self.edit.setText("")

    def __update_edit(self, value):
        if isinstance(self.edit, QCheckBox):
            self.edit.setChecked(value == True)
        else:
            self.edit.setText(str(value))

    def update_gui(self, options):
        assert isinstance(options, Options)
        attr = options.__getattribute__(self.name)
        flag_check = attr is not None
        self.checkbox.setChecked(flag_check)
        if self.flag_never_used and flag_check:
            self.flag_never_used = False
        if attr is None:
            self.__clear_edit()
        else:
            self.__update_edit(attr)

    def set_gui_default_if_never_used(self):
        """Sets edit/checkbox default if first time the option is set to "in use"."""
        if self.default is not None and self.flag_never_used:
            if isinstance(self.edit, QCheckBox):
                self.edit.setChecked(self.default)
            else:
                self.edit.setText(str(self.default))
        self.flag_never_used = False

    def get_label_text(self):
        return enc_name_descr("--%s" % self.name, self.short_descr, self.color)

class WOptionsEditor(QWidget):
    """
    FileMain editor widget.

    Arguments:
      parent=None
    """

    # Emitted whenever any value changes
    edited = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)


        # # Setup & accessible attributes

        # Whether all the values in the fields are valid or not
        self.flag_valid = True
        self.options = None # Options object
        self.logger = get_python_logger()

        # # Internal stuff that must not be accessed from outside

        # options map: list of _Option
        self.omap = []
        # Internal flag to prevent taking action when some field is updated programatically
        self.flag_process_changes = False

        # # Central layout

        la = self.centralLayout = QVBoxLayout()
        self.setLayout(la)

        # ## Toolbar: checkboxes with executables
        l1 = self.layout_exes = QHBoxLayout()
        la.addLayout(l1)
        w0 = self.checkbox_i = QCheckBox("innewmarcs")
        w1 = self.checkbox_h = QCheckBox("hydro2")
        w2 = self.checkbox_p = QCheckBox("pfant")
        w3 = self.checkbox_n = QCheckBox("nulbad")
        ww = self.checkboxes_exes = [w0, w1, w2, w3]
        l1.addWidget(QLabel("<b>Show options for Fortran binaries:</b>"))
        for w in ww:
            l1.addWidget(w)
            w.setTristate(False)
            w.setChecked(True)
            w.stateChanged.connect(self.on_checkbox_exe_clicked)
        l1.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # ## Toolbar: checkbox for main configuration file override
        l1 = self.layout_main = QHBoxLayout()
        la.addLayout(l1)
        w = self.checkbox_main = QCheckBox("Show main configuration file override options")
        w.setTristate(False)
        w.setChecked(True)
        w.stateChanged.connect(self.on_checkbox_main_clicked)
        w.setToolTip("Show options that, if set, will override values that appear in the main configuration file.")
        l1.addWidget(w)
        l1.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        b = QPushButton("Preview command line")
        b.clicked.connect(self.on_preview)
        l1.addWidget(b)


        # ## Splitter with scroll area and descripton+error area
        sp = self.splitter = QSplitter(Qt.Vertical)
        la.addWidget(sp)

        # ### Scroll area containing the form

        sa = self.scrollArea = QScrollArea()
        sp.addWidget(sa)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sa.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Widget that will be handled by the scrollable area
        w = self.scrollWidget = QWidget()
        sa.setWidget(self.scrollWidget)
        sa.setWidgetResizable(True)
#        la.addWidget(w)

        # #### The form layout
        # This layout contains the form layout and a spacer item
        lw = QVBoxLayout()
        w.setLayout(lw)
        # Form layout
        lo = self.formLayout = QGridLayout()
        lw.addLayout(lo)
        lo.setVerticalSpacing(4)
        lo.setHorizontalSpacing(5)
        lw.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # ##### The editing controls

        self.w_logging_level = QLineEdit()
        self.w_logging_console = QCheckBox()
        self.w_logging_file = QCheckBox()
        self.w_fn_logging = QLineEdit()
        self.w_fn_main = QLineEdit()
        self.w_fn_progress = QLineEdit()
        self.w_explain = QCheckBox()
        self.w_fn_modeles = QLineEdit()
        self.w_teff = QLineEdit()
        self.w_glog = QLineEdit()
        self.w_asalog = QLineEdit()
        self.w_fn_absoru2 = QLineEdit()
        self.w_fn_hmap = QLineEdit()
        self.w_llzero = QLineEdit()
        self.w_llfin = QLineEdit()
        self.w_fn_moddat = QLineEdit()
        self.w_modcode = QLineEdit()
        self.w_tirb = QLineEdit()
        self.w_fn_gridsmap = QLineEdit()
        self.w_ptdisk = QLineEdit()
        self.w_kik = QLineEdit()
        self.w_amores = QCheckBox()
        self.w_kq = QLineEdit()
        self.w_vvt = QLineEdit()
        self.w_zph = QLineEdit()
        self.w_interp = QLineEdit()
        self.w_fn_dissoc = QLineEdit()
        self.w_fn_partit = QLineEdit()
        self.w_fn_abonds = QLineEdit()
        self.w_fn_atoms = QLineEdit()
        self.w_fn_molecules = QLineEdit()
        self.w_molidxs_off = QLineEdit()
        self.w_no_molecules = QCheckBox()
        self.w_no_atoms = QCheckBox()
        self.w_no_h = QCheckBox()
        self.w_zinf = QLineEdit()
        self.w_pas = QLineEdit()
        self.w_aint = QLineEdit()
        self.w_flprefix = QLineEdit()
        self.w_fn_flux = QLineEdit()
        self.w_flam = QCheckBox()
        self.w_fn_cv = QCheckBox()
        self.w_pat = QLineEdit()
        self.w_convol = QCheckBox()
        self.w_fwhm = QLineEdit()

        # ##### The options map
        # (*) A few options have been commented out because they are probably
        # irrelevant nowadays, but may be shown again some time.

        self.__add_option(self.w_logging_level, 'ihpn', 'logging_level', 'debug',
         'logging level',
         'These are the available options:<ul>'+
         '<li>debug'+
         '<li>info'+
         '<li>warning'+
         '<li>error'+
         '<li>critical'+
         '<li>halt</ul>')
        self.__add_option(self.w_logging_console, 'ihpn', 'logging_console', True,
         'Log to console?',
         'Whether or not to log messages to standard output (usually the command console)')
        self.__add_option(self.w_logging_file, 'ihpn', 'logging_file', False,
          'Log to file?',
          'Whether or not to log messages to log file '+
          '(specified by option --fn_logging)')
        # (*) o = self.__add_option(self.w_fn_logging, 'ihpn', 'fn_logging', None,
        # (*)  'log filename',
        # (*)  'default: <executable name>_dump.log, <i>e.g.</i>, <b>pfant_dump.log</b>')
        # (*) o.type = str
        self.__add_option(self.w_fn_main, 'ihpn', 'fn_main', FileMain.default_filename,
         'input file name: main configuration',
         'Contains star parameters and additional software configuration.<br><br>'
         'Here is a list of parameters in this file that also have a command-line option:'
         '<ul><li>llzero<li>llfin<li>pas<li>aint<li>flprefix<li>fwhm</ul>'
         'If specified by command line, any of these options will override'
         'the values in the main configuration file.')
        # (*) self.__add_option(self.w_fn_progress, 'ihpn', 'fn_progress', 'file name', 'progress.txt',
        # (*)  'output file name - progress indicator')
        self.__add_option(self.w_explain, 'ihpn', 'explain', False,
          'Save additional debugging information?',
          'This flag informs the Fortran code to save additional information in file explain.txt '+
          '(debugging purposes; output varies, or flag may be ignored)')

        #
        # innewmarcs, hydro2, pfant
        #
        self.__add_option(self.w_fn_modeles, 'ihp', 'fn_modeles', FileMod.default_filename,
         'atmospheric model file name',
         'This is a binary file containing information about atmospheric model'
         '(created by innewmarcs).')

        #
        # innewmarcs-only
        #

        # (*) self.__add_option(self.w_fn_moddat, 'i', 'fn_moddat', 'file name', 'modeles.dat',
        # (*)  'ASCII file containing information about atmospheric model (created by innewmarcs)')
        # (*) self.__add_option(self.w_modcode, 'i', 'modcode', 'string up to 25 characters', 'NoName',
        # (*)  '"Model name"')
        self.__add_option(self.w_fn_gridsmap, 'i', 'fn_gridsmap', 'gridsmap.dat',
         'input file name -- list of MARCS models file names',
         'This file contains a list of MARCS models file names.')

        #
        # hydro2-only
        #
        self.__add_option(self.w_amores, 'h', 'amores', True,
         'AMOrtissement de RESonnance?', '')
        self.__add_option(self.w_kq, 'h', 'kq', 1,
         'theorie',
         '<ul>'
         '<li>0: THEORIE DE GRIEM;<br>'+
         '<li>1: THEORIE QUASISTATIQUE</li>')

        self.__add_option(self.w_zph, 'h', 'zph', 12,
         'hydrogen-reference-abundance',
         'abondance d''H pour laquelle sont donnees les abondances metalliques')

        #
        # hydro2, pfant
        #
        o = self.__add_option(self.w_llzero, 'hp', 'llzero', 6000,
         "lower boundary of calculation interval (&Aring;)",
         'default: &lt;main_llzero&gt; '+_FROM_MAIN)
        o.flag_main = True
        o.color = COLOR_CONFIG
        o.type = float
        o = self.__add_option(self.w_llfin, 'hp', 'llfin', 6200,
         'upper boundary of calculation interval (&Aring;)',
         'default: &lt;main_llfin&gt; '+_FROM_MAIN)
        o.flag_main = True
        o.color = COLOR_CONFIG
        o.type = float
        self.__add_option(self.w_fn_absoru2, 'hp', 'fn_absoru2', FileAbsoru2.default_filename,
         'input file name - absoru2',
         'This file contains physical data for pfant and hydro2 "absoru" module')
        self.__add_option(self.w_fn_hmap, 'hp', 'fn_hmap', FileHmap.default_filename,
         'input file name - hydrogen lines data',
         'Contains a table with<pre>'+
         'filename, niv inf, niv sup, central lambda, kiex, c1</pre>')
        self.__add_option(self.w_kik, 'hp', 'kik', 0,
         'option affecting the flux integration',
         '<ul>'+
         '<li>0: integration using 6/7 points depending on option --ptdisk;<br>'+
         '<li>1: 26-point integration</ul>')

        #
        # pfant-only
        #
        self.__add_option(self.w_interp, 'p', 'interp', 1,
         'interpolation for subroutine turbul()',
         'interpolation type for subroutine turbul()<ul>'+
         '<li>1: linear;<br>'+
         '<li>2: parabolic</ul>')
        # > @todo Find names for each file and update options help
        self.__add_option(self.w_fn_dissoc, 'p', 'fn_dissoc', FileDissoc.default_filename,
         'input file name - dissociative equilibrium', '')
        self.__add_option(self.w_fn_partit, 'p', 'fn_partit', FilePartit.default_filename,
         'input file name - partition functions', '')
        self.__add_option(self.w_fn_abonds, 'p', 'fn_abonds', FileAbonds.default_filename,
         'input file name - atomic abundances', '')
        self.__add_option(self.w_fn_atoms, 'p', 'fn_atoms', FileAtoms.default_filename,
         'input file name - atomic lines', '')
        self.__add_option(self.w_fn_molecules, 'p', 'fn_molecules', FileMolecules.default_filename,
         'input file name - molecular lines', '')
        self.__add_option(self.w_molidxs_off, 'p', 'molidxs_off', '',
         'moleculed to be "turned off"',
         'comma-separated ids of molecules to be "turned off" (1 to '+str(_NUM_MOL)+').')
        self.__add_option(self.w_no_molecules, 'p', 'no_molecules', False,
         'Skip molecules?',
         'If set, skips the calculation of molecular lines.')
        self.__add_option(self.w_no_atoms, 'p', 'no_atoms', False,
         'Skip atomic lines?',
         'If set, skips the calculation of atomic lines (except hydrogen).')
        self.__add_option(self.w_no_h, 'p', 'no_h', False,
         'Skip hydrogen lines?',
         'If set, skips the calculation of hydrogen lines.')
        self.__add_option(self.w_zinf, 'p', 'zinf', 0.5,
         '(zinf per-line in dfile:atoms)',
         'This is the distance from center of line to consider in atomic line calculation.<br><br>'+
         'If this option is used, will override the zinf defined for each atomic line<br>'+
         '<li>of dfine:atoms and use the value passed')
        o = self.__add_option(self.w_pas, 'p', 'pas', 0.02,
         'calculation delta-lambda (&Aring;)',
         'default: &lt;main_pas&gt; '+_FROM_MAIN)
        o.flag_main = True
        o.color = COLOR_CONFIG
        o = self.__add_option(self.w_aint, 'p', 'aint', 100,
         'interval length per iteration (&Aring;)',
         'default: &lt;main_aint&gt; '+_FROM_MAIN)
        o.flag_main = True
        o.color = COLOR_CONFIG

        #
        # pfant, nulbad
        #
        o = self.__add_option(self.w_flprefix, 'pn', 'flprefix', 'flux',
         'pfant output - prefix for flux output files',
         'Three files will be created based on this prefix:<ul>'+
         '<li><flprefix>.spec: un-normalized spectrum<br>'+
         '<li><flprefix>.cont: continuum<br>'+
         '<li><flprefix>.norm: normalized spectrum</ul><br>'
         'default: &lt;main_flprefix&gt; '+_FROM_MAIN)
        o.flag_main = True
        o.color = COLOR_CONFIG

        #
        # nulbad-only
        #
        self.__add_option(self.w_fn_flux, 'n', 'fn_flux', 'flux.norm',
         'flux file name',
         'default: &lt;main_flprefix>.norm '+_FROM_MAIN)
        o.flag_main = True
        o.color = COLOR_CONFIG
        self.__add_option(self.w_flam, 'n', 'flam', False,
         'Perform Fnu-to-FLambda transformation?',
         'If True, Fnu-to-FLambda transformation is done before the convolution')
        self.__add_option(self.w_fn_cv, 'n', 'fn_cv', True,
          'nulbad output -- convolved spectrum file name',
          'default: &lt;flux file name&gt;.nulbad.&lt;fwhm&gt;')
        self.__add_option(self.w_pat, 'n', 'pat', 0.02,
          'wavelength delta-lambda of nulbad output spectrum (&Aring;)',
          'default: same as delta-lambda of input spectrum')
        self.__add_option(self.w_convol, 'n', 'convol', True,
          'Apply convolution?', '')
        o = self.__add_option(self.w_fwhm, 'n', 'fwhm', 0.12,
          'full-width-half-maximum of Gaussian function',
          'default: &lt;main_fwhm&gt; '+_FROM_MAIN+')')
        o.flag_main = True
        o.color = COLOR_CONFIG

        IHPN = "ihpn"
        NIHPN = len(IHPN)
        for j, letter in enumerate(IHPN):
            lo.addWidget(QLabel("<b>%s</b>" % letter), 0, 3+j, Qt.AlignCenter)
        lo.addWidget(QLabel("<b>in use?</b>"), 0, 2)
        i = 1  # index of next row in layout
        for option in self.omap:
            try:
                for j, letter in enumerate(IHPN):
                    # unicode is for a "v"-like check mark
                    label = QLabel(QString(unichr(10003)) if letter in option.ihpn else "")
                    option.other_widgets.append(label)
                    lo.addWidget(label, i, 3+j)
                label = option.label = \
                    QLabel(option.get_label_text())
                label.setAlignment(Qt.AlignRight)
                checkbox = option.checkbox = QCheckBox()
                checkbox.installEventFilter(self)
                checkbox.stateChanged.connect(self.on_in_use_checkbox_clicked)
                edit = option.edit
                edit.installEventFilter(self)

                lo.addWidget(label, i, 0)
                lo.addWidget(edit, i, 1)
                lo.addWidget(checkbox, i, 2, Qt.AlignCenter)
                i += 1
                option.edit.setToolTip(option.long_descr)
                if isinstance(edit, QCheckBox):
                    edit.stateChanged.connect(self.on_edited)
                else:
                    edit.textEdited.connect(self.on_edited)
            except:
                self.logger.exception("Processing option '%s'" % option.name)
                raise\


        # ### Second widget of splitter
        # layout containing description area and a error label
        wlu = QWidget()
        lu = QVBoxLayout(wlu)
        lu.setMargin(0)
        lu.setSpacing(4)
        x = self.textEditDescr = QTextEdit(self)
        x.setEnabled(False)
        # x.setGeometry(0, 0, 100, 0)
        # x.setWordWrap(True)
        x.setStyleSheet("QTextEdit {color: %s}" % COLOR_DESCR)
        lu.addWidget(x)
        x = self.labelError = QLabel(self)
        x.setStyleSheet("QLabel {color: %s}" % COLOR_ERROR)
        lu.addWidget(self.labelError)
        sp.addWidget(wlu)


        self.setEnabled(False)  # disabled until load() is called
        self.__update_visible_options()
        style_checkboxes(self)
        self.flag_process_changes = True


    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Interface

    def load(self, x):
        assert isinstance(x, Options)
        self.options = x
        self.__update_from_options()
        # this is called to perform file validation upon loading
        self.__update_options()
        self.setEnabled(True)

    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Qt override

    def setFocus(self, reason=None):
        """Sets focus to first field. Note: reason is ignored."""
        self.omap[0].edit.setFocus()

    def eventFilter(self, obj_focused, event):
        if event.type() == QEvent.FocusIn:
            option = self.__find_option_by_widget(obj_focused)
            if option:
                text = "%s<br><br>%s" % \
                       (_enc_name(option.name.replace("&", ""), option.color),
                        option.long_descr)
                self.__set_descr_text(text)

        return False

    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Slots

    def on_edited(self):
        #self._update_file_main()
        option = self.__find_option_by_edit(self.sender())
        self.flag_process_changes = False
        option.checkbox.setChecked(True)
        self.flag_process_changes = True
        option.flag_never_used = False
        self.__update_options()
        self.edited.emit()

    def on_in_use_checkbox_clicked(self):
        if not self.flag_process_changes:
            return
        checkbox = self.sender()
        option = self.__find_option_by_in_use_checkbox(checkbox)
        if checkbox.isChecked():
            option.set_gui_default_if_never_used()

    def on_checkbox_exe_clicked(self):
        self.__update_visible_options()

    def on_checkbox_main_clicked(self):
        self.__update_visible_options()

    def on_preview(self):
        args = self.options.get_args()
        print args
        line = "fortran-binary-xxxx "+(" ".join(args))
        w = XText(self, line, "Command line")
        w.show()



    # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * # * #
    # # Internal gear
    
    def __add_option(self, widget, ihpn, name, default, short_descr, long_descr):
        o = _Option()
        w = o.checkbox = QCheckBox()
        w.setTristate(False)
        w.stateChanged.connect(self.on_in_use_checkbox_clicked)


        o.edit = widget
        o.ihpn = ihpn
        o.name = name
        o.default = default
        o.short_descr = short_descr
        o.long_descr = long_descr
        self.omap.append(o)
        return o

    def __find_option_by_widget(self, widget):
        if isinstance(widget, QCheckBox):
            ret = self.__find_option_by_in_use_checkbox(widget)
            if not ret:
                ret = self.__find_option_by_edit(widget)
        ret = self.__find_option_by_edit(widget)
        return ret

    def __find_option_by_in_use_checkbox(self, checkbox):
        ret = None
        for option in self.omap:
            if option.checkbox == checkbox:
                ret = option
                break
        return ret

    def __find_option_by_edit(self, widget):
        ret = None
        for option in self.omap:
            if option.edit == widget:
                ret = option
                break
        return ret

    def __update_from_options(self):
        self.flag_process_changes = False
        try:
            for option in self.omap:
                option.update_gui(self.options)
        finally:
            self.flag_process_changes = True

    def __update_options(self):
        emsg, flag_error = "", False
        ss = ""
        try:
            for option in self.omap:
                if not option.checkbox.isChecked():
                    continue
                ss = option.name
                type_ = type(option.default) if option.default is not None else option.type
                w = option.edit
                if type_ == bool:
                    value = w.isChecked()
                else:
                    value = type_(w.text())
                self.options.__setattr__(option.name, value)

        except Exception as E:
            flag_error = True
            if ss:
                emsg = "Field \"%s\": %s" % (ss, str(E))
            else:
                emsg = str(E)
            emsg = "<b>Invalid</b>: "+emsg
            # ShowError(str(E))
        self.flag_valid = not flag_error
        self.__set_error_text(emsg)


    def __update_visible_options(self):
        LETTERS = "ihpn"
        ll = []
        for i, (checkbox, letter) in enumerate(zip(self.checkboxes_exes, LETTERS)):
            if checkbox.isChecked():
                ll.append(letter)
        flag_main_goes = self.checkbox_main.isChecked()
        hidden_set_count = 0 # whether there will be set options hidden

        for option in self.omap:
            flag_visible = flag_main_goes or not option.flag_main
            if flag_visible:
                flag_visible = any([letter in option.ihpn for letter in ll])
            option.checkbox.setVisible(flag_visible)
            option.label.setVisible(flag_visible)
            option.edit.setVisible(flag_visible)
            for w in option.other_widgets:
                w.setVisible(flag_visible)
            if not flag_visible and option.checkbox.isChecked():
                hidden_set_count += 1

        if hidden_set_count > 0:
            ShowWarning("Hiding %d option%s in use." %
             (hidden_set_count, "" if hidden_set_count == 1 else "s"))

    def __set_error_text(self, x):
        """Sets text of labelError."""
        self.labelError.setText(x)

    def __set_descr_text(self, x):
        """Sets text of labelDescr."""
        self.textEditDescr.setText(x)




