# **************************************************************************
# *
# * Authors:     David Maluenda (dmaluenda@cnb.csic.es)
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************

import os
import subprocess

import sys
import re
import Tkinter as tk
import tkFont
import time
from ConfigParser import SafeConfigParser

from acquisition_workflow import preprocessWorkflow
from constants import *

import pyworkflow as pw
import pyworkflow.utils as pwutils
from pyworkflow.project import Manager, ProjectSettings
from pyworkflow.gui import Message, Icon
import pyworkflow.gui as pwgui
from pyworkflow.gui.project.base import ProjectBaseWindow
from pyworkflow.gui.widgets import HotButton, Button


class BoxWizardWindow(ProjectBaseWindow):
    """ Windows to manage all projects. """

    def __init__(self, config, **kwargs):

        windowTitle = config.get(WINDOWS_TITLE, 'Scipion wizard')
        try:
            title = '%s (%s on %s)' % (windowTitle,
                                       pwutils.getLocalUserName(),
                                       pwutils.getLocalHostName())
        except Exception:
            title = windowTitle

        settings = ProjectSettings()
        self.generalCfg = settings.getConfig()

        self.config = config
        ProjectBaseWindow.__init__(self, title, minsize=(400, 550), **kwargs)
        self.viewFuncs = {VIEW_WIZARD: BoxWizardView}
        self.manager = Manager()
        self.switchView(VIEW_WIZARD)


class BoxWizardView(tk.Frame):
    def __init__(self, parent, windows, **kwargs):
        tk.Frame.__init__(self, parent, bg='white', **kwargs)
        self.windows = windows
        self.manager = windows.manager
        self.root = windows.root
        self.vars = {}
        self.checkvars = []
        self.microscope = None
        self.configDict = self.windows.config
        # Regular expression to validate username and sample name
        self.re = re.compile('\A[a-zA-Z0-9][a-zA-Z0-9_-]+[a-zA-Z0-9]\Z')

        # tkFont.Font(size=12, family='verdana', weight='bold')
        bigSize = pwgui.cfgFontSize + 2
        smallSize = pwgui.cfgFontSize - 2
        fontName = pwgui.cfgFontName

        self.bigFont = tkFont.Font(size=bigSize, family=fontName)
        self.bigFontBold = tkFont.Font(size=bigSize, family=fontName,
                                       weight='bold')

        self.projDateFont = tkFont.Font(size=smallSize, family=fontName)
        self.projDelFont = tkFont.Font(size=smallSize, family=fontName,
                                       weight='bold')
        self.manager = Manager()

        # Header section
        headerFrame = tk.Frame(self, bg='white')
        headerFrame.grid(row=0, column=0, sticky='new')
        headerText = "Create New Session"

        headerText += "  %s" % pwutils.prettyTime(dateFormat='%Y-%m-%d')

        label = tk.Label(headerFrame, text=headerText,
                         font=self.bigFontBold,
                         borderwidth=0, anchor='nw', bg='white',
                         fg=pwgui.Color.DARK_GREY_COLOR)
        label.grid(row=0, column=0, sticky='nw', padx=(20, 5), pady=10)

        # Body section
        bodyFrame = tk.Frame(self, bg='white')
        bodyFrame.grid(row=1, column=0, sticky='news')
        self._fillContent(bodyFrame)

        # Add the create project button
        btnFrame = tk.Frame(self, bg='white')
        btn = HotButton(btnFrame, text="Create New Session",
                        activebackground="dark grey",
                        activeforeground='black',
                        font=self.bigFontBold,
                        command=self._onAction)
        btn.grid(row=0, column=1, sticky='ne', padx=10, pady=10)

        # Add the Cancel project button
        btn = Button(btnFrame, Message.LABEL_BUTTON_CANCEL,
                     Icon.ACTION_CLOSE,
                     font=self.bigFontBold,
                     command=self.windows.close)
        btn.grid(row=0, column=0, sticky='ne', padx=10, pady=10)

        btnFrame.grid(row=2, column=0, sticky='sew')
        btnFrame.columnconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

    def _fillContent(self, frame):

        def _addPair(key, lf, r, entry='text', traceCallback=None, mouseBind=False,
                     color='white', width=8, col=0, t1='', t2='', default=''):
            t = LABELS.get(key, key)

            label = tk.Label(lf, text=t, bg='white', font=self.bigFont)
            sti = 'nw' if col == 1 else 'e'
            label.grid(row=r, column=col, padx=(10, 5), pady=2, sticky=sti)

            if entry == 'text':
                var = tk.StringVar(value=self.getConfValue(key,default))
                entry = tk.Entry(lf, width=width, font=self.bigFont,
                                 textvariable=var, bg=color)
                if traceCallback:
                    if mouseBind:  # call callback on click
                        entry.bind("<Button-1>")
                    else:  # call callback on type
                        var.trace('w', traceCallback)
                self.vars[key] = var
                entry.grid(row=r, column=1, sticky='nw', padx=(5, 10), pady=2)

            elif entry == 'checkbox':
                var = tk.IntVar()

                cb = tk.Checkbutton(lf, font=self.bigFont, bg='white',
                                    variable=var)
                self.vars[key] = var
                self.checkvars.append(key)

                cb.grid(row=r, column=1, padx=5, sticky='nw')

            elif t1 != '':
                label1 = tk.Label(lf, text=t1, bg='white',
                                  font=self.bigFont)
                label1.grid(row=r, column=1, sticky='nw', padx=(5, 10), pady=2)

            if t2 != '':
                label2 = tk.Label(lf, text=t2, bg='white',
                             font=self.bigFont)
                label2.grid(row=r, column=2, sticky='nw', padx=(5, 10), pady=2)
            return r

        def _addCheckPair(key, lf, r, col=1, default=0, bold=False):
            t = LABELS.get(key, key)
            var = tk.BooleanVar(value=self.getConfValue(key, default))
            fnt = self.bigFontBold if bold else self.bigFont
            cb = tk.Checkbutton(lf, text=t, font=fnt, bg='white',
                                variable=var)
            self.vars[key] = var
            self.checkvars.append(key)
            cb.grid(row=r, column=col, padx=5, sticky='nw')

            if bold:
                return r
            else:
                return r, col

        def _addSection(row, text=''):
            lf = tk.LabelFrame(frame, text=text, bg='white',
                               font=self.bigFontBold)
            lf.grid(row=row, column=0, sticky='nw', padx=20, pady=5)
            return lf, row

        ### Acquisition Info ###
        labelFrame, lastSection = _addSection(0, text=' Acquisition Info ')

        lastRow = _addPair(PROJECT_NAME, labelFrame, 0, width=30,
                           default=self._getProjectName(), color='lightgray',
                           traceCallback=self._onInputChange if PROJECT_NAME
                                         not in self.configDict else None)
        if PROJECT_NAME not in self.configDict:
            lastRow = _addPair(USER_NAME, labelFrame, lastRow+1, default='mySelf',
                               width=30, traceCallback=self._onInputChange)
            lastRow = _addPair(SAMPLE_NAME, labelFrame, lastRow+1, default='myProtein',
                               width=30, traceCallback=self._onInputChange)
        if os.environ.get(PATTERN, False):
            lastRow = _addPair(DEPOSITION_PATTERN, labelFrame, lastRow+1,
                               default=self.getConfValue(DEPOSITION_PATTERN),
                               width=30)

        if self.getConfValue(ASK_PATH, True) or self.getConfValue(ASK_ALL, False):
            path2ask = RAWDATA_SIM if self.getConfValue(SIMULATION, False) else DEPOSITION_DIR
            lastRow = _addPair(path2ask, labelFrame, lastRow+1, default='', width=30)

        ### MotionCor2 parameters ###
        labelFrame2, lastSection = _addSection(lastSection+1,
                                               text=' MotionCor2 parameters ')

        lastRow = _addPair(FRAMES, labelFrame2, 0, default='3-0',
                           t2='ex: 2-15 (empty = all frames, 0 = last frame)')
        lastRow = _addPair(DOSE0, labelFrame2, lastRow+1, default='0', t2='e/A^2')
        lastRow = _addPair(DOSEF, labelFrame2, lastRow+1, default='1.18',
                           t2='(if 0, no dose weight is applied)')


        ### Picking parameters ###
        labelFrame3, lastSection = _addSection(lastSection+1,
                                               text=' Picking parameters ')
        lastRow = -1
        if self.getConfValue(ASK_PARTSIZE, True) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair(PARTSIZE, labelFrame3, lastRow+1, default='250',
                               t2='Angstroms (if 0, manual picking is launched)')
        if self.getConfValue(ASK_MICS2PIC, False) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair(MICS2PICK, labelFrame3, lastRow+1, default='10',
                               t2=' (if 0, automatic sample size estimation)')
        if self.getConfValue(ASK_PICK_PROT, False) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair("Protocols:", labelFrame3, lastRow+1, entry="else")
            lastRow, c = _addCheckPair(CRYOLO, labelFrame3, lastRow, default=True)
            lastRow, c = _addCheckPair(RELION_PICK, labelFrame3, lastRow,
                                       default=True, col=c+1)
            # lastRow, c = _addCheckPair(DOGPICK, labelFrame3, lastRow+1,
            #                            default=True)
            # lastRow, c = _addCheckPair(SPARX, labelFrame3, lastRow, col=2,
            #                            default=True)


        ### 2D Classification ###
        labelFrame4, lastSection = _addSection(lastSection+1, text='')
        lastRow = _addCheckPair(DO_2DCLASS, labelFrame4, 0, default=True,
                                bold=True, col=0)

        if self.getConfValue(ASK_2DSAMP, True) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair(SAMPLING_2D, labelFrame4, lastRow+1, default='3',
                               t2='A/pixel (-1 to keep original size)')
        if self.getConfValue(ASK_PARTS2CLASS, True) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair(PARTS2CLASS, labelFrame4, lastRow+1, default='3000')
        if self.getConfValue(ASK_2D_PROT, False) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair("Protocols:", labelFrame4, lastRow+1, entry="else")
            lastRow, c = _addCheckPair(RELION_2D, labelFrame4, lastRow, default=True)
            lastRow, c = _addCheckPair(XMIPP_2D, labelFrame4, lastRow, default=True, col=c+1)
            lastRow, c = _addCheckPair(CRYOS_2D, labelFrame4, lastRow, default=True, col=c+1)


        ### Initial volume estimation ###
        labelFrame5, lastSection = _addSection(lastSection+1, text='')
        lastRow = _addCheckPair(DO_INITVOL, labelFrame5, 0, default=True,
                                bold=True, col=0)

        if self.getConfValue(ASK_SYMGROUP, True) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair(SYMGROUP, labelFrame5, lastRow+1,
                               t2='(if unknown, set at c1)', default='d2')
        if self.getConfValue(ASK_INITVOL_PROT, False) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair("Protocols:", labelFrame5, lastRow+1, entry="else")
            lastRow, c = _addCheckPair(EMAN_INITIAL, labelFrame5, lastRow, default=True)
            lastRow, c = _addCheckPair(SIGNIFICANT, labelFrame5, lastRow, default=True, col=c+1)
            lastRow, c = _addCheckPair(RANSAC, labelFrame5, lastRow, default=False, col=c+1)


        ### 3D Classification
        labelFrame6, lastSection = _addSection(lastSection+1, text='')
        lastRow = _addCheckPair(DO_3DCLASS, labelFrame6, 0, default=True,
                                bold=True, col=0)

        if self.getConfValue(ASK_3DSAMP, True) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair(SAMPLING_3D, labelFrame6, lastRow+1, default='1',
                               t2='A/pixel (-1 to keep original size)')
        if self.getConfValue(ASK_PARTS3D, True) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair(PARTS3D, labelFrame6, lastRow+1, default='10000',
                               t2='(-1 for an automatic value)')
        if self.getConfValue(ASK_3D_PROT, True) or self.getConfValue(ASK_ALL, False):
            lastRow = _addPair("Protocols:", labelFrame6, lastRow+1, entry="else")
            lastRow, c = _addCheckPair(RELION_REFINE, labelFrame6, lastRow, default=True)
            lastRow, c = _addCheckPair(RELION_3DCL, labelFrame6, lastRow, default=True, col=c+1)
            lastRow, c = _addCheckPair(CRYOS_3D, labelFrame6, lastRow+1, default=True)


        ### Extract particles FULL SIZE
        if self.getConfValue(ASK_FULLSIZE, False) or self.getConfValue(ASK_ALL, False):
            labelFrame7, lastSection = _addSection(lastSection+1, text='')
            lastRow = _addCheckPair(DO_FULLSIZE, labelFrame6, 0, default=True,
                                    bold=True, col=0)

        ### RESOURCES
        if self.getConfValue(ASK_RESOURCES, False) or self.getConfValue(ASK_ALL, False):
            labelFrame7, lastSection = _addSection(lastSection+1,
                                                   text=' GPU Resources ')
            lastRow = _addPair("Protocols", labelFrame7, 0, entry="else",
                               t1='GPU id', t2="(-1 to use the alternative below)")
            lastRow = _addPair(MOTIONCOR2_GPU, labelFrame7, lastRow+1,
                               t2="(if not, Xmipp will be used)", default='2-3')
            lastRow = _addPair(GCTF_GPU, labelFrame7, lastRow+1, default='2',
                               t2="(if not, ctfFind4 will be used)")
            lastRow = _addPair(RELION_GPU, labelFrame7, lastRow+1, default='1',
                               t2="(if not, Relion with CPU will be used)")
            lastRow = _addPair(GL2D_GPU, labelFrame7, lastRow+1, default='0',
                               t2="(if not, streaming 2D class in batches)")

        # _addPair(MICS2PICK, 4, labelFrame2, t2='(if 0, only automatic picking is done)')

        #_addPair('Optional protocols:', 5, labelFrame2, entry='empty')


        #labelFrame3 = tk.LabelFrame(frame, text=' GPU usage ', bg='white',
        #                            font=self.bigFontBold)

        #labelFrame3.grid(row=2, column=0, sticky='nw', padx=20, pady=10)
        #labelFrame3.columnconfigure(0, minsize=120)

        #_addPair("Protocols", 0, labelFrame3, entry="else", t1='GPU id', t2="(-1 to use the alternative below)")
        #_addPair(MOTIONCOR2, 1, labelFrame3, t2="(if not, Xmipp will be used)", default='1')
        #_addPair(GCTF, 2, labelFrame3, t2="(if not, ctfFind4 will be used)", default='3')
        #_addPair(CRYOLO, 3, labelFrame3, t2="(if not, there are other pickers)", default='-1')
        #_addPair(RELION, 3, labelFrame3, t2="(if not, Relion with CPU will be used)", default='2')
        #_addPair(GL2D, 4, labelFrame3, t2="(if not, streaming 2D class. is done in batches)", default='0')

        frame.columnconfigure(0, weight=1)

    def _onAction(self, e=None):
        errors = []

        # Check form parameters
        errors = self.checkNames(errors)

        # Loading all vars in the form and check types
        errors = self.castParameters(errors)
        fullProjPath = os.path.join(self.getConfValue(PROJECTS_PATH),
                                    self.getConfValue(PROJECT_NAME))
        if not errors:
            # Check project path only if no problems with project name
            if os.path.exists(fullProjPath):
                errors.append("Project '%s' already exists.\n"
                              "Change User or Sample name" % fullProjPath)

        if not errors:
            # Do more checks only if there are not previous errors
            errors = self.checkWorkflowParams()

        if errors:
            errors.insert(0, "*Errors*:")
            self.windows.showError("\n  - ".join(errors))
        else:
            # self._createDataFolder(dataPath, scipionProjPath)
            # command = os.path.join(os.getenv("SCIPION_HOME"),
            #                        "scripts/mirror_directory.sh")
            # if doBackup:
            #     subprocess.Popen([command, dataFolder, projName, backupFolder],
            #                      stdout=open('logfile_out.log', 'w'),
            #                      stderr=open('logfile_err.log', 'w')
            #                      )
            # print projName, dataPath, scipionProjPath
            try:
                self._createScipionProject()
                close = True
            except Exception as exc:
                errorStr = ("\nSome error occurred while "
                            "creating the project: \n !! %s !!" % exc)
                print(errorStr)
                print(" > Removing that failed project: (rm -rf %s)\n" % fullProjPath)
                # os.system("rm -rf %s" % fullProjPath)
                self.windows.showError(errorStr)
                close = False
                raise
            if close: self.windows.close()

    def _createScipionProject(self):

        dataPath = self.getConfValue(DEPOSITION_PATTERN)
        projectName = self.getConfValue(PROJECT_NAME)
        projectPath = os.path.join(self.getConfValue(PROJECTS_PATH), projectName)

        print("")
        print("Deposition Pattern: %s" % dataPath)
        print("Project Name: %s" % projectName)
        print("Project Path: %s" % projectPath)

        # Launch the simulation
        if self.getConfValue(SIMULATION):
            rawData = self.getConfValue(RAWDATA_SIM)

            gainGlob = os.path.join(rawData, self.getConfValue(GAIN_PAT))
            gainPath = gainGlob[0] if len(gainGlob) > 0 else ''
            rawDataPath = os.path.join(rawData, self.getConfValue(PATTERN))

            subprocess.Popen('%s python %s "%s" %s %d %s &'
                             % (pw.getScipionScript(),
                                'simulate_acquisition.py',
                                rawDataPath, self.getConfValue(DEPOSITION_DIR),
                                self.getConfValue(TIMEOUT),
                                gainPath), shell=True)
            time.sleep(1)

        # Check if there are something to process
        count = 1
        while not len(pwutils.glob(dataPath)):
            if count == 6:
                self.windows.close()

            string = ("No file found in %s.\n"
                      "Make sure that the acquisition has been started.\n\n"
                      % dataPath)
            if count < 5:
                str2 = "Retrying... (%s/5)" % count
            else:
                str2 = "Last try..."
            try:
                self.windows.showInfo(string + str2)
            except:  # When 'Cancel' is press
                sys.exit(0)
            time.sleep(3)
            count += 1

        preprocessWorkflow(self.configDict)

        os.system('touch /tmp/scipion/project_%s' % projectName)
        os.system('touch /tmp/scipion/wait4picking_%s' % projectName)

        # ignoreOption = '' # '--ignore XmippProtParticlePicking'
        # os.system('%s python %s %s %s &' % (pw.getScipionScript(),
        #                                    'schedule_project.py',
        #                                     projName, ignoreOption))

    def getConfValue(self, key, default=None):
        return self.configDict.get(key, default)

    def setConfValue(self, key, value):
        self.configDict.update({key: value})

    def _getValue(self, varKey):
        """ For form callback """
        try:
            value = self.vars[varKey].get()
        except:
            value = None
        return value

    def _setValue(self, varKey, value):
        """ For form callback """
        return self.vars[varKey].set(value)

    def get(self, varKey, default=None):
        return getattr(self, varKey, default)

    def _getProjectName(self):
        usr = self._getUserName()
        sam = self._getSampleName()
        return '%s_%s_%s' % (pwutils.prettyTime(dateFormat='%Y%m%d'), usr, sam)

    def _getSampleName(self):
        try:
            sam = self._getValue(SAMPLE_NAME)
            sam = 'myProtein' if sam is None else sam
        except:
            sam = 'myProtein'
        return sam

    def _getUserName(self):
        try:
            usr = self._getValue(USER_NAME)
            usr = 'mySelf' if usr is None else usr
        except:
            usr = 'mySelf'
        return usr

    def _onInputChange(self, *args):
        self._setValue(PROJECT_NAME, self._getProjectName())

    def checkNames(self, errors):
        dataFolder = self.getConfValue(DEPOSITION_DIR)
        if not os.path.exists(dataFolder):
            errors.append("Data folder '%s' does not exists. "
                          "Check config file." % dataFolder)
        userName = self._getUserName()
        if self.re.match(userName.strip()) is None:
            errors.append("Wrong username")
        sampleName = self._getSampleName()
        if self.re.match(sampleName.strip()) is None:
            errors.append("Wrong sample name")
        return errors

    def checkWorkflowParams(self):
        errors = []

        if not errors:
            self.checkPickingParameters(errors)

        if not errors:
            self.check2DParameters(errors)


        if errors:
            outErr = ['Some incompatible parameters found:']
            return outErr + errors
        else:
            return errors

    def checkPickingParameters(self, errors):
        errors = []
        if (not self.getConfValue(CRYOLO) and
            not self.getConfValue(RELION_PICK) and
            # not self.getConfValue(SPARX) and
            # not self.getConfValue(DOGPICK) and
            self.getConfValue(PARTSIZE) != 0):
            errors.append("At least, one picker is needed. "
                        "Choose crYOLO or Relion LoG, or "
                        "fix the particle size to 0 for a manual picking.")
            return errors

        if (self.getConfValue(PARTSIZE) == 0 and
            self.getConfValue(MICS2PICK) == 0):
            errors.append("If no partivle size is provides, "
                          "a manual picking must be done. "
                          "Thus, please indicate some mics to manula pick "
                          "(MICS2PIC in config file)")
            return errors

        return errors

    def check2DParameters(self, errors):
        pass


    def castParameters(self, errors):
        print("Getting parameters form the form:")
        for var in self.vars:
            try:
                cast = formatsParameters.get(var, 'default')
                value = self._getValue(var)
                if cast == 'default':
                    newvar = value
                elif cast == 'splitInt':
                    if value == '':
                        aux = ['1', '0']
                    elif '-' in value:
                        aux = value.split('-')
                    else:
                        aux = ['0', '0']
                        errors.append("'%s' is not well formated (ie. 2-15)"
                                      % LABELS.get(var))
                    newvar = [int(item) for item in aux]
                else:
                    if value == '':
                        value = 0
                    newvar = cast(value)
                print(" - %s (%s): %s %s" % (var, value, newvar, type(newvar)))
                self.setConfValue(var, newvar)

            except Exception as e:
                if cast == int:
                    errors.append("'%s' should be an integer" % LABELS.get(var))
                elif cast == float:
                    errors.append("'%s' should be a float" % LABELS.get(var))
                else:
                    errors.append("'%s': %s" % (LABELS.get(var), str(e)))

        # Setting some special parameters
        if self.getConfValue(SIMULATION):
            # We classify the acquisitions in projects when simulation
            self.setConfValue(DEPOSITION_DIR,
                              os.path.join(self.getConfValue(DEPOSITION_DIR),
                                           self.getConfValue(PROJECT_NAME)))
        if DEPOSITION_PATTERN not in self.configDict:
            # The pattern can be token from the environ
            pattern = os.path.join(self.getConfValue(DEPOSITION_DIR),
                                   os.environ.get(PATTERN,
                                                  self.getConfValue(PATTERN)))
            self.setConfValue(DEPOSITION_PATTERN, pattern)
        if PROJECTS_PATH not in self.configDict:
            scipionProjPath = os.path.join(os.environ.get('SCIPION_USER_DATA'),
                                           'projects')
            self.setConfValue(PROJECTS_PATH, scipionProjPath)
        print("\n -------------------- \n")
        return errors

def createDictFromConfig(confFile):
    """ Read the configuration from scipion/config/scipionbox.conf.
     A dictionary will be created where each key will be a section starting
     by MICROSCOPE:, all variables that are in the GLOBAL section will be
     inherited by default.
    """
    def fillConfPrint(missing=None):
        print(" > There is some problem reading '%s' config file.\n"
              "Please fill a config file with:\n" % os.path.realpath(confFile))

        print(" - *MANDATORY* parameters: " +
              ', '.join(getConfFileds('mandatory')[0:-1]) +
              ' and ' + getConfFileds('mandatory')[-1] + '\n')

        print(" - Optional parameters: Please see %s\n"
              % os.path.abspath('scipionbox.template'))
        if missing:
            print("\n -> Missing: %s\n" % missing)
        sys.exit(1)

    # confFile = pw.getConfigPath("scipionbox.conf")
    if not os.path.isfile(confFile):
        fillConfPrint()

    # initialization of default parameters
    confDict = {k: d for k, c, d in formatConfParameters if d != 'Mandatory'}

    print("\nReading conf file: %s" % os.path.realpath(confFile))
    # Read from config file.
    cp = SafeConfigParser()
    cp.optionxform = str  # keep case (stackoverflow.com/questions/1611799)
    cp.read(confFile)

    for section in cp.sections():
        print("\n - %s section - " % section)
        for opt in cp.options(section):
            value = cp.get(section, opt)
            # apply a certain casting
            newValue = castConf(opt, value)
            print("     %s (%s): %s %s" % (opt, value, type(newValue), newValue))
            confDict[opt] = newValue
    print('\n -------------------- \n')
    for var in getConfFileds('mandatory'):
        if var not in confDict.keys():
            fillConfPrint(var)

    return confDict

def castConf(var, value):
    """ Casting definitions for config parameters.
    """
    value = pwutils.expandPattern(value)

    castList = [c for k, c, d in formatConfParameters if k == var]
    if castList:
        cast = castList[0]
    else:
        cast = 'default'

    if cast == 'splitTimesFloat':
        if "*" in value:
            newvar = reduce(lambda x, y: float(x) * float(y), value.split('*'))
        elif "/" in value:
            newvar = reduce(lambda x, y: float(x) / float(y), value.split('/'))
        else:
            newvar = float(value)
    elif cast == bool:
        try:
            newvar = int(value) > 0
        except:
            newvar = False if value.lower() == 'false' else True
    elif cast == 'path':
        newvar = pwutils.expandPattern(value)
    elif cast == 'default':
        if value.lower() == 'true':
            newvar = True
        elif value.lower() == 'false':
            newvar = False
        else:
            try:  # to transform to int: '-1'.isdigit() = False...
                newvar = int(value)
            except:
                try:  # to transform to float (1.234, 1.32E-4...)
                    newvar = float(value)
                except ValueError:
                    newvar = value
    else:
        newvar = cast(value)
    return newvar

mandatories = []
optionals = {}
def setConfFileds():
    for var, _, default in formatConfParameters:
        if default == 'Mandatory':
            mandatories.append(var)
        else:
            optionals.update({var: default})

def getConfFileds(type='all'):
    if type == 'mandatory':
        return mandatories
    elif type == 'optionals':
        return optionals
    else:
        return mandatories + optionals


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    setConfFileds()
    if len(sys.argv) < 2:
        confDict = createDictFromConfig('scipionbox.conf')
    else:
        confDict = createDictFromConfig(sys.argv[1])

    wizWindow = BoxWizardWindow(confDict)
    wizWindow.show()

