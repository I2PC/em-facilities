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
import pickle
import subprocess
import random
from collections import OrderedDict

import pyworkflow.utils as pwutils
from pyworkflow.project import Manager
from pyworkflow.object import Pointer
from pyworkflow.em.protocol import (ProtImportMovies, ProtMonitorSummary,
                                    ProtUnionSet, ProtMonitor2dStreamer,
                                    ProtSubSet, ProtExtractCoords)

try:  # Xmipp plugin is mandatory to run this workflow
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
                                  XmippProtCropResizeVolumes, XmippProtEliminateEmptyClasses,
                                  XmippProtDeepMicrographScreen)
except Exception as exc:
     pwutils.pluginNotFound('xmipp', errorMsg=exc, doRaise=True)

# Protocols from plugins to import (some are optional, according to config params)
protPlugins = {'ProtMotionCorr': 'motioncorr.protocols',
               'ProtCTFFind': 'grigoriefflab.protocols',
               'ProtGctf': 'gctf.protocols',
               'DogPickerProtPicking': 'appion.protocols',
               'SparxGaussianProtPicking': 'eman2.protocols',
               'EmanProtInitModel': 'eman2.protocols',
               'SphireProtCRYOLOPicking': 'sphire.protocols',
               'ProtRelion2Autopick': 'relion.protocols',
               'ProtRelionAutopickLoG': 'relion.protocols',
               'ProtRelionExtractParticles': 'relion.protocols',
               'ProtRelionClassify2D': 'relion.protocols',
               'ProtRelionRefine3D': 'relion.protocols',
               'ProtRelionClassify3D': 'relion.protocols',
               'ProtCryo2D': 'cryosparc2.protocols',
               'ProtCryoSparcInitialModel': 'cryosparc2.protocols'}

from constants import *


def preprocessWorkflow(configDict):

    print("Final parameters to be used in the workflow:")
    for k, v in sorted(configDict.iteritems()):
        print(" -> %s: %s %s" % (k, type(v), v))
    print('')

    def get(var, default=None):
        return configDict.get(var, default)

    manager = Manager()
    project = manager.createProject(get(PROJECT_NAME),
                                    location=get(PROJECTS_PATH))


    # Total available CPUs to be used in very demanding computations
    numCpus = getCpus(get(NUM_CPU, -1))

    def getGpuArray(var):
        """ Get the a int list pointing to the GPUs for that protocol.
              output examples:
                - noGPU assigned: []
                - id assigned: [id]
                - multiple GPU assignation: [id1, id2, ...]
        """
        value = get(var, '-1')

        try:
            auxI = int(value)
            array = [] if auxI < 0 else [auxI]
        except:
            array = []
            for delim in [',', ':', '-']:
                if delim in value:
                    array = [int(x) for x in value.split(delim)]

        return array

    def getGpu(var):
        """ Get the valit string pointing to the GPUs for that protocol.
              output examples:
                - noGPU assigned: None
                - id assigned: 'id'
                - multiple GPU assignation: 'id1, id2, ...'
        """
        if getGpuArray(var):
            return get(var)
        else:
            return None

    def getRelionMPI(confVar=RELION_GPU):
        gpuList = getGpuArray(confVar)
        if gpuList:
            return 3
        else:
            return numCpus - 10 if numCpus > 10 else 4

    # we will fill a list with all protocols
    # to be included in the summary report
    summaryList = []
    def _registerProt(prot, label='', toSummary=False, color=''):
        project.saveProtocol(prot)
        if label != '':
            applyLabel(prot, label, color)
        if toSummary:
            summaryList.append(prot)

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

    # ***********   MOVIES   ***********************************************
    doDose = True if get(DOSEF, 0) > 0 else False
    gainGlob = pwutils.glob(os.path.join(get(DEPOSITION_DIR),
                                         get(GAIN_PAT, 'noGain')))
    if len(gainGlob) >= 1:
        gainFn = gainGlob[0]
    else:
        gainFn = ''
        print(" > No gain file found, proceeding without applying it.")
    if len(gainGlob) > 1:
        print(" > More than one gain file found, using only the first.")
    # ----------- IMPORT MOVIES -------------------
    timeout = (get(TIMEOUT, 43200) if get(SIMULATION, False)
               else get(TIMEOUT, 43200)*10)  # 43200=12h default
    protImport = project.newProtocol(ProtImportMovies,
                              objLabel='import movies',
                              importFrom=ProtImportMovies.IMPORT_FROM_FILES,
                              filesPath=get(DEPOSITION_DIR),
                              filesPattern=get(PATTERN),
                              amplitudeContrast=get(AMP_CONTR),
                              sphericalAberration=get(SPH_AB),
                              voltage=get(VOL_KV),
                              samplingRate=get(SAMPLING),
                              doseInitial=get(DOSE0, 0),
                              dosePerFrame=get(DOSEF, 0),
                              gainFile=gainFn,
                              dataStreaming=True,
                              timeout=timeout)
    _registerProt(protImport, label='Movies', toSummary=True)

    # ----------- MOVIE GAIN --------------------------
    protMG = project.newProtocol(XmippProtMovieGain,
                                 objLabel='Xmipp - movie gain',
                                 frameStep=5,
                                 movieStep=40,
                                 estimateOrientation=False)
    setExtendedInput(protMG.inputMovies, protImport, 'outputMovies')
    _registerProt(protMG, label='Movies', toSummary=True)

    # ----------- MOTIONCOR ----------------------------
    frame0 = get(FRAMES, [1, 0])[0]
    frameF = get(FRAMES, [1, 0])[1]
    if getGpu(MOTIONCOR2_GPU):
        mcMpi = (1 if len(getGpuArray(MOTIONCOR2_GPU)) == 1 else
                 len(getGpuArray(MOTIONCOR2_GPU)) + 1)
        protMA = project.newProtocol(importPlugin('ProtMotionCorr'),
                                     objLabel='MotionCor2 - movie align.',
                                     gpuList=get(MOTIONCOR2_GPU),
                                     numberOfThreads=mcMpi,
                                     doApplyDoseFilter=doDose,
                                     doSaveUnweightedMic=not doDose,
                                     patchX=5, patchY=5,
                                     extraParams2='-SumRange 0 0',  # To avoid DWS files
                                     alignFrame0=frame0,
                                     alignFrameN=frameF)
        setExtendedInput(protMA.inputMovies, protMG, 'outputMovies')
        _registerProt(protMA, 'Movies')
    else:
        # ----------- CORR ALIGN ----------------------------
        protMA = project.newProtocol(XmippProtMovieCorr,
                                     objLabel='Xmipp - corr. align.',
                                     numberOfThreads=numCpus,
                                     useGpu=False,
                                     doLocalAlignment=False,
                                     alignFrame0=frame0,
                                     alignFrameN=frameF)
        setExtendedInput(protMA.inputMovies, protImport, 'outputMovies')
        _registerProt(protMA, label='Movies')
    # ----------- MAX SHIFT -----------------------------
    protMax = project.newProtocol(XmippProtMovieMaxShift,
                                  objLabel='Xmipp - max shift')
    setExtendedInput(protMax.inputMovies, protMA, 'outputMovies')
    _registerProt(protMax, 'Movies', True)

    # ----------- OF ALIGNMENT --------------------------
    if get(OPTICAL_FLOW, False):
        protOF = project.newProtocol(XmippProtOFAlignment,
                                     objLabel='Xmipp - OF align.',
                                     doApplyDoseFilter=doDose,
                                     applyDosePreAlign=False)
        setExtendedInput(protOF.inputMovies, protMax, 'outputMovies')
        _registerProt(protOF, 'Movies')

        alignedMicsLastProt = protOF
    else:
        alignedMicsLastProt = protMax
        
    if doDose:
        alignMicsOutput = 'outputMicrographsDoseWeighted'
    else:
        alignMicsOutput = 'outputMicrographs'


    # *********   CTF ESTIMATION   *****************************************
    # --------- CTF ESTIMATION 2 ---------------------------
    if getGpu(GCTF_GPU):
        protCTF2 = project.newProtocol(importPlugin('ProtGctf'),
                                       objLabel='gCTF estimation',
                                       gpuList=get(GCTF_GPU))
        setExtendedInput(protCTF2.inputMicrographs,
                         alignedMicsLastProt, alignMicsOutput)
        _registerProt(protCTF2, 'CTF')

    else:
        protCTF2 = project.newProtocol(XmippProtCTFMicrographs,
                                       objLabel='Xmipp - ctf estimation',
                                       #doInitialCTF=True
                                       )
        #setExtendedInput(protCTF2.ctfRelations, protCTF2, 'outputCTF')
        setExtendedInput(protCTF2.inputMicrographs,
                         alignedMicsLastProt, alignMicsOutput)
        _registerProt(protCTF2, 'CTF')#, 'outputCTF')

    # --------- CTF ESTIMATION 1 ---------------------------
    protCTF1 = project.newProtocol(importPlugin('ProtCTFFind'),
                                   objLabel='GrigorieffLab - CTFfind',
                                   numberOfThreads=numCpus)
    setExtendedInput(protCTF1.inputMicrographs,
                     alignedMicsLastProt, alignMicsOutput)
    _registerProt(protCTF1, 'CTF')

    # --------- CTF CONSENSUS ---------------------------
    isCtf2Xmipp = isinstance(protCTF2, XmippProtCTFMicrographs)
    protCTFs = project.newProtocol(XmippProtCTFConsensus,
                                   objLabel='Xmipp - CTF consensus',
                                   useDefocus=True,
                                   useAstigmatism=True,
                                   useResolution=True,
                                   resolution=5,
                                   useCritXmipp=isCtf2Xmipp,
                                   calculateConsensus=True,
                                   minConsResol=7)
    setExtendedInput(protCTFs.inputCTF, protCTF2, 'outputCTF')
    setExtendedInput(protCTFs.inputCTF2, protCTF1, 'outputCTF')
    _registerProt(protCTFs, 'CTF', True)

    # *************   PICKING   ********************************************
    # --------- PREPROCESS MICS ---------------------------
    protPreMics0 = project.newProtocol(XmippProtPreprocessMicrographs,
                                      objLabel='Xmipp - preprocess Mics',
                                      doRemoveBadPix=True,
                                      doInvert=not get(INV_CONTR))
    setExtendedInput(protPreMics0.inputMicrographs,
                     protCTFs, 'outputMicrographs')
    _registerProt(protPreMics0, 'Micrographs')

    # Resizing to a larger sampling rate
    doDownSamp2D = 0 < get(SAMPLING_2D, -1) > get(SAMPLING)
    samp2D = get(SAMPLING_2D) if doDownSamp2D else get(SAMPLING)
    if doDownSamp2D:
        downSampPreMics = get(SAMPLING_2D) / get(SAMPLING)
        protPreMics = project.newProtocol(XmippProtPreprocessMicrographs,
                                          objLabel='downSampling to 2D size',
                                          doDownsample=True,
                                          downFactor=downSampPreMics)
        setExtendedInput(protPreMics.inputMicrographs,
                         protPreMics0, 'outputMicrographs')
        _registerProt(protPreMics, 'Micrographs')
    else:
        #downSampPreMics = 1
        protPreMics = protPreMics0

    #protPreMics = project.newProtocol(XmippProtPreprocessMicrographs,
    #                                  objLabel='Xmipp - preprocess Mics',
    #                                  doRemoveBadPix=True,
    #                                  doInvert=not get(INV_CONTR),
    #                                  doDownsample=downSampPreMics>1,
    #                                  downFactor=downSampPreMics)
    #setExtendedInput(protPreMics.inputMicrographs,
    #                 protCTFs, 'outputMicrographs')
    #_registerProt(protPreMics, 'Micrographs')

    pickers = []
    pickersOuts = []

    if get(PARTSIZE, 0) == 0 and get(MICS2PICK, 0) > 0:
        # -------- TRIGGER MANUAL-PICKER ---------------------------
        protTRIG0 = project.newProtocol(XmippProtTriggerData,
                                        objLabel='Xmipp - trigger some mics',
                                        outputSize=get(MICS2PICK, 10),
                                        allImages=True)
        setExtendedInput(protTRIG0.inputImages, protPreMics, 'outputMicrographs')
        _registerProt(protTRIG0, 'Picking')

        # -------- XMIPP MANUAL-PICKER -------------------------
        protPrePick = project.newProtocol(XmippProtParticlePicking,
                                          objLabel='Xmipp - manual picking',
                                          doInteractive=False)
        setExtendedInput(protPrePick.inputMicrographs,
                         protTRIG0, 'outputMicrographs')
        _registerProt(protPrePick, 'Picking')
        
        # -------- XMIPP AUTO-PICKING ---------------------------
        protPPauto = project.newProtocol(XmippParticlePickingAutomatic,
                                         objLabel='Xmipp - auto picking',
                                         xmippParticlePicking=protPrePick,
                                         micsToPick=1  # 0=same ; 1=other
                                         )
        setExtendedInput(protPPauto.inputMicrographs,
                         protPreMics, 'outputMicrographs')
        # protPPauto.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPPauto, 'Picking')

        pickers.append(protPPauto)
        pickersOuts.append('outputCoordinates')
        waitManualPick = True
        bxSize = None
    else:
        # -------- XMIPP AUTO-BOXSIZE -------------------------
        waitManualPick = False
        protPrePick = None
        # protPrePick = project.newProtocol(XmippProtParticleBoxsize,
        #                                   objLabel='Xmipp - particle boxsize')
        # setExtendedInput(protPrePick.inputMicrographs,
        #                  protCTFs, 'outputMicrographs')
        # _registerProt(protPrePick, 'Picking')
        bxSize = getEvenPartSize(get(PARTSIZE)/samp2D)

    def setBoxSize(protDotBoxSize):
        if protPrePick:
            setExtendedInput(protDotBoxSize, protPrePick, 'boxsize', True)
        else:
            protDotBoxSize.set(bxSize)

    # --------- PARTICLE PICKING CRYOLO ---------------------------
    if get(CRYOLO, True) and not waitManualPick:  # manualPick work alone, so far
        protPP2 = project.newProtocol(importPlugin('SphireProtCRYOLOPicking'),
                                      objLabel='Sphire - CrYolo auto-picking',
                                      conservPickVar=0.03,
                                      streamingBatchSize=4,
                                      gpuList='0')  # CPU version installation
        setBoxSize(protPP2.boxSize)
        setExtendedInput(protPP2.inputMicrographs, protPreMics, 'outputMicrographs')
        if waitManualPick:
            protPP2.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPP2, 'Picking')

        pickers.append(protPP2)
        pickersOuts.append('outputCoordinates')

    # --------- PARTICLE PICKING RELION LOG -----------------
    if get(RELION_PICK, True) and not waitManualPick:  # manualPick work alone, so far
        protPP4 = project.newProtocol(importPlugin('ProtRelionAutopickLoG'),
                                      objLabel='Relion - LoG auto-picking',
                                      conservPickVar=0.03,
                                      minDiameter=bxSize-20,
                                      maxDiameter=bxSize+10,
                                      maxResolution=-1,
                                      threshold=-1,
                                      streamingBatchSize=4)
        setBoxSize(protPP4.boxSize)
        setExtendedInput(protPP4.inputMicrographs, protPreMics, 'outputMicrographs')
        if waitManualPick:
            protPP4.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPP4, 'Picking')

        pickers.append(protPP4)
        pickersOuts.append('outputCoordinates')

    # --------- PARTICLE PICKING SPARX ---------------------------
    if get(SPARX, False) and not waitManualPick:  # manualPick work alone, so far
        # Be careful with the contrast, Sparx needs different contrast than CRYOLO
        protPP1 = project.newProtocol(importPlugin('SparxGaussianProtPicking'),
                                      objLabel='Eman - Sparx auto-picking',
                                      lowerThreshold=0.02)
        setBoxSize(protPP1.boxSize)
        if waitManualPick:
            protPP1.addPrerequisites(protPrePick.getObjId())
        _registerProt(protPP1, 'Picking')

        pickers.append(protPP1)
        pickersOuts.append('outputCoordinates')
        
       # --------- PARTICLE PICKING DOGPICKER ---------------------------
    if get(DOGPICK, False) and not waitManualPick:  # manualPick work alone, so far
        protPP3 = project.newProtocol(importPlugin('DogPickerProtPicking'),
                                      objLabel='Appion - DoG auto-picking',
                                      diameter=bxSize*get(SAMPLING))  # in A
        setExtendedInput(protPP3.inputMicrographs, protPreMics, 'outputMicrographs')
        _registerProt(protPP3, 'Picking')

        pickers.append(protPP3)
        pickersOuts.append('outputCoordinates')     

    # --------- CONSENSUS PICKING -----------------------
    if len(pickers) > 1:
        # --------- CONSENSUS PICKING AND -----------------------
        consRadius = int(bxSize/3) if bxSize else 10
        protCPand = project.newProtocol(XmippProtConsensusPicking,
                                        objLabel='Xmipp - consensus picking (AND)',
                                        consensusRadius=consRadius,
                                        consensus=-1)
        setExtendedInput(protCPand.inputCoordinates, pickers, pickersOuts)
        _registerProt(protCPand, 'Picking', True)

        # --------- CONSENSUS PICKING OR -----------------------
        protCPor = project.newProtocol(XmippProtConsensusPicking,
                                       objLabel='Xmipp - consensus picking (OR)',
                                       consensusRadius=consRadius,
                                       consensus=1)

        setExtendedInput(protCPor.inputCoordinates, pickers, pickersOuts)
        _registerProt(protCPor, 'Picking')

        finalPicker = protCPand
        outputCoordsStr = 'consensusCoordinates'
        outCPor = 'consensusCoordinates'
    else:
        finalPicker = pickers[0]
        outputCoordsStr = pickersOuts[0]
        protCPor = finalPicker
        outCPor = outputCoordsStr

    # ----- DEEP CARBON CLEANER -----------------------
    protDCC = project.newProtocol(XmippProtDeepMicrographScreen,
                                  objLabel='Xmipp - micrograph cleaner',
                                  gpuList=get(GL2D_GPU),
                                  threshold=0.75,
                                  streamingBatchSize=4,
                                  micsSource=1)
    setExtendedInput(protDCC.inputCoordinates, finalPicker, outputCoordsStr)
    setExtendedInput(protDCC.inputMicrographs,
                     protPreMics, 'outputMicrographs')
    #_registerProt(protDCC, 'Picking', True)  # not working yet
    dccOutputStr = protDCC.getOutputName()

    protExtractAnd2 = project.newProtocol(XmippProtExtractParticles,
                                         objLabel='Xmipp - extract particles TEST',
                                         boxSize=-1,
                                         downsampleType=1,  # Other to avoid a bug
                                         doRemoveDust=True,
                                         doNormalize=True,
                                         doInvert=get(INV_CONTR),
                                         doFlip=True)
    setExtendedInput(protExtractAnd2.inputCoordinates, protDCC, dccOutputStr)
    setExtendedInput(protExtractAnd2.inputMicrographs,
                     protPreMics, 'outputMicrographs')
    setExtendedInput(protExtractAnd2.ctfRelations, protCTFs, 'outputCTF')
    #_registerProt(protExtractAnd2, 'Particles')

    protDCC = finalPicker
    dccOutputStr = outputCoordsStr

    # ---------------------------------- AND/SINGLE PICKING BRANCH ----------

    # --------- EXTRACT PARTICLES AND ----------------------
    ANDstr = ' (AND)' if len(pickers) > 1 else ''
    protExtractAnd = project.newProtocol(XmippProtExtractParticles,
                                         objLabel='Xmipp - extract particles%s'%ANDstr,
                                         boxSize=-1,
                                         downsampleType=1,  # Other to avoid a bug
                                         doRemoveDust=True,
                                         doNormalize=True,
                                         doInvert=get(INV_CONTR),
                                         doFlip=True)
    setExtendedInput(protExtractAnd.inputCoordinates, protDCC, dccOutputStr)
    setExtendedInput(protExtractAnd.inputMicrographs,
                     protPreMics, 'outputMicrographs')
    setExtendedInput(protExtractAnd.ctfRelations, protCTFs, 'outputCTF')
    _registerProt(protExtractAnd, 'Particles')

    # ***********   CLEAN PARTICLES   ************************************
    # --------- ELIM EMPTY PARTS AND ---------------------------
    protEEPand = project.newProtocol(XmippProtEliminateEmptyParticles,
                                     objLabel='Xmipp - Elim. empty part.%s'%ANDstr,
                                     threshold=0.6)
    setExtendedInput(protEEPand.inputParticles, protExtractAnd, 'outputParticles')
    _registerProt(protEEPand, 'Particles')

    # --------- TRIGGER PARTS AND ---------------------------
    protTRIGand = project.newProtocol(XmippProtTriggerData,
                                      objLabel='Xmipp - trigger data to stats%s'%ANDstr,
                                      outputSize=1000, delay=30,
                                      allImages=True,
                                      splitImages=False)
    setExtendedInput(protTRIGand.inputImages, protEEPand, 'outputParticles')
    _registerProt(protTRIGand, 'Particles')

    # --------- SCREEN PARTS AND ---------------------------
    protSCRand = project.newProtocol(XmippProtScreenParticles,
                                     objLabel='Xmipp - Screen particles%s'%ANDstr)
    protSCRand.autoParRejection.set(XmippProtScreenParticles.REJ_MAXZSCORE)
    protSCRand.autoParRejectionSSNR.set(XmippProtScreenParticles.REJ_PERCENTAGE_SSNR)
    protSCRand.autoParRejectionVar.set(XmippProtScreenParticles.REJ_VARIANCE)
    setExtendedInput(protSCRand.inputParticles, protTRIGand, 'outputParticles')
    _registerProt(protSCRand, 'Particles', len(pickers) < 2)
    # ----------------------------- END OF AND/SINGLE PICKING BRANCH --------

    # ----------------------------- AND PICKING BRANCH ---------------------
    if len(pickers) > 1:  # if so, Elim. Empty and Screen are the same of above
        # --------- EXTRACT PARTICLES OR ----------------------
        protExtractOr = project.newProtocol(XmippProtExtractParticles,
                                            objLabel='Xmipp - extract particles (OR)',
                                            boxSize=-1,
                                            downsampleType=1,  # Other to skip a bug
                                            doRemoveDust=True,
                                            doNormalize=True,
                                            doInvert=get(INV_CONTR),
                                            doFlip=True)
        setExtendedInput(protExtractOr.inputCoordinates,
                         protCPor, 'consensusCoordinates')
        setExtendedInput(protExtractOr.inputMicrographs,
                         protPreMics, 'outputMicrographs')
        setExtendedInput(protExtractOr.ctfRelations, protCTFs, 'outputCTF')
        _registerProt(protExtractOr, 'Particles')

        # --------- ELIM EMPTY PARTS AND ---------------------------
        protEEPor = project.newProtocol(XmippProtEliminateEmptyParticles,
                                        objLabel='Xmipp - Elim. empty part. (OR)',
                                        inputType=0,
                                        threshold=0.6)
        setExtendedInput(protEEPor.inputParticles, protExtractOr, 'outputParticles')
        _registerProt(protEEPor, 'Particles')

        # --------- TRIGGER PARTS AND  ---------------------------
        protTRIGor = project.newProtocol(XmippProtTriggerData,
                                         objLabel='Xmipp - trigger data to stats (OR)',
                                         outputSize=1000, delay=30,
                                         allImages=True,
                                         splitImages=False)
        setExtendedInput(protTRIGor.inputImages, protEEPor, 'outputParticles')
        _registerProt(protTRIGor, 'Particles')

        # --------- SCREEN PARTS AND  ---------------------------
        protSCRor = project.newProtocol(XmippProtScreenParticles,
                                        objLabel='Xmipp - screen particles (OR)')
        protSCRor.autoParRejection.set(XmippProtScreenParticles.REJ_MAXZSCORE)
        protSCRor.autoParRejectionSSNR.set(XmippProtScreenParticles.REJ_PERCENTAGE_SSNR)
        protSCRor.autoParRejectionVar.set(XmippProtScreenParticles.REJ_VARIANCE)
        setExtendedInput(protSCRor.inputParticles, protTRIGor, 'outputParticles')
        _registerProt(protSCRor, 'Particles', True)
    else:
        protExtractOr = protExtractAnd
        protSCRor = protSCRand


    # ************   CLASSIFY 2D   *****************************************
    if get(DO_2DCLASS, True):
        allAvgs = []
        classifiers = []
        # --------- TRIGGER PARTS ---------------------------
        protTRIG2 = project.newProtocol(XmippProtTriggerData,
                                        objLabel='Xmipp - trigger data to classify',
                                        outputSize=get(PARTS2CLASS, 5000),
                                        delay=30,
                                        allImages=False)
        setExtendedInput(protTRIG2.inputImages, protSCRand, 'outputParticles')
        _registerProt(protTRIG2, '2Dclassify')

        if get(CRYOS_2D, True):
            protCryoSparc2D = project.newProtocol(importPlugin('ProtCryo2D'),
                                                  objLabel='Cryosparc2 - classify 2D',
                                                  numberOfClasses=16,
                                                  cacheParticlesSSD=get(USE_CRYOS_SSD, False))
            setExtendedInput(protCryoSparc2D.inputParticles, protTRIG2, 'outputParticles')
            _registerProt(protCryoSparc2D, '2Dclassify')
            classifiers.append(protCryoSparc2D)
            # Classes -> Averages
            protCl2Av0 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                             objLabel='Classes to averages (cs2)',
                                             threshold=-1,
                                             usePopulation=False)
            setExtendedInput(protCl2Av0.inputClasses, protCryoSparc2D, 'outputClasses')
            _registerProt(protCl2Av0, '2Dclassify')
            allAvgs.append(protCl2Av0)

        # --------- XMIPP GL2D/CL2D ---------------------------
        if get(XMIPP_2D, True):
            if False:  # getGpu(GL2D_GPU):
                gl2dMpi = numCpus if numCpus<32 else 32
                protCL = project.newProtocol(XmippProtGpuCrrCL2D,
                                             objLabel='Xmipp - GL2D',
                                             gpuList=get(GL2D_GPU),
                                             numberOfClasses=16,
                                             numberOfMpi=gl2dMpi)
            else:
                protCL = project.newProtocol(XmippProtCL2D,
                                             objLabel='Xmipp - CL2D',
                                             doCore=False,
                                             numberOfClasses=16,
                                             numberOfMpi=numCpus-20)
            setExtendedInput(protCL.inputParticles, protTRIG2, 'outputParticles')
            _registerProt(protCL, '2Dclassify')
            classifiers.append(protCL)
            # Classes -> Averages
            protCl2Av1 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                             objLabel='Classes to averages (xmipp)',
                                             threshold=-1,
                                             usePopulation=False)
            setExtendedInput(protCl2Av1.inputClasses, protCL, 'outputClasses')
            _registerProt(protCl2Av1, '2Dclassify')
            allAvgs.append(protCl2Av1)

        # --------- Relion 2D classify ---------------------------
        if get(RELION_2D, True):
            protCL2 = project.newProtocol(importPlugin('ProtRelionClassify2D'),
                                          objLabel='Relion - 2D classifying',
                                          doGpu=bool(getGpu(RELION_GPU)),
                                          gpusToUse=getGpu(RELION_GPU),
                                          numberOfClasses=16,
                                          relionCPUs=getRelionMPI())
            setExtendedInput(protCL2.inputParticles, protTRIG2, 'outputParticles')
            if get(RELION_GPU, -1) == get(GL2D_GPU, -1) and get(XMIPP_2D):
                protCL2.addPrerequisites(protCL.getObjId())
            _registerProt(protCL2, '2Dclassify')
            classifiers.append(protCL2)
            # Classes -> Averages
            protCl2Av2 = project.newProtocol(XmippProtEliminateEmptyClasses,
                                             objLabel='Classes to averages (relion)',
                                             threshold=-1,
                                             usePopulation=False)
            setExtendedInput(protCl2Av2.inputClasses, protCL2, 'outputClasses')
            _registerProt(protCl2Av2, '2Dclassify')
            allAvgs.append(protCl2Av2)

        # --------- JOIN SETS ---------------------------
        if len(allAvgs) > 1:
            protJOIN = project.newProtocol(ProtUnionSet,
                                           objLabel='Scipion - Join all Averages')
            setExtendedInput(protJOIN.inputSets,
                             allAvgs, ['outputAverages']*len(allAvgs))
            _registerProt(protJOIN, '2Dclassify')
            allAvgsOut = 'outputSet'
        else:
            protJOIN = allAvgs[0]
            allAvgsOut = 'outputAverages'

        # --------- AUTO CLASS SELECTION ---------------------------
        protCLSEL = project.newProtocol(XmippProtEliminateEmptyClasses,
                                        objLabel='Xmipp - Auto class selection',
                                        threshold=12,
                                        usePopulation=False)
        setExtendedInput(protCLSEL.inputClasses, protJOIN, allAvgsOut)
        _registerProt(protCLSEL, 'initVol')


    # ***************   INITIAL VOLUME   ***********************************
    if get(DO_INITVOL, True):
        initVols = []
        initVolsOuts = []
        initVolDeps = -1
        initVolCpus = numCpus - 8 if numCpus > 8 else int(numCpus/2)+1
        # ------------ RECONSTRUCT SIGNIFICANT ---------------------------
        if get(SIGNIFICANT, True):
            protSIG = project.newProtocol(XmippProtReconstructSignificant,
                                          objLabel='Xmipp - Recons. significant',
                                          symmetryGroup=get(SYMGROUP, 'c1'),
                                          numberOfMpi=initVolCpus,
                                          iter=35)
            setExtendedInput(protSIG.inputSet, protCLSEL, 'outputAverages')
            _registerProt(protSIG, 'initVol')
            initVolDeps = protSIG.getObjId()
            initVols.append(protSIG)
            initVolsOuts.append('outputVolume')

        # --------- EMAN INIT VOLUME ---------------------------
        if get(EMAN_INITIAL, True):
            protINITVOL = project.newProtocol(importPlugin('EmanProtInitModel'),
                                              objLabel='Eman - Initial vol',
                                              symmetry=get(SYMGROUP, 'c1'),
                                              numberOfThreads=initVolCpus,
                                              numberOfModels=7)
            setExtendedInput(protINITVOL.inputSet, protCLSEL, 'outputAverages')
            if initVolDeps > 0: protINITVOL.addPrerequisites(initVolDeps)
            _registerProt(protINITVOL, 'initVol')
            initVolDeps = protINITVOL.getObjId()
            initVols.append(protINITVOL)
            initVolsOuts.append('outputVolumes')

        # --------- RECONSTRUCT RANSAC ---------------------------
        if get(RANSAC, False):
            protRAN = project.newProtocol(XmippProtRansac,
                                          objLabel='Xmipp - Ransac significant',
                                          symmetryGroup=get(SYMGROUP, 'c1'),
                                          numberOfThreads=initVolCpus)
            setExtendedInput(protRAN.inputSet, protCLSEL, 'outputAverages')
            if initVolDeps > 0: protRAN.addPrerequisites(initVolDeps)
            _registerProt(protRAN, 'initVol')
            initVolDeps = protRAN.getObjId()
            initVols += [protRAN]
            initVolsOuts += ['outputVolumes']

        # --------- CREATING AN ALIGNED SET OF VOLUMES -----------
        if len(initVols) > 1:
            protAVOL = project.newProtocol(XmippProtAlignVolume,
                                           objLabel='Xmipp - Join/Align volumes',
                                           alignmentAlgorithm=3,  # Fast Fourier
                                           numberOfThreads=initVolCpus)
            setExtendedInput(protAVOL.inputReference, protSIG, 'outputVolume')
            setExtendedInput(protAVOL.inputVolumes, initVols, initVolsOuts)
            _registerProt(protAVOL, 'initVol')

            # --------- SWARM CONSENSUS INITIAL VOLUME ---------------
            protSWARM = project.newProtocol(XmippProtReconstructSwarm,
                                            objLabel='Xmipp - Swarm init. vol.',
                                            symmetryGroup=get(SYMGROUP, 'c1'),
                                            numberOfMpi=numCpus,
                                            numberOfIterations=5)
            setExtendedInput(protSWARM.inputParticles, protTRIG2, 'outputParticles')
            setExtendedInput(protSWARM.inputVolumes, protAVOL, 'outputVolumes')
            _registerProt(protSWARM, 'initVol')
            initVolOut = 'outputVolume'
        else:  # if no swarm, we use the only one initVolume
            protSWARM = initVols[0]
            initVolOut = initVolsOuts[0]


    # ***************   3D ANALISIS   **************************************
    relion3Ddeps = -1
    go2FullSize = get(DO_FULLSIZE, True) and doDownSamp2D
    if get(DO_3DCLASS, True) or go2FullSize:
        # --------- RESIZE THE INITIAL VOL TO FULL SIZE ----------
        doDownSample3D = 0 < get(SAMPLING_3D, -1) < samp2D
        if doDownSample3D or go2FullSize:
            finalSamp = (get(SAMPLING_3D) if doDownSample3D
                         else get(SAMPLING))
            # bxSize3D = getEvenPartSize(get(PARTSIZE)/finalSamp)
            label3DStr = '3D' if doDownSample3D else 'FULL'

            protVOL3D = project.newProtocol(XmippProtCropResizeVolumes,
                                            objLabel='Resize volume - %s SIZE'%label3DStr,
                                            doResize=True,
                                            resizeOption=0,  # sampling rate
                                            # doFourier=True,  # incompatible with sampling rate option
                                            resizeSamplingRate=finalSamp)
            setExtendedInput(protVOL3D.inputVolumes, protSWARM, initVolOut)
            _registerProt(protVOL3D, 'useful_OUTPUTs', color='#00ff00')
            vol3Dout = 'outputVol'

            # # --------- EXTRACT (almost) FULL SIZE PART ------------------
            # ---- preprocess mics ----
            if doDownSample3D:
                # Resizing to a larger sampling rate
                #downSamp3D = get(SAMPLING_3D) / get(SAMPLING)
                #protPreMics3D = project.newProtocol(XmippProtPreprocessMicrographs,
                #                                    objLabel='downsampling to %s SIZE'%label3DStr,
                #                                    doDownsample=True,
                #                                    downFactor=downSamp3D)
                #setExtendedInput(protPreMics3D.inputMicrographs,
                #                 protPreMics0, 'outputMicrographs')
                #_registerProt(protPreMics3D, '3Danalysis')

                protExCoord = project.newProtocol(ProtExtractCoords,
                                                  objLabel='extract coords. to %s SIZE'%label3DStr)
                setExtendedInput(protExCoord.inputParticles,
                                 protSCRor, 'outputParticles')
                setExtendedInput(protExCoord.inputMicrographs,
                                 protPreMics0, 'outputMicrographs')
                _registerProt(protExCoord, '3Danalysis')

                dwnFactor = get(SAMPLING_3D) / get(SAMPLING)

            else:  # from the full sized
                #protPreMics3D = protPreMics0
                dwnFactor = 1
            # ---- extract parts -------
            protExtract3D = project.newProtocol(XmippProtExtractParticles,
                                                objLabel='Xmipp - extract part. %s SIZE'%label3DStr,
                                                boxSize=-1,
                                                downsampleType=1,  # other mics
                                                downFactor=dwnFactor,
                                                doRemoveDust=True,
                                                doNormalize=True,
                                                doInvert=get(INV_CONTR),
                                                doFlip=True)
            setExtendedInput(protExtract3D.inputCoordinates,
                             protExCoord, 'outputCoordinates')
            setExtendedInput(protExtract3D.inputMicrographs,
                             protPreMics0, 'outputMicrographs')
            setExtendedInput(protExtract3D.ctfRelations, protCTFs, 'outputCTF')
            _registerProt(protExtract3D, 'useful_OUTPUTs', color='#00ff00')
        else:
            protVOL3D = protSWARM
            vol3Dout = initVolOut
            protExtract3D = protExtractAnd

    if get(DO_3DCLASS, True):
        # Trigger particles to 3D analysis (needed even with PARTS3D=-1)
        partsFor3Dcls = get(PARTS3D) if get(PARTS3D, -1) > 0 else 1  # a minimum
        protPartTr3D = project.newProtocol(XmippProtTriggerData,
                                           objLabel='Xmipp - trigger data to 3D',
                                           outputSize=partsFor3Dcls,
                                           delay=30,
                                           allImages=False)
        protPartTr3D.addPrerequisites(protVOL3D.getObjId())
        setExtendedInput(protPartTr3D.inputImages, protSCRand, 'outputParticles')
        _registerProt(protPartTr3D, '3Danalysis')
        # Subset (almost) full size
        protPart3D = project.newProtocol(ProtSubSet,
                             objLabel='Scipion - clean particles %s SIZE'%label3DStr)
        setExtendedInput(protPart3D.inputFullSet,
                         protExtract3D, 'outputParticles')
        setExtendedInput(protPart3D.inputSubSet,
                         protPartTr3D, 'outputParticles')
        _registerProt(protPart3D, '3Danalysis')

        if get(RELION_REFINE, True):
            # ---------- Refine 3D full sized -----------------------------------
            protRelionRefine = project.newProtocol(importPlugin('ProtRelionRefine3D'),
                                           objLabel='Relion - Refine 3D',
                                           initialLowPassFilterA=15,
                                           symmetryGroup=get(SYMGROUP, 'c1'),
                                           doGpu=bool(getGpu(RELION_GPU)),
                                           gpusToUse=getGpu(RELION_GPU),
                                           numberOfMpi=getRelionMPI()
                                                   )
            setExtendedInput(protRelionRefine.inputParticles,
                             protPart3D, 'outputParticles')
            setExtendedInput(protRelionRefine.referenceVolume,
                             protVOL3D, vol3Dout)
            if relion3Ddeps > 0: protRelionRefine.addPrerequisites(relion3Ddeps)
            _registerProt(protRelionRefine, '3Danalysis')
            relion3Ddeps = protRelionRefine.getObjId()

        if get(RELION_3DCL, True):
            protRelion3D = project.newProtocol(importPlugin('ProtRelionClassify3D'),
                                           objLabel='Relion - 3D class.',
                                           # initialLowPassFilterA=15,
                                           symmetryGroup=get(SYMGROUP, 'c1'),
                                           doGpu=bool(getGpu(RELION_GPU)),
                                           gpusToUse=getGpu(RELION_GPU),
                                           numberOfMpi=getRelionMPI()
                                                    )
            setExtendedInput(protRelion3D.inputParticles,
                             protPart3D, 'outputParticles')
            setExtendedInput(protRelion3D.referenceVolume,
                             protVOL3D, vol3Dout)
            if relion3Ddeps > 0: protRelion3D.addPrerequisites(relion3Ddeps)
            _registerProt(protRelion3D, '3Danalysis')
            relion3Ddeps = protRelion3D.getObjId()

        if get(CRYOS_3D, True):
            symStr = get(SYMGROUP, 'c1')
            symOrder = 1
            if symStr.startswith('c'):
                symGroup = 0
                symOrder = int(symStr.lstrip('c'))
            elif symStr.startswith('d'):
                symGroup = 1
                symOrder = int(symStr.lstrip('d'))
            elif symStr == 't':
                symGroup = 2
            elif symStr == 'o':
                symGroup = 3
            elif symStr == 'i1':
                symGroup = 4
            elif symStr == 'i2':
                symGroup = 5
            else:
                symGroup = 0
                symOrder = 1

            protCS2_3D = project.newProtocol(importPlugin('ProtCryoSparcInitialModel'),
                                             objLabel='Cryosparc2 - 3D class.',
                                             compute_use_ssd=get(USE_CRYOS_SSD, False),
                                             abinit_K=3,
                                             symmetryGroup=symGroup,
                                             symmetryOrder=symOrder,
                                             numberOfMpi=2,
                                             numberOfThreads=2)
            setExtendedInput(protCS2_3D.inputParticles, protPart3D, 'outputParticles')
            _registerProt(protCS2_3D, '3Danalysis')


    # ************   FINAL PROTOCOLS   *************************************
    # --------- Streaming classification to monitor --------------------
    if get(DO_2DCLASS, True):
        if getGpu(GL2D_GPU):
            # --------- GL2D in streaming --------------------
            protGL2D = project.newProtocol(XmippProtStrGpuCrrSimple,
                                           objLabel='Xmipp - GL2D assignation',
                                           gpuList=get(GL2D_GPU))
            setExtendedInput(protGL2D.inputRefs, protCl2Av2, 'outputAverages')
            setExtendedInput(protGL2D.inputParticles, protSCRor, 'outputParticles')
            _registerProt(protGL2D, 'useful_OUTPUTs', color='#00ff00')
        else:
            # --------- ADDING 2D CLASSIFIERS -------------------------
            clProt2Streaming = protCL2 if get(RELION_2D) else classifiers[0]
            protStreamer = project.newProtocol(ProtMonitor2dStreamer,
                                               objLabel='Scipion - Streamer',
                                               input2dProtocol=clProt2Streaming,
                                               batchSize=2000,
                                               startingNumber=get(PARTS2CLASS, 5000),
                                               samplingInterval=1 if get(TIMEOUT) < 10 else 10)
            setExtendedInput(protStreamer.inputParticles, protSCRor, 'outputParticles')
            if relion3Ddeps > 0: protStreamer.addPrerequisites(relion3Ddeps)
            _registerProt(protStreamer, '2Dclassify')


    # --------- SUMMARY MONITOR -----------------------
    protMonitor = project.newProtocol(ProtMonitorSummary,
                                   objLabel='Scipion - Summary Monitor',
                                   samplingInterval=20)
    protMonitor.inputProtocols.set(summaryList)
    _registerProt(protMonitor, 'monitor')

    # Saving the labels and colors:
    with open(os.path.join(get(PROJECTS_PATH), get(PROJECT_NAME), 'labels.pkl'),
              'w') as f:
        pickle.dump([labelsDict, colorsDict], f)


def getEvenPartSize(partSize):
    """ Fixing an even partSize big enough:
        int(x / 2 + 1) * 2 = ceil(x / 2) * 2 = even!
    """
    return int(partSize / 2 + 1) * 2


def importPlugin(protocol):
    if protocol not in protPlugins:
        raise Exception("'%s' protocol from plugin not found. Please, "
                        "include it at the available protocol list.\n"
                        "(at the beginning of %s)"
                        % (protocol, os.path.abspath(__file__)))
    return pwutils.importFromPlugin(protPlugins[protocol], protocol,
                                    doRaise=True)

labelsDict = OrderedDict()  # key: labelName ; value: [prot1, prot2, prot3...])
colorsDict = OrderedDict()  # key: labelName ; value: colorRGB
random.seed(6)
colorsDef = ["#e57373", "#4fc3f7", "#81c784", "#ff8a65", "#9575cd",
             "#a1887f", "#ffd54f", "#dce775", "#4db6ac"]

def applyLabel(prot, labelName, color=''):
    if all(l != labelName for l in labelsDict.keys()):
        if color == '':
            if len(colorsDict) < 9:
                color = colorsDef[len(colorsDict)]
            else:
                color = "#%s" % ''.join([random.choice('0123456789abcdef')
                                         for j in range(6)])
        colorsDict.update({labelName: color})
        labelsDict.update({labelName: [prot.getObjId()]})
    else:
        labelsDict[labelName].append(prot.getObjId())

def getCpus(cpusDefault):
    if cpusDefault > 0:
        numCpus = cpusDefault
    else:
        try:
            numCpus = int(subprocess.Popen(['nproc', '--all'],
                          stdout=subprocess.PIPE).stdout.read())
        except:
            numCpus = 8
    return numCpus
