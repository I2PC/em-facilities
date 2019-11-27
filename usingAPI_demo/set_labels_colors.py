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
"""
Launch main project window
"""
import pickle

import sys
import os

from pyworkflow.project import Manager, Label
from pyworkflow.gui.project import ProjectWindow


if __name__ == '__main__':

    manager = Manager()
    projName = os.path.basename(sys.argv[1])
    projPath = manager.getProjectPath(projName)

    projWindow = ProjectWindow(projPath)

    proj = projWindow.project
    sett = proj.getSettings()
    sett.setColorMode(sett.COLOR_MODE_LABELS)

    with open(proj.getPath('labels.pkl'), 'r') as f:
        labelsDict, colorsDict = pickle.load(f)

    for labelName, prots in labelsDict.iteritems():
        label = Label(name=labelName, color=colorsDict[labelName])
        sett.getLabels().addLabel(label)
        for protId in prots:
            node = sett.getNodeById(protId)
            node.setLabels([labelName])

    proj.saveSettings()

