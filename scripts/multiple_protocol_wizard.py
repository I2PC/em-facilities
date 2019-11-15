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
import glob

from motioncorr.protocols import ProtMotionCorr
from pyworkflow import getScipionScript
from pyworkflow.em import ProtImportMovies, time
from xmipp3.protocols import XmippProtMovieGain


def usage(message=''):
    print("\nConvert all PDBs found in PATTERN to density maps using Scipion"
          "\n\n   -> scipion python convert_pdbs.py [opt1=val1 opt2=val2 ...] "
          "\n\n         options:  default"
            "\n         pattern:  /current/directory/*.pdb"
            "\n         project:  convertManyPDBs"
            "\n         sampling: 1.0  (A/px)"
            "\n         window:   -1  (px) (auto default)")
    message = "\n\n  >>  %s\n" % message if message != '' else ''
    print(message)
    sys.exit(1)


# Importing Scipion and Xmipp modules
try:  # if python not from Scipion used, it could fail
    import pyworkflow.utils as pwutils
    from pyworkflow.project import Manager
    from pyworkflow.gui.project import ProjectWindow

    XmippProtConvertPdb = pwutils.importFromPlugin('xmipp3.protocols',
                                                    'XmippProtConvertPdb',
                                                    doRaise=True)
except Exception as e:
    usage(" Some error ocurred while importing from Scipion or Xmipp\n"
          "%s" % e)

def getArg(arg, argName, dictKey, cast=None):
    argPars = argName + '='
    if arg.startswith(argPars):
        value = arg.split(argPars)[1]
        if cast is not None:
            try:
                confDict.update({dictKey: cast(value)})
            except ValueError:
                usage(" %s must be a %s." % (argName, cast))
        elif cast == bool:
            confDict.update({dictKey: value.lower() not in
                                      ['false', 'no', '0', '-1']})
        else:
            confDict.update({dictKey: value})


# Manager will halp as to find paths, create project...
manager = Manager()

# Fixing some parameters depending on the arguments or taking the default ones
PROJECT_PREFIX = 'convertManyPDBs'

confDict = {
    'PROJECT_NAME': PROJECT_PREFIX,
    'SAMPLING_RATE': 1,
    'WINDOW_SIZE': -1,
    'PATTERN': os.path.join(os.getcwd(), '*.pdb'),
    'PATH': os.getcwd(),
    'GAINS': os.path.join(os.getcwd(), 'gain.mrc'),
    'STREAMING': False
}

for arg in sys.argv:
    getArg(arg, 'path', 'PATH')
    getArg(arg, 'gains', 'GAINS')
    getArg(arg, 'pattern', 'PATTERN')
    getArg(arg, 'project', 'PROJECT_NAME')
    getArg(arg, 'sampling', 'SAMPLING_RATE', float)
    getArg(arg, 'window', 'WINDOW_SIZE', int)
    getArg(arg, 'streaming', 'STREAMING', bool)


# Ensuring that the project is not already existing
if os.path.isdir(manager.getProjectPath(confDict['PROJECT_NAME'])):
    correlativeNumber = 1
    PROJECT_PREFIX = confDict['PROJECT_NAME']
    while os.path.isdir(manager.getProjectPath(confDict['PROJECT_NAME'])):
        # to ensure a new project
        confDict['PROJECT_NAME'] = "%s_%d" % (PROJECT_PREFIX, correlativeNumber)
        correlativeNumber += 1

# Creating the project
project = manager.createProject(confDict['PROJECT_NAME'])

# launch project GUI
if confDict['STREAMING']:
    imports = os.path.join(os.environ['SCIPION_USER_DATA'], 'projects',
                           confDict['PROJECT_NAME'], project.getTmpPath('imports'))
    pwutils.makePath(imports)
    subprocess.Popen([getScipionScript(), 'python', '/home/david/em-facilities/usingAPI_demo/simulate_acquisition.py',
                      os.path.join(confDict['PATH'], confDict['PATTERN']),
                      imports, '60'])
    time.sleep(10)
    print('ln -s %s %s' % (os.path.join(confDict['PATH'], confDict['GAINS']), imports+'/'))
    os.system('ln -s %s %s' % (os.path.join(confDict['PATH'], confDict['GAINS']),
                               imports+'/'))
    confDict['PATH'] = imports

lastDep = -1
# Creating as many XmippProtConvertPrb as files found in PATTERN
for file in glob.glob(os.path.join(confDict['PATH'], confDict['GAINS'])):

    print(" -> file: %s" % file)

    protImport = project.newProtocol(ProtImportMovies,
                              objLabel='import movies',
                              importFrom=ProtImportMovies.IMPORT_FROM_FILES,
                              filesPath=confDict['PATH'],
                              filesPattern=confDict['PATTERN'],
                              amplitudeContrast=0.1,
                              sphericalAberration=2.7,
                              voltage=300,
                              samplingRate=confDict['SAMPLING_RATE'],
                              doseInitial=0,
                              dosePerFrame=0,
                              gainFile=file,
                              dataStreaming=True)
    # Register the protocol
    project.saveProtocol(protImport)

    protGain = project.newProtocol(XmippProtMovieGain,
                                 objLabel='Xmipp - movie gain',
                                 frameStep=6,
                                 movieStep=10)
    protGain.inputMovies.set(protImport)
    protGain.inputMovies.setExtended('outputMovies')
    project.saveProtocol(protGain)

    protMA = project.newProtocol(ProtMotionCorr,
                                 objLabel='MotionCor2 - movie align.',
                                 gpuList='0',
                                 doApplyDoseFilter=False,
                                 patchX=5, patchY=5,
                                 extraParams2='-SumRange 0 0',  # To avoid DWS files
                                 )
    protMA.inputMovies.set(protGain)
    protMA.inputMovies.setExtended('outputMovies')

    if lastDep > 0: protMA.addPrerequisites(lastDep)
    project.saveProtocol(protMA)
    lastDep = protMA.getObjId()


# launch project GUI
subprocess.Popen([getScipionScript(), 'project', confDict['PROJECT_NAME']])

# launch all protocols
project.load()
for prot in project.getRuns():
    project.launchProtocol(prot)

protImport = project.newProtocol(ProtImportMovies,
                          objLabel='import movies',
                          importFrom=ProtImportMovies.IMPORT_FROM_FILES,
                          filesPath=confDict['PATH'])

print("  >>>>>>>>>       %s" % protImport)
pwutils.moveFile()