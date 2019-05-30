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
import tkFileDialog
import tkMessageBox
import ttk
import tkFont
import time
from collections import OrderedDict
from ConfigParser import SafeConfigParser
import argparse

import pyworkflow as pw
import pyworkflow.utils as pwutils
from pyworkflow.gui.dialog import MessageDialog
from pyworkflow.project import Manager, ProjectSettings
from pyworkflow.gui import Message, Icon
import pyworkflow.em as em

import pyworkflow.gui as pwgui
from pyworkflow.gui.project.base import ProjectBaseWindow
from pyworkflow.gui.widgets import HotButton, Button
import subprocess
from pyworkflow.object import Pointer
from pyworkflow.em.protocol import (ProtImportMovies, ProtMonitorSummary,
                                    ProtImportMicrographs, ProtImportAverages,
                                    ProtSubSet, ProtUnionSet, ProtUserSubSet,
                                    ProtExtractCoords, ProtMonitor2dStreamer,
                                    ProtSubSet)

# Plugin imports
ProtMotionCorr = pwutils.importFromPlugin('motioncorr.protocols', 'ProtMotionCorr')

ProtCTFFind = pwutils.importFromPlugin('grigoriefflab.protocols', 'ProtCTFFind')

ProtGctf = pwutils.importFromPlugin('gctf.protocols', 'ProtGctf')

DogPickerProtPicking = pwutils.importFromPlugin('appion.protocols', 'DogPickerProtPicking')

SparxGaussianProtPicking = pwutils.importFromPlugin('eman2.protocols', 'SparxGaussianProtPicking')
EmanProtInitModel = pwutils.importFromPlugin('eman2.protocols', 'EmanProtInitModel')

SphireProtCRYOLO = pwutils.importFromPlugin('sphire.protocols', 'SphireProtCRYOLOPicking')

# ProtRelion2Autopick = pwutils.importFromPlugin('relion.protocols', 'ProtRelion2Autopick')
# ProtRelionExtractParticles = pwutils.importFromPlugin('relion.protocols', 'ProtRelionExtractParticles')
ProtRelionRefine3D = pwutils.importFromPlugin('relion.protocols', 'ProtRelionRefine3D')
ProtRelionClassify2D = pwutils.importFromPlugin('relion.protocols', 'ProtRelionClassify2D')

try:
    from xmipp3.protocols import (XmippProtOFAlignment, XmippProtMovieGain,
                                  XmippProtMovieMaxShift, XmippProtCTFMicrographs,
                                  XmippProtMovieCorr, XmippProtCTFConsensus,
                                  XmippProtPreprocessMicrographs, XmippProtParticleBoxsize,
                                  XmippProtParticlePicking, XmippParticlePickingAutomatic,
                                  XmippProtConsensusPicking, XmippProtCL2D,
                                  XmippProtExtractParticles, XmippProtTriggerData,
                                  XmippProtEliminateEmptyParticles,
                                  XmippProtScreenParticles,
                                  XmippProtReconstructSignificant, XmippProtRansac,
                                  XmippProtAlignVolume, XmippProtReconstructSwarm,
                                  XmippProtStrGpuCrrSimple, XmippProtGpuCrrCL2D,
                                  XmippProtCropResizeVolumes, XmippProtEliminateEmptyClasses)
except Exception as exc:
     pwutils.pluginNotFound('xmipp', errorMsg=exc)


VIEW_WIZARD = 'wizardview'


PROJECT_NAME = "PROJECT_NAME"
FRAMES = "FRAMES"
DOSE0 = 'DOSE0'
DOSEF = 'DOSEF'
MICS2PICK = 'MICS2PICK'
PARTSIZE = 'PARTSIZE'
SYMGROUP = 'SYMGROUP'

# Protocol's contants
GPU_USAGE = 'GPU_USAGE'
MOTIONCOR2 = "MOTIONCOR2"
OPTICAL_FLOW = "OPTICAL_FLOW"
SPARX = "SPARX"
DOGPICK = "DOGPICK"
GCTF = "GCTF"
CRYOLO = 'CRYOLO'
RELION = 'RELION'
GL2D = 'GL2D'
EMAN_INITIAL = 'EMAN_INITIAL'
RANSAC = 'RANSAC'

# Some related environment variables
DATA_FOLDER = 'DATA_FOLDER'
USER_NAME = 'USER_NAME'
SAMPLE_NAME = 'SAMPLE_NAME'

# - conf - #
DEPOSITION_PATH = 'DEPOSITION_PATH'
PATTERN = 'PATTERN'
GAIN_PAT = 'GAIN_PAT'
SCIPION_PROJECT = 'SCIPION_PROJECT'
SIMULATION = 'SIMULATION'
RAWDATA_SIM = 'RAWDATA_SIM'
AMP_CONTR = 'AMP_CONTR'
SPH_AB = 'SPH_AB'
VOL_KV = 'VOL_KV'
SAMPLING = 'SAMPLING'
TIMEOUT = 'TIMEOUT'
INV_CONTR = 'INV_CONTR'
NUM_CPU = 'NUM_CPU'
PARTS2CLASS = 'PARTS2CLASS'
WAIT2PICK = 'WAIT2PICK'


# Define some string constants for the form
LABELS = {
    USER_NAME: "User name",
    SAMPLE_NAME: "Sample name",
    PROJECT_NAME: "Project name",
    FRAMES: "Frames range",
    DOSE0: "Initial dose",
    DOSEF: "Dose per frame",
    MICS2PICK: "Number of mics to manual pick",
    PARTSIZE: "Estimated particle size",
    SYMGROUP: "Estimated symmetry group",

    MOTIONCOR2: "MotionCor2",
    #CRYOLO: "Cryolo",
    RELION: "Relion",
    # OPTICAL_FLOW: "Optical Flow",
    #SPARX: 'Eman2 Sparx',
    #DOGPICK: 'Appion DoG',
    GCTF: "gCtf",
    GL2D: "GL2D",
    EMAN_INITIAL: 'Eman Initial Volume',
    RANSAC: 'Xmipp Ransac'
}

MANDATORY = [PATTERN, AMP_CONTR, SPH_AB, VOL_KV, SAMPLING, INV_CONTR]

defaultVals = {SIMULATION: False,
               RAWDATA_SIM: '',
               GAIN_PAT: '',
               TIMEOUT: 60,
               NUM_CPU: -1,
               PARTS2CLASS: 5000,
               WAIT2PICK: True
               }

# desired casting for the parameters (form and config)
formatConfParameters = {SIMULATION: bool,
                        RAWDATA_SIM: str,
                        PATTERN: str,
                        GAIN_PAT: str,
                        AMP_CONTR: float,
                        SPH_AB: float,
                        VOL_KV: float,
                        SAMPLING: float,
                        TIMEOUT: 'splitTimesFloat',
                        INV_CONTR: bool,
                        NUM_CPU: int,
                        PARTS2CLASS: int,
                        WAIT2PICK: bool}

formatsParameters = {PARTSIZE: int,
                     SYMGROUP: str,
                     FRAMES: 'splitInt',
                     DOSE0: float,
                     DOSEF: float,
                     # OPTICAL_FLOW: bool,
                     # MICS2PICK: int,
                     MOTIONCOR2: int,
                     GCTF: int,
                     #CRYOLO: int,
                     RELION: int,
                     GL2D: int,
                     #SPARX: bool,
                     #DOGPICK: bool,
                     EMAN_INITIAL: bool,
                     RANSAC: bool
                     }

class BoxWizardWindow(ProjectBaseWindow):
    """ Windows to manage all projects. """
    
    def __init__(self, config, **kwargs):
        try:
            title = '%s (%s on %s)' % (Message.LABEL_PROJECTS,
                                       pwutils.getLocalUserName(),
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
                        entry.bind("<Button-1>")#, traceCallback, "eee")
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
        #_addCheckPair(DOGPICK, 5, labelFrame2, default=1)
        #_addCheckPair(SPARX, 5, labelFrame2, col=2, default=1)
        _addCheckPair(RANSAC, 5, labelFrame2, default=0)
        _addCheckPair(EMAN_INITIAL, 5, labelFrame2, default=1, col=2)

        labelFrame3 = tk.LabelFrame(frame, text=' GPU usage ', bg='white',
                                    font=self.bigFontBold)

        labelFrame3.grid(row=2, column=0, sticky='nw', padx=20, pady=10)
        labelFrame3.columnconfigure(0, minsize=120)

        _addPair("Protocols", 0, labelFrame3, entry="else", t1='GPU id', t2="(-1 to use the alternative below)")
        _addPair(MOTIONCOR2, 1, labelFrame3, t2="(if not, Xmipp will be used)", default='1')
        _addPair(GCTF, 2, labelFrame3, t2="(if not, ctfFind4 will be used)", default='3')
        #_addPair(CRYOLO, 3, labelFrame3, t2="(if not, there are other pickers)", default='-1')
        _addPair(RELION, 3, labelFrame3, t2="(if not, Relion with CPU will be used)", default='2')
        _addPair(GL2D, 4, labelFrame3, t2="(if not, streaming 2D class. is done in batches)", default='0')

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
                    newvar = reduce(lambda x, y: float(x)*float(y), value.split('*'))
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
            #if (not self.configDict.get(SPARX, True) and
            #    not self.configDict.get(DOGPICK, True) and
            #        self.configDict.get(PARTSIZE) != 0 and
            #        self.configDict.get(CRYOLO) < 0):
            #    errors.append("At least, one picker is needed. "
            #                  "Choose DoG picker, Sparx, crYOLO or "
            #                  "fix particle size to 0 for manual picking.")

            projName = self._getProjectName()
            dataPath = os.path.join(dataFolder, projName)

            # if not len(pwutils.glob(os.path.join(dataPath,
            #                                     self._getConfValue(PATTERN)))):
            #     errors.append("No file found in %s.\n"
            #                   "Make sure that the acquisition has been started."
            #                   % os.path.join(dataPath, self._getConfValue(PATTERN)))

            scipionProjPath = pwutils.expandPattern(self._getConfValue(SCIPION_PROJECT))
            if not errors:
                if os.path.exists(os.path.join(scipionProjPath, projName)):
                    errors.append("Project path '%s' already exists.\n"
                                  "Change User or Sample name" % projName)


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

            self._createScipionProject(projName, dataPath, scipionProjPath)
            self.windows.close()

    
    def _createScipionProject(self, projName, dataPath, scipionProjPath):

        print("")
        print("Deposition Path: %s" % dataPath)
        print("Project Name: %s" % projName)
        print("Project Path: %s" % scipionProjPath)

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
                            dataPath, self.configDict.get(TIMEOUT),
                            gainPath))

        manager = Manager()
        project = manager.createProject(projName, location=scipionProjPath)

        # smtpServer = self._getConfValue(SMTP_SERVER, '')
        # smtpFrom = self._getConfValue(SMTP_FROM, '')
        # smtpTo = self._getConfValue(SMTP_TO, '')
        # doMail = self._getValue(EMAIL_NOTIFICATION)
        # doPublish = self._getValue(HTML_REPORT)

        count = 1
        while not len(pwutils.glob(os.path.join(dataPath,
                                                self._getConfValue(PATTERN)))):
            if count == 6:
                self.windows.close()

            string = ("No file found in %s.\n"
                      "Make sure that the acquisition has been started.\n\n"
                      % os.path.join(dataPath, self._getConfValue(PATTERN)))
            if count < 5:
                str2 = "Retrying... (%s/5)" % count
            else:
                str2 = "Last try..."

            self.windows.showInfo(string + str2)

            time.sleep(self.configDict.get(TIMEOUT) / 10)
            count += 1

        preprocessWorkflow(project, dataPath, self.configDict)

        ignoreOption = '--ignore XmippProtParticlePicking XmippProtConsensusPicking'
                       # ('' if (self._getConfValue(WAIT2PICK) == 'False' or 
                       #         self._getConfValue(PARTSIZE, 0) == 0) else
                       #  '--ignore XmippProtParticlePicking '
                       #           'XmippParticlePickingAutomatic '
                       #           'XmippProtConsensusPicking ')

        os.system('touch /tmp/scipion/project_%s' % projName)

        os.system('%s python %s %s %s &' % (pw.getScipionScript(),
                                           'schedule_project.py',
                                            projName, ignoreOption))

        #os.system('%s project %s &' % (pw.getScipionScript(), projName))




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



def preprocessWorkflow(project, dataPath, configDict):
    summaryList = []
    summaryExt = []
    numCpus = (configDict.get(NUM_CPU) if configDict.get(NUM_CPU, -1) > 0
                  else int(subprocess.Popen(['nproc','--all'],
                           stdout=subprocess.PIPE).stdout.read()))

    def _registerProt(prot, output=None):
        project.saveProtocol(prot)

        if output is not None:
            summaryList.append(prot)
            summaryExt.append(output)

    def setExtendedInput(protDotInput, lastProt, extended, pointer=False):
        if pointer:

            pointer = Pointer(lastProt, extended=extended)
            protDotInput.setPointer(pointer)
        else:
            if isinstance(lastProt, list):
                for idx, prot in enumerate(lastProt):
                    inputPointer = Pointer(prot, extended=extended[idx])
                    protDotInput.append(inputPointer)
            else:
                protDotInput.set(lastProt)
                protDotInput.setExtended(extended)

    DOWNSAMPLED_SAMPLING = 2.

    # ***********   MOVIES   ***********************************************
    doDose = False if configDict.get(DOSEF, 0) == 0 else True
    gainGlob = pwutils.glob(pwutils.expandPattern(os.path.join(dataPath,
                                        configDict.get(GAIN_PAT, 'noGain'))))
    if len(gainGlob) >= 1:
        gainFn = gainGlob[0]
    else:
        gainFn = ''
        print(" > No gain file found, proceeding without applying it.")
    if len(gainGlob) > 1:
        print(" > More than one gain file found, using only the first.")
    # ----------- IMPORT MOVIES -------------------
    protImport = project.newProtocol(ProtImportMovies,
                              objLabel='import movies',
                              importFrom=ProtImportMovies.IMPORT_FROM_FILES,
                              filesPath=dataPath,
                              filesPattern=configDict.get(PATTERN),
                              amplitudeContrast=configDict.get(AMP_CONTR),
                              sphericalAberration=configDict.get(SPH_AB),
                              voltage=configDict.get(VOL_KV),
                              samplingRate=configDict.get(SAMPLING),
                              doseInitial=configDict.get(DOSE0, 0),
                              dosePerFrame=configDict.get(DOSEF, 0),
                              gainFile=gainFn,
                              dataStreaming=True,
                              timeout=43200)  # configDict.get(TIMEOUT, 43200))  # 12h default
    _registerProt(protImport, 'outputMovies')

    # ----------- MOVIE GAIN --------------------------
    protMG = project.newProtocol(XmippProtMovieGain,
                                 objLabel='Xmipp - movie gain',
                                 frameStep=5,
                                 movieStep=10,
                                 useExistingGainImage=False)
    setExtendedInput(protMG.inputMovies, protImport, 'outputMovies')
    _registerProt(protMG, 'outputImages')

    # ----------- MOTIONCOR ----------------------------
    if configDict.get(MOTIONCOR2, -1) > -1 and ProtMotionCorr is not None:
        protMA = project.newProtocol(ProtMotionCorr,
                                     objLabel='MotionCor2 - movie align.',
                                     gpuList=str(configDict.get(MOTIONCOR2)),
                                     doApplyDoseFilter=doDose,
                                     patchX=7, patchY=7,
                                     alignFrame0=configDict.get(FRAMES, [1,0])[0],
                                     alignFrameN=configDict.get(FRAMES, [1,0])[1])
        setExtendedInput(protMA.inputMovies, protImport, 'outputMovies')
        _registerProt(protMA) #, 'outputMovies')
    else:
        # ----------- CORR ALIGN ----------------------------
        protMA = project.newProtocol(XmippProtMovieCorr,
                                     objLabel='Xmipp - corr. align.',
                                     numberOfThreads=numCpus,
                                     useGpu=False,
                                     doLocalAlignment=False,
                                     alignFrame0=configDict.get(FRAMES, [1,0])[0],
                                     alignFrameN=configDict.get(FRAMES, [1,0])[1])
        setExtendedInput(protMA.inputMovies, protImport, 'outputMovies')
        _registerProt(protMA) #, 'outputMovies')

    # ----------- MAX SHIFT -----------------------------
    protMax = project.newProtocol(XmippProtMovieMaxShift,
                                  objLabel='Xmipp - max shift')
    setExtendedInput(protMax.inputMovies, protMA, 'outputMovies')
    _registerProt(protMax, 'outputMovies')

    # ----------- OF ALIGNMENT --------------------------
    if False and configDict.get(OPTICAL_FLOW, -1):  # Not ready...
        protOF = project.newProtocol(XmippProtOFAlignment,
                                     objLabel='Xmipp - OF align.',
                                     doApplyDoseFilter=doDose,
                                     applyDosePreAlign=False)
        setExtendedInput(protOF.inputMovies, protMax, 'outputMovies')
        _registerProt(protOF)

        alignedMicsLastProt = protOF
    else:
        alignedMicsLastProt = protMax
        
    if doDose:
        alignMicsOutput = 'outputMicrographsDoseWeighted'
    else:
        alignMicsOutput = 'outputMicrographs'


    # *********   CTF ESTIMATION   *****************************************
    # --------- CTF ESTIMATION 2 ---------------------------
    if configDict.get(GCTF, -1) > -1:
        protCTF2 = project.newProtocol(ProtGctf,
                                       objLabel='gCTF estimation',
                                       gpuList=str(configDict.get(GCTF)))
        setExtendedInput(protCTF2.inputMicrographs,
                         alignedMicsLastProt, alignMicsOutput)
        _registerProt(protCTF2)

    else:
        protCTF2 = project.newProtocol(ProtCTFFind,
                                       objLabel='GrigorieffLab - CTFfind',
                                       numberOfThreads=numCpus)
        setExtendedInput(protCTF2.inputMicrographs,
                         alignedMicsLastProt, alignMicsOutput)
        _registerProt(protCTF2)

    # --------- CTF ESTIMATION 1 ---------------------------
    protCTF1 = project.newProtocol(XmippProtCTFMicrographs,
                                   objLabel='Xmipp - ctf estimation')
    setExtendedInput(protCTF1.inputMicrographs,
                     alignedMicsLastProt, alignMicsOutput)
    _registerProt(protCTF1)#, 'outputCTF')


    # --------- CTF CONSENSUS 1 ---------------------------
    protCTFs = project.newProtocol(XmippProtCTFConsensus,
                                   objLabel='Xmipp - CTF consensus',
                                   useDefocus=True,
                                   useAstigmatism=True,
                                   useResolution=True,
                                   resolution=5,
                                   useCritXmipp=True,
                                   calculateConsensus=True,
                                   minConsResol=7)
    setExtendedInput(protCTFs.inputCTF, protCTF2, 'outputCTF')
    setExtendedInput(protCTFs.inputCTF2, protCTF1, 'outputCTF')
    _registerProt(protCTFs, 'outputMicrographs')

    # *************   PICKING   ********************************************
    # Resizing to a sampling rate larger than 3A/px
    downSampPreMics = (float(DOWNSAMPLED_SAMPLING) / configDict.get(SAMPLING) 
                       if configDict.get(SAMPLING) < DOWNSAMPLED_SAMPLING else 1)

    # --------- PREPROCESS MICS ---------------------------
    protPreMics = project.newProtocol(XmippProtPreprocessMicrographs,
                                      objLabel='Xmipp - preprocess Mics',
                                      doRemoveBadPix=True,
                                      doInvert=configDict.get(INV_CONTR),
                                      doDownsample=downSampPreMics>1,
                                      downFactor=downSampPreMics)
    setExtendedInput(protPreMics.inputMicrographs,
                     protCTFs, 'outputMicrographs')
    _registerProt(protPreMics)

    pickers = []
    pickersOuts = []

    if configDict.get(PARTSIZE, 0) == 0:  #configDict.get(MICS2PICK, 0) > 0:
        # -------- TRIGGER MANUAL-PICKER ---------------------------
        # protTRIG0 = project.newProtocol(XmippProtTriggerData,
        #                                 objLabel='Xmipp - trigger some mics',
        #                                 outputSize=configDict.get(MICS2PICK),
        #                                 delay=30,
        #                                 allImages=configDict.get(WAIT2PICK, True))
        # setExtendedInput(protTRIG0.inputImages, protPreMics, 'outputMicrographs')
        # _registerProt(protTRIG0)

        # -------- XMIPP MANUAL-PICKER -------------------------
        protPrePick = project.newProtocol(XmippProtParticlePicking,
                                          objLabel='Xmipp - manual picking',
                                          doInteractive=False)
        setExtendedInput(protPrePick.inputMicrographs,
                         protPreMics, 'outputMicrographs')  # protTRIG0
        _registerProt(protPrePick)
        
        # -------- XMIPP AUTO-PICKING ---------------------------
        protPPauto = project.newProtocol(XmippParticlePickingAutomatic,
                                         objLabel='Xmipp - auto picking',
                                         xmippParticlePicking=protPrePick,
                                         micsToPick=0  # 0=same ; 1=other
                                         )
        # setExtendedInput(protPPauto.inputMicrographs,
        #                  protPreMics, 'outputMicrographs')
        protPPauto.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPPauto)

        pickers.append(protPPauto)
        pickersOuts.append('outputCoordinates')
        bxSize = 64

    else:
        # -------- XMIPP AUTO-BOXSIZE -------------------------
        # protPrePick = project.newProtocol(XmippProtParticleBoxsize,
        #                                   objLabel='Xmipp - particle boxsize')
        # setExtendedInput(protPrePick.inputMicrographs,
        #                  protCTFs, 'outputMicrographs')
        # _registerProt(protPrePick)

        # Fixing an even boxsize big enough: int(x/2+1)*2 = ceil(x/2)*2 = even!
        bxSize = int(configDict.get(PARTSIZE) / configDict.get(SAMPLING)
                     / downSampPreMics / 2 + 1) * 2

    # --------- PARTICLE PICKING 1 ---------------------------
    if configDict.get(CRYOLO, -1) > -1 and SphireProtCRYOLO is not None:
        protPP2 = project.newProtocol(SphireProtCRYOLO,
                                      objLabel='Sphire - CrYolo auto-picking',
                                      boxSize=bxSize,
                                      conservPickVar=0.03,
                                      gpuList=str(configDict.get(CRYOLO)))
        # setExtendedInput(protPP2.boxSize, protPrePick, 'boxsize', True)
        setExtendedInput(protPP2.inputMicrographs, protPreMics, 'outputMicrographs')
        if configDict.get(PARTSIZE, 0) == 0:
            protPP2.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPP2)

        pickers.append(protPP2)
        pickersOuts.append('outputCoordinates')
        
    # --------- PARTICLE PICKING 2 ---------------------------
    if configDict.get(PARTSIZE, 0) != 0 and SparxGaussianProtPicking is not None:  #configDict.get(SPARX, True)
        protPP1 = project.newProtocol(SparxGaussianProtPicking,
                                      objLabel='Eman - Sparx auto-picking',
                                      lowerThreshold=0.02,
                                      boxSize=bxSize)
        # setExtendedInput(protPP1.boxSize, protPrePick, 'boxsize', True)
        setExtendedInput(protPP1.inputMicrographs, protPreMics, 'outputMicrographs')
        if configDict.get(PARTSIZE, 0) == 0:
            protPP1.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPP1)

        pickers.append(protPP1)
        pickersOuts.append('outputCoordinates')
        
       # --------- PARTICLE PICKING 3 ---------------------------
    if configDict.get(DOGPICK, False) and DogPickerProtPicking is not None:
        protPP2 = project.newProtocol(DogPickerProtPicking,
                                      objLabel='Appion - DoG auto-picking',
                                      diameter=bxSize*configDict.get(SAMPLING)) # in A
        # setExtendedInput(protPP1.boxSize, protPrePick, 'boxsize', True)
        setExtendedInput(protPP2.inputMicrographs, protPreMics, 'outputMicrographs')
        if configDict.get(PARTSIZE, 0) == 0:
            protPP2.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPP2)

        pickers.append(protPP2)
        pickersOuts.append('outputCoordinates')     

    # --------- CONSENSUS PICKING -----------------------
    if len(pickers) > 1:
        # --------- CONSENSUS PICKING AND -----------------------
        protCPand = project.newProtocol(XmippProtConsensusPicking,
                                        objLabel='Xmipp - consensus picking (AND)',
                                        consensusRadius=int(bxSize/3),
                                        consensus=-1)
        setExtendedInput(protCPand.inputCoordinates, pickers, pickersOuts)
        _registerProt(protCPand)#, 'consensusCoordinates')

        # --------- CONSENSUS PICKING OR -----------------------
        protCPor = project.newProtocol(XmippProtConsensusPicking,
                                       objLabel='Xmipp - consensus picking (OR)',
                                       consensusRadius=int(bxSize/3),
                                       consensus=1)

        setExtendedInput(protCPor.inputCoordinates, pickers, pickersOuts)
        _registerProt(protCPor)#, 'consensusCoordinates')
        finalPicker = protCPor
        outputCoordsStr = 'consensusCoordinates'

    else:
        finalPicker = pickers[0]
        outputCoordsStr = pickersOuts[0]

    # ---------------------------------- OR/SINGLE PICKING BRANCH ----------

    # --------- EXTRACT PARTICLES OR ----------------------
    ORstr = ' (OR)' if len(pickers) > 1 else ''
    protExtraOR = project.newProtocol(XmippProtExtractParticles,
                                      objLabel='Xmipp - extract particles%s'%ORstr,
                                      boxSize=-1,
                                      downsampleType=0,  # Same as picking
                                      doRemoveDust=True,
                                      doNormalize=True,
                                      doInvert=False,
                                      doFlip=True)
    setExtendedInput(protExtraOR.inputCoordinates,
                     finalPicker, outputCoordsStr)
    setExtendedInput(protExtraOR.ctfRelations, protCTFs, 'outputCTF')
    _registerProt(protExtraOR)#, 'outputParticles')

    # ***********   PROCESS PARTICLES   ************************************
    # --------- ELIM EMPTY PARTS OR ---------------------------
    protEEPor = project.newProtocol(XmippProtEliminateEmptyParticles,
                                    objLabel='Xmipp - Elim. empty part.%s'%ORstr,
                                    inputType=0,
                                    threshold=0.6)
    setExtendedInput(protEEPor.inputParticles, protExtraOR, 'outputParticles')
    _registerProt(protEEPor)#, 'outputParticles')

    # --------- TRIGGER PARTS OR ---------------------------
    protTRIGor = project.newProtocol(XmippProtTriggerData,
                                     objLabel='Xmipp - trigger data to stats%s'%ORstr,
                                     outputSize=1000, delay=30,
                                     allImages=True,
                                     splitImages=False)
    setExtendedInput(protTRIGor.inputImages, protEEPor, 'outputParticles')
    _registerProt(protTRIGor)

    # --------- SCREEN PARTS OR ---------------------------
    protSCRor = project.newProtocol(XmippProtScreenParticles,
                                    objLabel='Xmipp - Screen particles%s'%ORstr)
    protSCRor.autoParRejection.set(XmippProtScreenParticles.REJ_MAXZSCORE)
    protSCRor.autoParRejectionSSNR.set(XmippProtScreenParticles.REJ_PERCENTAGE_SSNR)
    protSCRor.autoParRejectionVar.set(XmippProtScreenParticles.REJ_VARIANCE)
    setExtendedInput(protSCRor.inputParticles, protTRIGor, 'outputParticles')  # protEEPor
    _registerProt(protSCRor)#, 'outputParticles')

    # ----------------------------- END OF OR/SINGLE PICKING BRANCH --------

    # ----------------------------- AND PICKING BRANCH ---------------------
    if len(pickers) < 2:  # if so, Elim. Empty and Screen are the same of above
        protSCR = protSCRor
    else:
        # --------- EXTRACT PARTICLES AND ----------------------
        protExtract = project.newProtocol(XmippProtExtractParticles,
                                          objLabel='Xmipp - extract particles (AND)',
                                          boxSize=-1,
                                          downsampleType=0,  # Same as picking
                                          doRemoveDust=True,
                                          doNormalize=True,
                                          doInvert=False,
                                          doFlip=True)
        setExtendedInput(protExtract.inputCoordinates,
                         protCPand, 'consensusCoordinates')
        setExtendedInput(protExtract.ctfRelations, protCTFs, 'outputCTF')
        _registerProt(protExtract)#, 'outputParticles')

        # --------- ELIM EMPTY PARTS AND ---------------------------
        protEEP = project.newProtocol(XmippProtEliminateEmptyParticles,
                                      objLabel='Xmipp - Elim. empty part. (AND)',
                                      inputType=0,
                                      threshold=0.8)
        setExtendedInput(protEEP.inputParticles, protExtract, 'outputParticles')
        _registerProt(protEEP)#, 'outputParticles')

        # --------- TRIGGER PARTS AND  ---------------------------
        protTRIG = project.newProtocol(XmippProtTriggerData,
                                       objLabel='Xmipp - trigger data to stats (AND)',
                                       outputSize=1000, delay=30,
                                       allImages=True,
                                       splitImages=False)
        setExtendedInput(protTRIG.inputImages, protEEP, 'outputParticles')
        _registerProt(protTRIG)

        # --------- SCREEN PARTS AND  ---------------------------
        protSCR = project.newProtocol(XmippProtScreenParticles,
                                      objLabel='Xmipp - screen particles (AND)')
        protSCR.autoParRejection.set(XmippProtScreenParticles.REJ_MAXZSCORE)
        protSCR.autoParRejectionSSNR.set(XmippProtScreenParticles.REJ_PERCENTAGE_SSNR)
        protSCR.autoParRejectionVar.set(XmippProtScreenParticles.REJ_VARIANCE)
        setExtendedInput(protSCR.inputParticles, protTRIG, 'outputParticles')  # protEEP
        _registerProt(protSCR)#, 'outputParticles')

    # ************   CLASSIFY 2D   *****************************************
    # --------- TRIGGER PARTS ---------------------------
    protTRIG2 = project.newProtocol(XmippProtTriggerData,
                                    objLabel='Xmipp - trigger data to classify',
                                    outputSize=configDict.get(PARTS2CLASS, 5000),
                                    delay=30,
                                    allImages=False)
    setExtendedInput(protTRIG2.inputImages, protSCR, 'outputParticles')
    _registerProt(protTRIG2)

    # --------- XMIPP GL2D/CL2D ---------------------------
    if configDict.get(GL2D) > -1:
        gl2dMpi = numCpus if numCpus<32 else 32
        protCL = project.newProtocol(XmippProtGpuCrrCL2D,
                                     objLabel='Xmipp - Gl2d',
                                     numberOfClasses=16,
                                     numberOfMpi=gl2dMpi)
        setExtendedInput(protCL.inputParticles, protTRIG2, 'outputParticles')
        _registerProt(protCL)
    else:
        protCL = project.newProtocol(XmippProtCL2D,
                                     objLabel='Xmipp - Cl2d',
                                     doCore=False,
                                     numberOfClasses=16,
                                     numberOfMpi=numCpus)
        setExtendedInput(protCL.inputParticles, protTRIG2, 'outputParticles')
        _registerProt(protCL)

    # --------- AUTO CLASS SELECTION I---------------------------
    protCLSEL1 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                     objLabel='Xmipp - Auto class selection I',
                                     threshold=10.0)
    setExtendedInput(protCLSEL1.inputClasses, protCL, 'outputClasses')
    _registerProt(protCLSEL1)#, 'outputAverages')

    # --------- Relion 2D classify ---------------------------
    relionCPUs = numCpus if configDict.get(RELION, -1) < 0 else 3
    protCL2 = project.newProtocol(ProtRelionClassify2D,
                                  objLabel='Relion - 2D classifying',
                                  doGpu=configDict.get(RELION, -1) > -1,
                                  gpusToUse=str(configDict.get(RELION, 0)),
                                  numberOfClasses=16,
                                  numberOfMpi=relionCPUs)
    setExtendedInput(protCL2.inputParticles, protTRIG2, 'outputParticles')
    if configDict.get(RELION, -1) == configDict.get(GL2D, -1):
        protCL2.addPrerequisites(protCL.getObjId())
    _registerProt(protCL2)

    # --------- AUTO CLASS SELECTION II---------------------------
    protCLSEL2 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                     objLabel='Xmipp - Auto class selection II',
                                     threshold=12.0)
    setExtendedInput(protCLSEL2.inputClasses, protCL2, 'outputClasses')
    _registerProt(protCLSEL2)#, 'outputAverages')

    # --------- JOIN SETS ---------------------------
    protJOIN = project.newProtocol(ProtUnionSet, objLabel='Scipion - Join good Averages')
    setExtendedInput(protJOIN.inputSets,
                     [protCLSEL1, protCLSEL2],
                     ['outputAverages', 'outputAverages'])
    _registerProt(protJOIN)

    # ***************   INITIAL VOLUME   ***********************************
    # ------------ RECONSTRUCT SIGNIFICANT ---------------------------
    numCpusSig = numCpus-8
    protSIG = project.newProtocol(XmippProtReconstructSignificant,
                                  objLabel='Xmipp - Recons. significant',
                                  symmetryGroup=configDict.get(SYMGROUP, 'c1'),
                                  numberOfMpi=numCpusSig)
    setExtendedInput(protSIG.inputSet, protJOIN, 'outputSet')
    _registerProt(protSIG)
    initVolDeps = protSIG.getObjId()
    initVols = [protSIG]
    initVolsOuts = ['outputVolume']
    
    # --------- EMAN INIT VOLUME ---------------------------
    if configDict.get(EMAN_INITIAL, True):
        protINITVOL = project.newProtocol(EmanProtInitModel,
                                          objLabel='Eman - Initial vol',
                                          symmetry=configDict.get(SYMGROUP, 'c1'),
                                          numberOfThreads=4)
        setExtendedInput(protINITVOL.inputSet, protJOIN, 'outputSet')
        # protINITVOL.addPrerequisites(initVolDeps)
        _registerProt(protINITVOL)
        initVolDeps = protINITVOL.getObjId()
        initVols += [protINITVOL]
        initVolsOuts += ['outputVolumes']
        
    # --------- RECONSTRUCT RANSAC ---------------------------
    if configDict.get(RANSAC, True):
        protRAN = project.newProtocol(XmippProtRansac,
                                      objLabel='Xmipp - Ransac significant',
                                      symmetryGroup=configDict.get(SYMGROUP, 'c1'),
                                      numberOfThreads=4)
        setExtendedInput(protRAN.inputSet, protJOIN, 'outputSet')
        # protRAN.addPrerequisites(initVolDeps)
        _registerProt(protRAN)
        initVolDeps = protRAN.getObjId()
        initVols += [protRAN]
        initVolsOuts += ['outputVolumes']

    # --------- CREATING AN ALIGNED SET OF VOLUMES -----------
    if len(initVols) > 1:
        protAVOL = project.newProtocol(XmippProtAlignVolume,
                                       objLabel='Xmipp - Join/Align volumes',
                                       alignmentAlgorithm=1,
                                       numberOfThreads=numCpus)
        setExtendedInput(protAVOL.inputReference, protSIG, 'outputVolume')
        setExtendedInput(protAVOL.inputVolumes, initVols, initVolsOuts)
        _registerProt(protAVOL)

        # --------- SWARM CONSENSUS INITIAL VOLUME ---------------
        protSWARM = project.newProtocol(XmippProtReconstructSwarm,
                                        objLabel='Xmipp - Swarm init. vol.',
                                        symmetryGroup=configDict.get(SYMGROUP, 'c1'),
                                        numberOfMpi=numCpus)
        setExtendedInput(protSWARM.inputParticles, protTRIG2, 'outputParticles')
        setExtendedInput(protSWARM.inputVolumes, protAVOL, 'outputVolumes')
        _registerProt(protSWARM)#, 'outputVolume')

    else:  # if no swarm, Significance is the last initVolume
        protSWARM = protSIG

    # ************   FINAL PROTOCOLS   *************************************
    
    # --------- Streaming classification to monitor --------------------
    if configDict.get(GL2D) > -1:
        # --------- GL2D in streaming --------------------
        protCLSEL1p = project.newProtocol(XmippProtEliminateEmptyClasses,
                                          objLabel='From classes to averages I',
                                          threshold=-1,
                                          usePopulation=False)
        setExtendedInput(protCLSEL1p.inputClasses, protCL, 'outputClasses')
        _registerProt(protCLSEL1p)#, 'outputAverages')
    
        protCLSEL2p = project.newProtocol(XmippProtEliminateEmptyClasses,
                                          objLabel='From classes to averages II',
                                          threshold=-1,
                                          usePopulation=False)
        setExtendedInput(protCLSEL2p.inputClasses, protCL2, 'outputClasses')
        _registerProt(protCLSEL2p)#, 'outputAverages')
    
        protJOIN2 = project.newProtocol(ProtUnionSet, objLabel='Scipion - Join all Averages')
        setExtendedInput(protJOIN2.inputSets,
                         [protCLSEL1p, protCLSEL2p],
                         ['outputAverages', 'outputAverages'])
        _registerProt(protJOIN2)
    
        protGL2D = project.newProtocol(XmippProtStrGpuCrrSimple,
                                       objLabel='Xmipp - GL2D assignation',
                                       gpuList=configDict.get(GL2D))
        setExtendedInput(protGL2D.inputRefs, protJOIN2, 'outputSet')
        setExtendedInput(protGL2D.inputParticles, protSCRor, 'outputParticles')
        _registerProt(protGL2D)
    else:
        # --------- ADDING 2D CLASSIFIERS -------------------------
        protStreamer = project.newProtocol(ProtMonitor2dStreamer,
                                           objLabel='Scipion - Streamer',
                                           input2dProtocol=protCL2,
                                           batchSize=2000,
                                           startingNumber=configDict.get(PARTS2CLASS, 5000),
                                           samplingInterval=1)
        setExtendedInput(protStreamer.inputParticles, protSCRor, 'outputParticles')
        # protStreamer.addPrerequisites(protCL2.getObjId())
        _registerProt(protStreamer)

    # # -------------------------- FULL SIZE PROTOCOLS -----
    # --------- RESIZE THE INITIAL VOL TO FULL SIZE ----------
    bxSizeFull = int(configDict.get(PARTSIZE)/configDict.get(SAMPLING)/2+1)*2
    if configDict.get(SAMPLING) < DOWNSAMPLED_SAMPLING:
        protVOLfull = project.newProtocol(XmippProtCropResizeVolumes,
                                          objLabel='Resize volume - FULL FIZE',
                                          doResize=True,
                                          resizeOption=1,  # dimensions
                                          doFourier=True,
                                          resizeDim=bxSizeFull)
        setExtendedInput(protVOLfull.inputVolumes, protSWARM, 'outputVolume')
        _registerProt(protVOLfull)
    
    # # --------- EXTRACT COORD ----------------------------
    #protExtraC = project.newProtocol(ProtExtractCoords,
    #                                 objLabel='Scipion - extrac coord.')
    #setExtendedInput(protExtraC.inputParticles, protSCRor, 'outputParticles')
    #setExtendedInput(protExtraC.inputMicrographs, protPreMics, 'outputMicrographs')
    #_registerProt(protExtraC)
    
    # # --------- EXTRACT FULL SIZE PART ------------------
    # fullBoxSize = int(configDict.get(PARTSIZE) / configDict.get(SAMPLING)) + 1
    protExtraFull = project.newProtocol(XmippProtExtractParticles,
                                        objLabel='Xmipp - extract part. FULL SIZE',
                                        boxSize=bxSizeFull,
                                        downsampleType=1,  # other mics
                                        doRemoveDust=True,
                                        doNormalize=True,
                                        doInvert=configDict.get(INV_CONTR),
                                        doFlip=True)
    setExtendedInput(protExtraFull.inputCoordinates,
                     finalPicker, outputCoordsStr)
                     #protExtraC, 'outputCoordinates')
    setExtendedInput(protExtraFull.inputMicrographs,
                     protCTFs, 'outputMicrographs')
    setExtendedInput(protExtraFull.ctfRelations, protCTFs, 'outputCTF')
    _registerProt(protExtraFull)#, 'outputParticles')
    
    # Subset full size
    protSubsetFullPart = project.newProtocol(ProtSubSet,
                                        objLabel='Scipion - clean particles FULL SIZE')
    setExtendedInput(protSubsetFullPart.inputFullSet,
                     protExtraFull, 'outputParticles')
    setExtendedInput(protSubsetFullPart.inputSubSet,
                     protSCRor, 'outputParticles')
    protSubsetFullPart.addPrerequisites(protVOLfull.getObjId())
    _registerProt(protSubsetFullPart)#, 'outputParticles')
    
    
    # ---------- Refine 3D full sized -----------------------------------
    protRelionRefine = project.newProtocol(ProtRelionRefine3D,
                                           objLabel='Relion - Refine 3D',
                                           initialLowPassFilterA=15,
                                           symmetryGroup=configDict.get(SYMGROUP, 'c1'),
                                           doGpu=configDict.get(RELION, -1) > -1,
                                           gpusToUse=str(configDict.get(RELION, 0))
                                           )
    setExtendedInput(protRelionRefine.inputParticles,
                     protSubsetFullPart, 'outputParticles')
    setExtendedInput(protRelionRefine.referenceVolume,
                     protVOLfull, 'outputVolume')
    _registerProt(protRelionRefine)#, 'outputParticles')

    # --------- SUMMARY MONITOR -----------------------
    protMonitor = project.newProtocol(ProtMonitorSummary,
                                   objLabel='Scipion - Summary Monitor')
    protMonitor.inputProtocols.set(summaryList)
    # setExtendedInput(protMonitor.inputProtocols,
    #                  summaryList, summaryExt)
    _registerProt(protMonitor)


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if len(sys.argv) < 2:
        confDict = createDictFromConfig('scipionbox.conf')
    else:
        confDict = createDictFromConfig(sys.argv[1])
    
    wizWindow = BoxWizardWindow(confDict)
    wizWindow.show()
