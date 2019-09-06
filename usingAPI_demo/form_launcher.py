#!/usr/bin/env python
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
import sys
import re
import Tkinter as tk
import tkFont
import time
from ConfigParser import SafeConfigParser

import pyworkflow as pw
import pyworkflow.utils as pwutils
from pyworkflow.project import Manager, ProjectSettings
from pyworkflow.gui import Message, Icon

import pyworkflow.gui as pwgui
from pyworkflow.gui.project.base import ProjectBaseWindow
from pyworkflow.gui.widgets import HotButton, Button

from acquisition_workflow_basic import preprocessWorkflow
from constants import *


class BoxWizardWindow(ProjectBaseWindow):
    """ Windows to manage all projects. """

    def __init__(self, config, **kwargs):
        try:
            title = 'Acquisition Form (%s on %s)' % (pwutils.getLocalUserName(),
                                                     pwutils.getLocalHostName())
        except Exception:
            title = Message.LABEL_PROJECTS

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
        self.configDict = {}
        # Regular expression to validate username and sample name
        self.re = re.compile('\A[a-zA-Z0-9][a-zA-Z0-9_-]+\Z')

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

        def _addPair(key, r, lf, entry='text', traceCallback=None, mouseBind=False,
                     color='white', width=5, col=0, t1='', t2='', default=''):
            t = LABELS.get(key, key)
            label = tk.Label(lf, text=t, bg='white', font=self.bigFont)
            sti = 'nw' if col == 1 else 'e'
            label.grid(row=r, column=col, padx=(10, 5), pady=2, sticky=sti)

            if entry == 'text':
                var = tk.StringVar(value=default)
                entry = tk.Entry(lf, width=width, font=self.bigFont,
                                 textvariable=var, bg=color)
                if traceCallback:
                    if mouseBind:  # call callback on click
                        entry.bind("<Button-1>")  # , traceCallback, "eee")
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

        def _addCheckPair(key, r, lf, col=1, default=0):
            t = LABELS.get(key, key)
            var = tk.IntVar(value=default)

            cb = tk.Checkbutton(lf, text=t, font=self.bigFont, bg='white',
                                variable=var)
            self.vars[key] = var
            self.checkvars.append(key)
            cb.grid(row=r, column=col, padx=5, sticky='nw')

        labelFrame = tk.LabelFrame(frame, text=' General ', bg='white',
                                   font=self.bigFontBold)
        labelFrame.grid(row=0, column=0, sticky='nw', padx=20)

        _addPair(PROJECT_NAME, 0, labelFrame, width=30, default=self._getProjectName(),
                 color='lightgray', traceCallback=self._onInputChange)
        _addPair(USER_NAME, 1, labelFrame, default='mySelf', width=30, traceCallback=self._onInputChange)
        _addPair(SAMPLE_NAME, 2, labelFrame, default='myProtein', width=30, traceCallback=self._onInputChange)

        labelFrame.columnconfigure(0, weight=1)
        labelFrame.columnconfigure(0, minsize=120)
        labelFrame.columnconfigure(1, weight=1)
        labelFrame.winfo_width()
        labelFrame2 = tk.LabelFrame(frame, text=' Pre-processing ', bg='white',
                                    font=self.bigFontBold)

        labelFrame2.grid(row=1, column=0, sticky='nw', padx=20, pady=10)
        labelFrame2.columnconfigure(0, minsize=120)

        _addPair(SYMGROUP, 0, labelFrame2, t2='(if unknown, set at c1)', default='d2')
        _addPair(FRAMES, 1, labelFrame2, default='3-0', t2='ex: 2-15 (empty = all frames, 0 = last frame)')
        _addPair(DOSE0, 2, labelFrame2, default='0', t2='e/A^2')
        _addPair(DOSEF, 3, labelFrame2, default='0', t2='(if 0, no dose weight is applied)')
        # _addPair(MICS2PICK, 4, labelFrame2, t2='(if 0, only automatic picking is done)')
        _addPair(PARTSIZE, 4, labelFrame2, default='250', t2='Angstroms (if 0, manual picking is launched)')
        _addPair('Optional protocols:', 5, labelFrame2, entry='empty')
        # _addCheckPair(DOGPICK, 5, labelFrame2, default=1)
        # _addCheckPair(SPARX, 5, labelFrame2, col=2, default=1)
        _addCheckPair(RANSAC, 5, labelFrame2, default=0)
        _addCheckPair(EMAN_INITIAL, 5, labelFrame2, default=1, col=2)

        labelFrame3 = tk.LabelFrame(frame, text=' GPU usage ', bg='white',
                                    font=self.bigFontBold)

        labelFrame3.grid(row=2, column=0, sticky='nw', padx=20, pady=10)
        labelFrame3.columnconfigure(0, minsize=120)

        _addPair("Protocols", 0, labelFrame3, entry="else", t1='GPU id', t2="(-1 to use the alternative below)")
        _addPair(MOTIONCOR2, 1, labelFrame3, t2="(if not, Xmipp will be used)", default='-1')
        _addPair(GCTF, 2, labelFrame3, t2="(if not, ctfFind4 will be used)", default='-1')
        # _addPair(CRYOLO, 3, labelFrame3, t2="(if not, there are other pickers)", default='-1')
        _addPair(RELION, 3, labelFrame3, t2="(if not, Relion with CPU will be used)", default='-1')
        _addPair(GL2D, 4, labelFrame3, t2="(if not, streaming 2D class. is done in batches)", default='-1')

        frame.columnconfigure(0, weight=1)

    def _getConfValue(self, key, default=''):
        return self.windows.config.get(key, default)

    def _getValue(self, varKey):
        try:
            value = self.vars[varKey].get()
        except:
            value = None
        return value

    def _setValue(self, varKey, value):
        return self.vars[varKey].set(value)

    def get(self, varKey, default=None):
        return getattr(self, varKey, default)

    def _getProjectName(self):
        try:
            usr = self._getValue(USER_NAME)
            usr = 'mySelf' if usr == None else usr
        except:
            usr = 'mySelf'
        try:
            sam = self._getValue(SAMPLE_NAME)
            sam = 'myProtein' if sam == None else sam
        except:
            sam = 'myProtein'
        return '%s_%s_%s' % (pwutils.prettyTime(dateFormat='%Y%m%d'), usr, sam)

    def _onInputChange(self, *args):
        # Quick and dirty trick to skip this function first time
        # if SAMPLE_NAME not in self.vars:
        #     return
        self._setValue(PROJECT_NAME, self._getProjectName())

    def _createDataFolder(self, projPath, scipionProjPath):
        def _createPath(p):
            # Create the project path
            sys.stdout.write("Creating path '%s' ... " % p)
            pwutils.makePath(p)
            sys.stdout.write("DONE\n")

        # _createPath(projPath)

        # if self._getConfValue(GRIDS) == '1':
        #     for i in range(12):
        #         gridFolder = os.path.join(projPath, 'GRID_%02d' % (i + 1))
        #         _createPath(os.path.join(gridFolder, 'ATLAS'))
        #         _createPath(os.path.join(gridFolder, 'DATA'))

        _createPath(scipionProjPath)

    def castParameters(self, errors):
        for var, cast in formatsParameters.iteritems():
            try:
                value = self._getValue(var)
                if cast == 'splitInt':
                    if value == '':
                        aux = ['1', '0']
                    elif '-' in value:
                        aux = value.split('-')
                    else:
                        aux = ['0', '0']
                        errors.append("'%s' is not well formated (ie. 2-15)"
                                      % LABELS.get(var))
                    newvar = []
                    for item in aux:
                        newvar.append(int(item))
                else:
                    if value == '':
                        value = 0
                    newvar = cast(value)

                self.configDict.update({var: newvar})
            except Exception as e:
                if cast == int:
                    errors.append("'%s' should be an integer" % LABELS.get(var))
                elif cast == float:
                    errors.append("'%s' should be a float" % LABELS.get(var))
                else:
                    errors.append("'%s': %s" % (LABELS.get(var), str(e)))

        return errors

    def castConf(self):
        for var, cast in formatConfParameters.iteritems():
            default = defaultVals.get(var, None)
            value = self._getConfValue(var, default)
            print(" -> %s: %s %s" % (var, type(value), value))
            if cast == 'splitTimesFloat':
                if "*" in value:
                    newvar = reduce(lambda x, y: float(x) * float(y), value.split('*'))
                else:
                    newvar = float(value)
            elif cast == bool:
                newvar = True if value.lower() == 'True'.lower() else False
            else:
                newvar = cast(value)

            self.configDict.update({var: newvar})

    def _onAction(self, e=None):

        errors = []

        # Check form parameters
        dataFolder = pwutils.expandPattern(self._getConfValue(DEPOSITION_PATH))
        if not os.path.exists(dataFolder):
            os.makedirs(dataFolder)
            # errors.append("Data folder '%s' does not exists. \n"
            #               "Check config file" % dataFolder)

        userName = self._getValue(USER_NAME)
        if self.re.match(userName.strip()) is None:
            errors.append("Wrong username")

        sampleName = self._getValue(SAMPLE_NAME)
        if self.re.match(sampleName.strip()) is None:
            errors.append("Wrong sample name")

        errors = self.castParameters(errors)

        # Do more checks only if there are not previous errors
        if not errors:
            # if (not self.configDict.get(SPARX, True) and
            #    not self.configDict.get(DOGPICK, True) and
            #        self.configDict.get(PARTSIZE) != 0 and
            #        self.configDict.get(CRYOLO) < 0):
            #    errors.append("At least, one picker is needed. "
            #                  "Choose DoG picker, Sparx, crYOLO or "
            #                  "fix particle size to 0 for manual picking.")

            self.configDict[PROJECT_NAME] = self._getProjectName()
            self.configDict[DATA_FOLDER] = os.path.join(dataFolder, self.configDict[PROJECT_NAME])

            # if not len(pwutils.glob(os.path.join(self.configDict[DATA_FOLDER],
            #                                      self._getConfValue(PATTERN)))):
            #     errors.append("No file found in %s.\n"
            #                   "Make sure that the acquisition has been started."
            #                   % os.path.join(self.configDict[DATA_FOLDER],
            #                                  self._getConfValue(PATTERN)))

            scipionProjPath = pwutils.expandPattern(self._getConfValue(SCIPION_PROJECT))
            self.configDict[SCIPION_PROJECT] = scipionProjPath
            if not errors:
                if os.path.exists(os.path.join(scipionProjPath,
                                               self.configDict[PROJECT_NAME])):
                    errors.append("Project path '%s' already exists.\n"
                                  "Change User or Sample name"
                                  % self.configDict[PROJECT_NAME])

        if errors:
            errors.insert(0, "*Errors*:")
            self.windows.showError("\n  - ".join(errors))
        else:
            self._createScipionProject()
            self.windows.close()

    def _createScipionProject(self):

        print('')
        print("Deposition Path: %s" % self.configDict[DATA_FOLDER])
        print("Project Name: %s" % self.configDict[PROJECT_NAME])
        print("Project Path: %s" % self.configDict[SCIPION_PROJECT])

        self.castConf()

        if self.configDict.get(SIMULATION):
            rawData = os.path.join(pwutils.expanduser(
                self._getConfValue(RAWDATA_SIM)))

            gainGlob = pwutils.glob(os.path.join(rawData,
                                                 self._getConfValue(GAIN_PAT)))
            gainPath = gainGlob[0] if len(gainGlob) > 0 else ''

            os.system('%s python %s "%s" %s %d %s &' % (pw.getScipionScript(),
                                                        'simulate_acquisition.py',
                                                        os.path.join(rawData, self._getConfValue(PATTERN)),
                                                        self.configDict[DATA_FOLDER],
                                                        self.configDict.get(TIMEOUT),
                                                        gainPath))
            time.sleep(0.5)  # wait a second to ensure that simulation is started

        count = 1
        while not len(pwutils.glob(os.path.join(self.configDict[DATA_FOLDER],
                                                self._getConfValue(PATTERN)))):
            if count == 6:
                self.windows.close()

            string = ("No file found in %s.\n"
                      "Make sure that the acquisition has been started.\n\n"
                      % os.path.join(self.configDict[DATA_FOLDER],
                                     self._getConfValue(PATTERN)))
            if count < 5:
                str2 = "Retrying... (%s/5)" % count
            else:
                str2 = "Last try..."

            self.windows.showInfo(string + str2)

            time.sleep(self.configDict.get(TIMEOUT) / 10)
            count += 1

        preprocessWorkflow(self.configDict)

        ignoreOption = '--ignore XmippProtParticlePicking ' \
                       'XmippProtConsensusPicking ' \
                       'XmippParticlePickingAutomatic ' \
                       'ProtUnionSet ' \
                       'XmippProtExtractParticles '

        # ('' if (self._getConfValue(WAIT2PICK) == 'False' or
        #         self._getConfValue(PARTSIZE, 0) == 0) else
        #  '--ignore XmippProtParticlePicking '
        #           'XmippParticlePickingAutomatic '
        #           'XmippProtConsensusPicking ')

        os.system('touch /tmp/scipion/project_%s'
                  % self.configDict[PROJECT_NAME])

        # os.system('%s python %s %s %s &' % (pw.getScipionScript(),
        #                                     'schedule_project.py',
        #                                     self.configDict[PROJECT_NAME],
        #                                     ignoreOption))

        os.system('%s project %s &' % (pw.getScipionScript(),
                                       self.configDict[PROJECT_NAME]))


def createDictFromConfig(confFile):
    """ Read the configuration from scipion/config/scipionbox.conf.
     A dictionary will be created where each key will be a section starting
     by MICROSCOPE:, all variables that are in the GLOBAL section will be
     inherited by default.
    """

    def fillConfPrint():
        errorStr = (" > There is some problem reading '%s' config file. "
                    "Please fill a config file with, at least, with"
                    "the following parameters: \n%s\n"
                    % (confFile,
                       ', '.join(MANDATORY[0:-1]) + ' and ' + MANDATORY[-1]))
        errorStr += (" - Optional parameters: \n%s"
                     % ', '.join(defaultVals.keys()[0:-1]) + ' and ' +
                     defaultVals.keys()[-1])
        print(errorStr)
        sys.exit(1)

    # confFile = pw.getConfigPath("scipionbox.conf")
    if not os.path.isfile(confFile):
        fillConfPrint()

    print("Reading conf file: %s" % confFile)
    # Read from config file.
    confDict = {}
    cp = SafeConfigParser()
    cp.optionxform = str  # keep case (stackoverflow.com/questions/1611799)
    cp.read(confFile)

    for section in cp.sections():
        print("\n - %s section - " % section)
        for opt in cp.options(section):
            confDict[opt] = cp.get(section, opt)
            print("    %s: %s" % (opt, confDict[opt]))
    print('')
    for field in MANDATORY:
        if field not in confDict.keys():
            fillConfPrint()

    return confDict


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) < 2:
        confDict = createDictFromConfig('scipionbox.conf')
    else:
        confDict = createDictFromConfig(sys.argv[1])

    wizWindow = BoxWizardWindow(confDict)
    wizWindow.show()
