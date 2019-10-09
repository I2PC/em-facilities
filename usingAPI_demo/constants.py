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

#   ---   CONSTANTS   ---   #
WINDOWS_TITLE = 'WINDOWS_TITLE'
VIEW_WIZARD = 'wizardview'
PROJECT_PATH = 'PROJECT_PATH'

# - conf - #
DEPOSITION_PATTERN = 'DEPOSITION_PATTERN'
DEPOSITION_DIR = 'DEPOSITION_DIR'
PATTERN = 'SCIPION_ACQUISITION_PATTERN'
GAIN_PAT = 'GAIN_PAT'
SIMULATION = 'SIMULATION'
RAWDATA_SIM = 'RAWDATA_SIM'
AMP_CONTR = 'AMP_CONTR'
SPH_AB = 'SPH_AB'
VOL_KV = 'VOL_KV'
SAMPLING = 'SAMPLING'
TIMEOUT = 'TIMEOUT'
INV_CONTR = 'INV_CONTR'
NUM_CPU = 'NUM_CPU'

# Form fields
PROJECT_NAME = "PROJECT_NAME"
ASK_ALL = 'ASK_ALL'

MOTIONCOR2_GPU = "MOTIONCOR2_GPU"
FRAMES = "FRAMES"
DOSE0 = 'DOSE0'
DOSEF = 'DOSEF'
OPTICAL_FLOW = "OPTICAL_FLOW"

GCTF_GPU = "GCTF_GPU"

ASK_PARTSIZE = 'ASK_PARTSIZE'
ASK_MICS2PIC = 'ASK_MICS2PIC'
ASK_PICK_PROT = 'ASK_PICK_PROT'
PARTSIZE = 'PARTSIZE'
MICS2PICK = 'MICS2PICK'
CRYOLO = 'CRYOLO'
RELION_PICK = 'RELION_PICK'
SPARX = "SPARX"
DOGPICK = "DOGPICK"
WAIT2PICK = 'WAIT2PICK'

DO_2DCLASS = 'DO_2DCLASS'
ASK_2DSAMP = 'ASK_2DSAMP'
SAMPLING_2D = 'SAMPLING_2D'
ASK_PARTS2CLASS = 'ASK_PARTS2CLASS'
PARTS2CLASS = 'PARTS2CLASS'
ASK_2D_PROT = 'ASK_2D_PROT'
RELION_2D = 'RELION_2D'
RELION_GPU = 'RELION_GPU'
XMIPP_2D = 'XMIPP_2D'
GL2D_GPU = 'GL2D_GPU'
CRYOS_2D = 'CRYOS_2D'
USE_CRYOS_SSD = 'USE_CRYOS_SSD'

DO_INITVOL = 'DO_INITVOL'
ASK_SYMGROUP = 'ASK_SYMGROUP'
SYMGROUP = 'SYMGROUP'
ASK_INITVOL_PROT = 'ASK_INITVOL_PROT'
EMAN_INITIAL = 'EMAN_INITIAL'
SIGNIFICANT = 'SIGNIFICANT'
RANSAC = 'RANSAC'

DO_3DCLASS = 'DO_3DCLASS'
ASK_3DSAMP = 'ASK_3DSAMP'
SAMPLING_3D = 'SAMPLING_3D'
ASK_PARTS3D = 'ASK_PARTS3D'
PARTS3D = 'PARTS3D'
ASK_3D_PROT = 'ASK_3D_PROT'
CRYOS_3D = 'CRYOS_3D'
RELION_REFINE = 'RELION_REFINE'
RELION_3DCL = 'RELION_3DCL'

DO_FULLSIZE = 'DO_FULLSIZE'
ASK_FULLSIZE = 'ASK_FULLSIZE'

ASK_RESOURCES = 'ASK_RESOURCES'

# Some related environment variables
DATA_FOLDER = 'DATA_FOLDER'
USER_NAME = 'USER_NAME'
SAMPLE_NAME = 'SAMPLE_NAME'


#   ---   FORM FIELDS   ----

# Define a label for the form
LABELS = {
    USER_NAME: "User name",
    SAMPLE_NAME: "Sample name",
    PROJECT_NAME: "Project name",
    DEPOSITION_PATTERN: "Acquisition pattern",
    FRAMES: "Frames range",
    DOSE0: "Initial dose",
    DOSEF: "Dose per frame",
    MICS2PICK: "Number of mics to manual pick",
    PARTSIZE: "Estimated particle size",
    SYMGROUP: "Estimated symmetry group",

    MOTIONCOR2_GPU: "MotionCor2",
    CRYOLO: "Cryolo",
    OPTICAL_FLOW: "Optical Flow",
    SPARX: 'Eman2 Sparx',
    DOGPICK: 'Appion DoG',
    EMAN_INITIAL: 'Eman',
    RANSAC: 'Xmipp Ransac',
    CRYOS_2D: 'cryosparc2',
    CRYOS_3D: 'cryosparc2',
    RELION_2D: 'Relion 2D',
    RELION_REFINE: 'Relion auto-refine',
    RELION_3DCL: 'Relion 3D classification',
    RELION_PICK: 'Relion LoG',
    XMIPP_2D: 'Xmipp CL2D/GL2D',
    SIGNIFICANT: 'Xmipp Significant',
    SAMPLING_2D: '2D analysis pixel size',
    SAMPLING_3D: '3D analysis pixel size',
    DO_2DCLASS: 'Do 2D analysis',
    DO_INITVOL: 'Estimate an Initial Volume',
    DO_3DCLASS: 'Do 3D analysis',
    DO_FULLSIZE: 'Extract particles at FULL resolution',
    PARTS2CLASS: '# particles to classify',
    PARTS3D: '# particles for 3D analysis',
}

# Make a specific casting to FORM parameters (if not, using the default type)
formatsParameters = {PARTSIZE: int,
                     SYMGROUP: str,
                     FRAMES: 'splitInt',
                     DOSE0: float,
                     DOSEF: float,
                     OPTICAL_FLOW: bool,
                     SPARX: bool,
                     DOGPICK: bool,
                     EMAN_INITIAL: bool,
                     RANSAC: bool,
                     SAMPLING: float,
                     SAMPLING_2D: float,
                     SAMPLING_3D: float,
                     PARTS3D: int,
                     }


#   ---   CONFIG FILEDS   ---
# Default values
defaultVals = {SIMULATION: False,
               RAWDATA_SIM: '',
               GAIN_PAT: '',
               TIMEOUT: 60,
               NUM_CPU: -1,
               PARTS2CLASS: 5000,
               WAIT2PICK: True,
               }

# Default values of certain config parameters and its casting,
#  see special casting below. Put 'Mandatory' to assert if present
formatConfParameters = [(SIMULATION, bool, False),
                        (DEPOSITION_DIR, 'path', ''),
                        (RAWDATA_SIM, 'path', ''),
                        (PATTERN, str, 'Mandatory'),
                        (GAIN_PAT, str, ''),
                        (AMP_CONTR, float, 0.1),
                        (SPH_AB, float, 'Mandatory'),
                        (VOL_KV, float, 'Mandatory'),
                        (SAMPLING, float, 'Mandatory'),
                        (TIMEOUT, 'splitTimesFloat', 60),
                        (INV_CONTR, bool, 'Mandatory'),
                        (NUM_CPU, int, -1),
                        (MICS2PICK, int, 10),
                        (MOTIONCOR2_GPU, str, '2,3'),
                        (GCTF_GPU, str, '2'),
                        (CRYOLO, bool, True),
                        (RELION_GPU, str, '1'),
                        (GL2D_GPU, str, '0'),
                        (PARTS2CLASS, int, 5000),
                        (WAIT2PICK, bool, False),
                        (OPTICAL_FLOW, bool, False),
                        ]
