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
import subprocess

import pyworkflow.utils as pwutils
from pyworkflow.object import Pointer
from pyworkflow.em.protocol import (ProtImportMovies, ProtMonitorSummary,
                                    ProtUnionSet, ProtUserSubSet,
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

from constants import *


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
