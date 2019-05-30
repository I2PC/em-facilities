#!/usr/bin/env python
# **************************************************************************
# *
# * Authors:     Pablo Conesa (pconesa@cnb.csic.es)
# *
# * Unidad de Bioinformatica of Centro Nacional de Biotecnologia, CSIC
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

import sys, os
from pyworkflow.project import Project, Manager
import pyworkflow.utils as pwutils


def usage(error):
    print """
    ERROR: %s

    Usage: scipion python scripts/schedule_project.py projectName 
    
              options: --ignore ProtClassName1 ProtClassName2 ProtClassLabel1 ...

        This script will schedule all the protocols in a linear project, 
          except for those protocols that belongs to ProtClassName1 or ProtClassName2 class,
          even except fot those protocols with a label equal to ProtClassLabel1
    """ % error
    sys.exit(1)


n = len(sys.argv)

if n < 2:
    usage("This script accepts 1 mandatory parameter: the project name.")
elif n > 2 and sys.argv[2] != '--ignore':
    usage("The protocol class names to be ignored must be after a '--ignore' flag.")

projName = sys.argv[1]

path = os.path.join(os.environ['SCIPION_HOME'], 'pyworkflow', 'gui', 'no-tkinter')
sys.path.insert(1, path)

# Create a new project
manager = Manager()

if not manager.hasProject(projName):
    usage("There is no project with this name: %s"
          % pwutils.red(projName))

# the project may be a soft link which may be unavailable to the cluster so get the real path
try:
    projectPath = os.readlink(manager.getProjectPath(projName))
except:
    projectPath = manager.getProjectPath(projName)

project = Project(projectPath)
project.load()

runs = project.getRuns()

# Now assuming that there is no dependencies between runs
# and the graph is lineal
for prot in runs:
    protClassName = prot.getClassName()
    protLabelName = prot.getObjLabel()
    if (protClassName not in sys.argv[3:] and
        protLabelName not in sys.argv[3:]):
        project.scheduleProtocol(prot)
    else:
        print(pwutils.yellowStr("\nNot scheduling '%s' protocol named '%s'.\n"
                                % (protClassName, protLabelName)))
