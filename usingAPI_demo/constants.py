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
    # CRYOLO: "Cryolo",
    RELION: "Relion",
    # OPTICAL_FLOW: "Optical Flow",
    # SPARX: 'Eman2 Sparx',
    # DOGPICK: 'Appion DoG',
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
                     # CRYOLO: int,
                     RELION: int,
                     GL2D: int,
                     # SPARX: bool,
                     # DOGPICK: bool,
                     EMAN_INITIAL: bool,
                     RANSAC: bool
                     }
