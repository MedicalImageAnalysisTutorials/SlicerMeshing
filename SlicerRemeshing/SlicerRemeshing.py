# ======================================================================================
#  Interface for Instant-Meshing [1] and Robust Quad/Hex-dominant Meshing [2]         #
#  to remesh segmentations                                                            #
#                                                                                     #
#  Contributers:                                                                      #
#                                                                                     #
#      - Ibraheem Al-Dhamari,  idhamari@uni-koblenz.de  : Plugin design & programming.#
#      - Heike Polders,        polders@uni-koblenz.de   : Programming & testing.      #
#      - Nora Schwartz         nschwartz@uni-koblenz.de : Programming & testing.      #
#      - Christian Schroeder   cschroeder@uni-koblenz.de: Programming & testing.      #
#                                                                                     #
#  [1] http://igl.ethz.ch/projects/instant-meshes                                     #
#  [2] https://github.com/gaoxifeng/robust_hex_dominant_meshing                       #
#                                                                                     #
#                                                                                     #
#  Updated: 3.3.2019                                                                  #
# =====================================================================================

import os, re , datetime, time ,shutil, unittest, logging, zipfile, urllib2, stat,  inspect
import sitkUtils, sys ,math, platform  
import  numpy as np, SimpleITK as sitk
import vtkSegmentationCorePython as vtkSegmentationCore
import vtk
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *   
from copy import deepcopy
from collections import defaultdict
from os.path import expanduser
from os.path import isfile
from os.path import basename
from PythonQt import BoolResult
from shutil import copyfile


# TODO:
#  Build and test in windows
#  speedup the process
#  add progress bar??? need interact with external tool iteration counter
#
#       check if range of Scale and Smoothing iteration need to be changed
#       robust Quad/Hex dominant meshing takes between 7 - 40 seconds or it runs forever - check!


# ===================================================================
#                           Main Class
# ===================================================================
class SlicerRemeshing(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        # Interface Captions
        parent.title = "SlicerRemeshing"
        parent.categories = ["VisSimTools"]
        parent.dependencies = []
        parent.contributors = ["Ibraheem Al-Dhamari, idhamari@uni-koblenz.de",  "Heike Polders, polders@uni-koblenz.de" , "Nora Schwartz, nschwartz@uni-koblenz.de", "Christian Schroeder, cschroeder@uni-koblenz.de"  ]
        parent.helpText = " This module is an interface to Instant and Quad/Hex-dominant Meshing"
        parent.acknowledgementText = "   "
        self.parent = parent


#===================================================================
#                           Main Widget
#===================================================================
class SlicerRemeshingWidget(ScriptedLoadableModuleWidget):

    #----------------------------------------   Initialization
    def setup(self):
        print(" ")
        print("=======================================================")
        print("                 Remeshing Tools 2019                  ")
        print("=======================================================")

        ScriptedLoadableModuleWidget.setup(self)

        # Declare global labels
        self.imtimeLbl = qt.QLabel("                 Time: 00:00")
        self.imtimeLbl.setFixedWidth(300)
        self.qhtimeLbl = qt.QLabel("                 Time: 00:00")
        self.qhtimeLbl.setFixedWidth(300)

        # Initialize GUI
        self.initMainPanel()

        self.logic = SlicerRemeshingLogic()
        self.logic.setGlobalVariables()
        self.logic.checkBinaries()

        # change the model type from vtk to stl
        msn = slicer.vtkMRMLModelStorageNode()
        msn.SetDefaultWriteFileExtension('stl')
        slicer.mrmlScene.AddDefaultNode(msn)
    #endef

    # --------------------------------------------------------------------------------------------
    #                        Main  Panel
    # --------------------------------------------------------------------------------------------
    def initMainPanel(self):
        # Create main collapsible Button
        self.mainCollapsibleBtn = ctk.ctkCollapsibleButton()
        self.mainCollapsibleBtn.setStyleSheet("ctkCollapsibleButton { background-color: DarkSeaGreen  }")
        self.mainCollapsibleBtn.text = "Remeshing Tools Selection"
        #self.mainCollapsibleBtn.collapsible = True
        self.layout.addWidget(self.mainCollapsibleBtn)
        self.mainFormLayout = qt.QFormLayout(self.mainCollapsibleBtn)

        # Create input Segmentation Selector
        self.inputSelectorCoBx = slicer.qMRMLNodeComboBox()
        self.inputSelectorCoBx.nodeTypes = ["vtkMRMLModelNode"]
        self.inputSelectorCoBx.setFixedWidth(200)
        self.inputSelectorCoBx.selectNodeUponCreation = True
        self.inputSelectorCoBx.addEnabled = False
        self.inputSelectorCoBx.removeEnabled = False
        self.inputSelectorCoBx.noneEnabled = False
        self.inputSelectorCoBx.showHidden = False
        self.inputSelectorCoBx.showChildNodeTypes = False
        self.inputSelectorCoBx.setMRMLScene(slicer.mrmlScene)
        self.inputSelectorCoBx.setToolTip("select an .stl file as the input segmentation")
        self.mainFormLayout.addRow("Input segmentation: ", self.inputSelectorCoBx)

        # Create button to show mesh of InputNode
        self.showMeshBtn = qt.QPushButton("Show Mesh")
        self.showMeshBtn.setFixedHeight(20)
        self.showMeshBtn.setFixedWidth(100)
        self.showMeshBtn.setStyleSheet("QPushButton{ background-color: DarkSeaGreen  }")
        self.showMeshBtn.toolTip = ('How to use:' ' Click the Show Mesh Button to show mesh of Input Segmentation ')
        self.showMeshBtn.connect('clicked(bool)', self.onShowBtnClick)
        self.mainFormLayout.addRow("Input Segmentation: ", self.showMeshBtn)

        # Create button to set visibility to 1 of inputNode
        self.showBtn = qt.QPushButton("Show Input")
        self.showBtn.setFixedHeight(20)
        self.showBtn.setFixedWidth(100)
        self.showBtn.setStyleSheet("QPushButton{ background-color: DarkSeaGreen  }")
        self.showBtn.toolTip = ('How to use:' ' Click the Show Mesh Button to show Input Segmentation ')
        self.showBtn.connect('clicked(bool)', self.onInputBtnClick)
        self.mainFormLayout.addRow("Input Segmentation: ", self.showBtn)

        # ---------------------------------------INSTANT MESHING--------------------------------------------
        # Create collapsible Button for Instant-Meshing options
        self.instantCollapsibleBtn = ctk.ctkCollapsibleButton()
        self.instantCollapsibleBtn.text = "Instant-Meshing"
        self.layout.addWidget(self.instantCollapsibleBtn)
        self.instantFormLayout = qt.QFormLayout(self.instantCollapsibleBtn)
        self.instantCollapsibleBtn.connect('clicked(bool)', self.onInstantClick)

        # Create button to run the Instant-Meshing tool
        self.imBtn = qt.QPushButton("Run")
        self.imBtn.setFixedHeight(40)
        self.imBtn.setFixedWidth(100)
        self.imBtn.setStyleSheet("QPushButton{ background-color: DarkSeaGreen  }")
        self.imBtn.toolTip = ('How to use:' ' Click the Run Button to start instant-meshing ')
        self.imBtn.connect('clicked(bool)', self.onImBtnClick)
        self.instantFormLayout.addRow(self.imBtn, self.imtimeLbl)

        # Create check box to display normals
        self.checkshowNormals = qt.QCheckBox()
        self.checkshowNormals.checked = False
        self.checkshowNormals.toolTip = ('If activated:' ' shows normals ')
        self.checkshowNormals.stateChanged.connect(self.onCheckShowNormalsChkBx)
        self.instantFormLayout.addRow("                                         Show normals: ", self.checkshowNormals)

        # ---------------------------------------ADVANCED USER OPTIONS--------------------------------------------
        # Create group box for advanced user options
        self.instantCollapsiblegroupBtn = ctk.ctkCollapsibleGroupBox()
        self.instantCollapsiblegroupBtn.title = "Advanced Options"
        self.layout.addWidget(self.instantCollapsiblegroupBtn)
        self.instantCollapsiblegroupBtn.collapsed = True
        self.instantFormLayout.addRow(self.instantCollapsiblegroupBtn)
        self.instantCGBFormLayout = qt.QFormLayout(self.instantCollapsiblegroupBtn)

        # Create radio buttons for triangle or quad meshing
        self.checkTR = qt.QRadioButton()
        self.checkTR.text = "Triangles (6/6)"
        self.checkTR.checked = True  # use triangle meshing by default
        self.instantCGBFormLayout.addRow("Orientation and Position Symmetry Type: ", self.checkTR)

        self.checkQD1 = qt.QRadioButton()
        self.checkQD1.text = "Quads (2/4)"
        self.instantCGBFormLayout.addRow("                                        ", self.checkQD1)

        self.checkQD2 = qt.QRadioButton()
        self.checkQD2.text = "Quads (4/4)"
        self.instantCGBFormLayout.addRow("                                        ", self.checkQD2)

        # Create check boxes for boolean values
        self.checkintrinsic = qt.QCheckBox()
        self.checkintrinsic.checked = False  # use extrinsic by default
        self.checkintrinsic.toolTip = ('If activated:' ' Measures smoothness directly on the surface instead of natural alignment to surface features ')
        self.checkintrinsic.stateChanged.connect(self.oncheckint)
        self.instantCGBFormLayout.addRow("Intrinsic: ", self.checkintrinsic)

        self.checkdominant = qt.QCheckBox()
        self.checkdominant.checked = False
        self.checkdominant.toolTip = ('If activated:' ' Generates a tri/quad dominant mesh instead of a pure tri/quad mesh ')
        self.checkdominant.stateChanged.connect(self.oncheckdom)
        self.instantCGBFormLayout.addRow("Dominant: ", self.checkdominant)

        self.checkdetermin = qt.QCheckBox()
        self.checkdetermin.checked = False
        self.checkdetermin.toolTip = ('If activated:' ' Prefers (slower) deterministic algorithms ')
        self.checkdetermin.stateChanged.connect(self.oncheckdet)
        self.instantCGBFormLayout.addRow("Deterministic: ", self.checkdetermin)

        # Create slider widget to adjust face count (triangle), prior vertex count (to change back, change -f in cmd to -v)
        self.vertSlider = ctk.ctkSliderWidget()
        self.vertSlider.minimum = 1000
        self.vertSlider.maximum = 10000
        self.vertSlider.setFixedWidth(400)
        self.vertSlider.value = 2800
        self.vertSlider.toolTip = ('What it changes:' ' Desired face count of the output mesh ')
        self.instantCGBFormLayout.addRow("Triangle count: ", self.vertSlider)

        # Create slider widget to adjust smoothing & ray tracing reprojection steps
        self.smoothraySlider = ctk.ctkSliderWidget()
        self.smoothraySlider.minimum = 0
        self.smoothraySlider.maximum = 10
        self.smoothraySlider.setFixedWidth(400)
        self.smoothraySlider.value = 2
        self.smoothraySlider.toolTip = ('What it changes:' ' Number of smoothing & ray tracing reprojection steps (default: 2) ')
        self.instantCGBFormLayout.addRow("Smoothing Steps: ", self.smoothraySlider)

        # Create slider widget to adjust Point cloud mode
        self.knnSlider = ctk.ctkSliderWidget()
        self.knnSlider.minimum = 5
        self.knnSlider.maximum = 20
        self.knnSlider.setFixedWidth(400)
        self.knnSlider.value = 10
        self.knnSlider.toolTip = ('Point cloud mode:' ' Number of adjacent points to consider (default: 10) ')
        self.instantCGBFormLayout.addRow("Adjacent Points: ", self.knnSlider)

        # Create slider widget to adjust Dihedral angle threshold
        self.angleSlider = ctk.ctkSliderWidget()
        self.angleSlider.minimum = -1
        self.angleSlider.maximum = 90
        self.angleSlider.setFixedWidth(400)
        self.angleSlider.value = -1
        self.angleSlider.toolTip = ('What it changes:' ' Dihedral angle threshold for creases, -1 means sharp creases ')
        self.instantCGBFormLayout.addRow("Crease Angle: ", self.angleSlider)

        # ---------------------------------------ROBUST QUAD/HEX-DOMINANT MESHING--------------------------------------------
        # Create collapsible Button for robust quad/hex-dominant meshing options
        self.quadhexCollapsibleBtn = ctk.ctkCollapsibleButton()
        self.quadhexCollapsibleBtn.text = "Robust Quad/Hex-dominant Meshing"
        self.layout.addWidget(self.quadhexCollapsibleBtn)
        self.quadhexCollapsibleBtn.collapsed = True
        self.quadhexFormLayout = qt.QFormLayout(self.quadhexCollapsibleBtn)
        self.quadhexCollapsibleBtn.connect('clicked(bool)', self.onQuadHexClick)

        # Create button to run the tool
        self.rmBtn = qt.QPushButton("Run")
        self.rmBtn.setFixedHeight(40)
        self.rmBtn.setFixedWidth(100)
        self.rmBtn.setStyleSheet("QPushButton{ background-color: DarkSeaGreen  }")
        self.rmBtn.toolTip = ('How to use:' ' Click the Run Button to start robust quad/hex-dominant meshing ')
        self.rmBtn.connect('clicked(bool)', self.onRmBtnClick)
        self.quadhexFormLayout.addRow(self.rmBtn, self.qhtimeLbl)

        # ---------------------------------------ADVANCED USER OPTIONS--------------------------------------------
        # Create group box for advanced user options
        self.robustCollapsiblegroupBtn = ctk.ctkCollapsibleGroupBox()
        self.robustCollapsiblegroupBtn.title = "Advanced Options"
        self.layout.addWidget(self.robustCollapsiblegroupBtn)
        self.robustCollapsiblegroupBtn.collapsed = True
        self.quadhexFormLayout.addRow(self.robustCollapsiblegroupBtn)
        self.robustCGBFormLayout = qt.QFormLayout(self.robustCollapsiblegroupBtn)

        # Create radio buttons to adjust dimension
        self.checkdim2 = qt.QRadioButton()
        self.checkdim2.checked = True  # use dimension 2 by default
        self.checkdim2.text = "2"
        self.robustCGBFormLayout.addRow("Dimension: ", self.checkdim2)

        # Create slider widget to adjust scale
        self.scaleSlider = ctk.ctkSliderWidget()
        self.scaleSlider.minimum = 2
        self.scaleSlider.maximum = 10
        self.scaleSlider.setFixedWidth(400)
        self.scaleSlider.value = 3
        self.robustCGBFormLayout.addRow("Scale: ", self.scaleSlider)

        # Create slider widget to adjust smooth iterator
        self.smoothSlider = ctk.ctkSliderWidget()
        self.smoothSlider.minimum = 5
        self.smoothSlider.maximum = 20
        self.smoothSlider.setFixedWidth(400)
        self.smoothSlider.value = 10
        self.robustCGBFormLayout.addRow("Smoothing iteration count: ", self.smoothSlider)

    # Run Instant-Meshing 
    def onImBtnClick(self):
        self.imBtn.setText("...please wait")
        self.imBtn.setStyleSheet("QPushButton{ background-color: red  }")
        slicer.app.processEvents()
        nodes = slicer.util.getNodesByClass('vtkMRMLModelNode')

        # start time is recorded
        self.stm = time.time()

        # Call Variables from advanced user option sliders
        vertex = str(int(self.vertSlider.value))
        smooth = str(int(self.smoothraySlider.value))
        knn = str(int(self.knnSlider.value))
        angle = str(int(self.angleSlider.value))
        # Check radio buttons for triangle or quad meshing
        if (self.checkQD1.isChecked() == True):
            posy = " -p 4 "
            rosy = " -r 2"
        elif (self.checkQD2.isChecked() == True):
            posy = " -p 4 "
            rosy = " -r 4"
        else:
            posy = " -p 6 "
            rosy = " -r 6"
        # endif

        inputNode = self.inputSelectorCoBx.currentNode()                               # load current node
        # run Instant-Meshing
        self.logic.runIM( inputNode, vertex, smooth, knn, angle, posy, rosy)

        # Reset Run Button
        self.imBtn.setText("Run")
        self.imBtn.setStyleSheet("QPushButton{ background-color: DarkSeaGreen  }")
        slicer.app.processEvents()

        # Update time label
        self.etm = time.time()
        tm = self.etm - self.stm
        self.imtimeLbl.setText("Time: "+str(tm)+"seconds")
        # print(self.CPos)
        slicer.app.processEvents()


    # Run Robust Quad/Hex-dominant Meshing
    def onRmBtnClick(self):
        self.rmBtn.setText("...please wait")
        self.rmBtn.setStyleSheet("QPushButton{ background-color: red  }")
        slicer.app.processEvents()

        # start time is recorded
        self.stm = time.time()

        # Call Variables from advanced user option sliders
        scale = str(int(self.scaleSlider.value))
        smooth = str(int(self.smoothSlider.value))

        # Check radio buttons for dimension variable
        if (self.checkdim2.isChecked() == True):
            dimension = "2"
        else:
            dimension = "3"
        # endif

        inputNode = self.inputSelectorCoBx.currentNode()                               # load current node
        # run Robust Quad/Hex-dominant Meshing
        self.logic.runRM(inputNode, scale, smooth, dimension)

        # Reset Run Button
        self.rmBtn.setText("Run")
        self.rmBtn.setStyleSheet("QPushButton{ background-color: DarkSeaGreen  }")
        slicer.app.processEvents()
        # Update time label
        self.etm = time.time()
        tm = self.etm - self.stm
        self.qhtimeLbl.setText("Time: "+str(tm)+"  seconds")
        # print(self.CPos)
        slicer.app.processEvents()


    # --------------------------------------------------------------------------------------------
    #                        Extra User Options
    # --------------------------------------------------------------------------------------------
    def onShowBtnClick(self):
        self.inputNode = self.inputSelectorCoBx.currentNode()
        self.logic.displayEnd(self.inputNode)

    def onInputBtnClick(self):
        self.inputNode = self.inputSelectorCoBx.currentNode()
        self.logic.resultNode.SetDisplayVisibility(0)
        self.inputNode.SetDisplayVisibility(1)

    def onQuadHexClick(self):
        if self.quadhexCollapsibleBtn.collapsed == False:
            # collapse instant meshing option
            self.instantCollapsibleBtn.collapsed = True
        # endif

    def onInstantClick(self):
        if self.instantCollapsibleBtn.collapsed == False:
            # collapse instant meshing option
            self.quadhexCollapsibleBtn.collapsed = True
        # endif

    def oncheckint(self):
        if self.checkintrinsic.checked:
            self.logic.intrinsic = " -i "
        else:
            self.logic.intrinsic = ""
        # endif

    def oncheckdom(self):
        if self.checkdominant.checked:
            self.logic.dominant = " -D "
        else:
            self.logic.dominant = ""
        # endif

    def oncheckdet(self):
        if self.checkdetermin.checked:
            self.logic.determin = " -d "
        else:
            self.logic.determin = ""
        # endif

    def onCheckShowNormalsChkBx(self):
        self.logic.showNormals(self.checkshowNormals.checked)



#===================================================================
#                           Logic Class
#===================================================================
class SlicerRemeshingLogic(ScriptedLoadableModuleTest):

    def setGlobalVariables(self):
        # Declare global labels
        # self.posy = " -p 6 "
        # self.rosy = " -r 6"
        # self.dimension = "2"
        self.intrinsic = ""
        self.dominant = ""
        self.determin = ""
        # self.showNormals = ""

        # --------------------------------------------------------------------------------------------
        #                       Default Settings
        # --------------------------------------------------------------------------------------------
        print("Default Settings: ")
        # Set default Remeshing Tools location (home/<user>/Remeshing)

        # For extension 
        self.vissimPath = os.path.join( expanduser("~"),"VisSimTools")
        if not os.path.exists(self.vissimPath):
           os.mkdir(self.vissimPath)
        #endif
        self.outputPath = os.path.join(self.vissimPath, 'outputs')
        if not os.path.exists(self.outputPath):
           os.mkdir(self.outputPath)
        #endif            
        self.remeshPath = os.path.dirname(os.path.abspath(__file__))
        self.remeshBinPath =os.path.abspath(os.path.join(self.remeshPath, os.pardir))      
        self.remeshBinPathIM = os.path.join(self.remeshBinPath , "instantMeshes")
        self.remeshBinPathRM = os.path.join(self.remeshBinPath , "rhdm")
        #print(self.remeshBinPathIM)
        
        # for local testing
        if not os.path.exists(self.remeshBinPathRM):
           # for local testing
           self.remeshPath = self.vissimPath
           s = self.remeshPath + ",sw,ReMeshing,instantMeshes"
           self.remeshBinPathIM  = os.path.join(*s.split(","))
           s = self.remeshPath + ",w,ReMeshing,rhdm"
           self.remeshBinPathRM  = os.path.join(*s.split(","))

        elif not os.path.exists(self.remeshBinPathRM): 
           print("binaries are not found!") #os.makedirs(self.remeshBinPath)        
        #endif
        #print("      Remeshing folder: " + self.remeshPath)        
        #self.remeshingWebLink = ("https://mtixnat.uni-koblenz.de/owncloud/index.php/s/BH0o4TkYtMEQlS5/download")

        
        self.noOutput = " >> /dev/null"
        self.winOS = 0
        # windows
        if platform.system() == 'Windows':
            self.remeshBinPathIM =  os.path.join(self.remeshBinPath , "instantMeshes.exe")
            self.remeshBinPathRM =  os.path.join(self.remeshBinPath , "rhdm.exe")
            self.noOutput = " > nul"
            self.winOS = 1
        # endif

        if not os.path.exists(self.outputPath):
            os.makedirs(self.outputPath)
        print("      Output folder : " + self.outputPath)
        # endif
    #endef

    def checkBinaries(self):
        # Check if Remeshing binaries exists or build it
        if isfile(self.remeshBinPathIM.strip()):
            print("      Remeshing binaries are found in " + self.remeshBinPath)
        else:
            print("Remeshing binaries are NOT found...")
        # endif
    #endef

    # ===========================================================================================
    #                       run Instant-Meshing
    # --------------------------------------------------------------------------------------------
    def runIM(self, inputNode, vertex, smooth, knn, angle, posy, rosy):
        # Remove old results
        nodes = slicer.util.getNodesByClass('vtkMRMLModelNode')
        for f in nodes:
           if ("instant" in f.GetName() ):
                    print(" .... removing " + f.GetName())
                    slicer.mrmlScene.RemoveNode(f)
                   #endif
        #endfor

            
        # Output Path for remeshed file
        
        self.resPath = os.path.join(self.outputPath , "instantMeshing.obj")

        # Call method to save node as .obj file, define inputPath and extract namebase for remeshed file
        [self.inputNode, self.inputPath, self.segNm] = self.stl2obj(inputNode)

        print("================= Instant-Meshing =====================")
        #TODO:  Add parameters descriptions:
        # Call Instant-Meshing
        Cmd = self.remeshBinPathIM + " -o " + self.resPath + " -f " + vertex + " -S " + smooth + " -k " + knn + " -c " + angle + rosy + posy + self.intrinsic + self.dominant + self.determin + self.inputPath
        print("executing: " + Cmd)
        c = os.system(Cmd)

        # Call method to save node as .stl file, reload it and delete .obj nodes
        [self.resultNode, self.resPath] = self.obj2stl("instant")

        # Call method to remove unneeded .obj and .mtl files
        self.removeTempFiles("instant")

        print("All taks are done !!! ")

        # show remeshed model
        print("Instant-Meshing result is saved as: " + self.resultNode.GetStorageNode().GetFileName())
        self.displayEnd(self.resultNode)


    # ===========================================================================================
    #                       run Robust Quad/Hex-dominant Meshing
    # --------------------------------------------------------------------------------------------
    def runRM(self, inputNode, scale, smooth, dimension):

        # Remove old results
        nodes = slicer.util.getNodesByClass('vtkMRMLModelNode')
        for f in nodes:
           if ("robust" in f.GetName() ):
                    print(" .... removing " + f.GetName())
                    slicer.mrmlScene.RemoveNode(f)
                   #endif
        #endfor

        # Path           
        self.resPath = os.path.join(self.outputPath , "robQuadHexDomMeshing.obj")

        # Call method to save node as .obj file, define inputPath and extract namebase for remeshed file
        [self.inputNode, self.inputPath, self.segNm] = self.stl2obj(inputNode)

        print("================= Robust Quad/Hex-dominant-Meshing =====================")
        #TODO:  Add parameters descriptions:

        # Call Rob Quad/Hex-Dom-Meshing
        Cmd = self.remeshBinPathRM + " -b " + "-i " + self.inputPath + " -o " + self.resPath + " -d " + dimension + " -s " + scale + " -S " + smooth
        print("executing: " + Cmd)
        c = os.system(Cmd)

        # Call method to save node as .stl file, reload it and delete .obj nodes
        [self.resultNode, self.resPath] = self.obj2stl("robust")

        # Call method to remove unneeded .obj and .mtl files
        self.removeTempFiles("robust")

        print("All taks are done !!! ")

        # show remeshed model
        print("Robust Quad/Hex-dominant-Meshing result is saved as: " + self.resultNode.GetStorageNode().GetFileName())
        self.displayEnd(self.resultNode)


    # --------------------------------------------------------------------------------------------
    #                        Save and Load .obj and .stl files
    # --------------------------------------------------------------------------------------------
    # convert stl to obj format to be compitable with the external tools
    def stl2obj(self, inputNode):
        # get the file path of the node
        self.segName = inputNode.GetStorageNode().GetFileName()       
        # get base name of file for result file name later
        self.segNm = basename(os.path.splitext(self.segName)[0])
        # load copy of input as temporary node, otherwise input node turns to .obj file
        [success, self.copyNode] = slicer.util.loadModel(self.segName, returnNode=True)
        # define name of input .obj file for remeshing
         
        self.inputPath = os.path.join(self.outputPath , "inputSegmentation.obj")
        # save the copy node as .obj with the new name
        slicer.util.saveNode(self.copyNode, self.inputPath)
        print("Segmentation is saved as .obj in: " + self.inputPath)
        # remove copy node, not needed anymore
        slicer.mrmlScene.RemoveNode(self.copyNode)
        # set input node as invisible, to see remeshed model only
        inputNode.SetDisplayVisibility(0)
        return inputNode, self.inputPath, self.segNm

    def obj2stl(self, mesh):
        # define name of remeshed .stl file (instant meshing)
        if mesh == "instant":
            self.resSeg = os.path.join(self.outputPath , self.segNm + "_IM.stl")   
        #endif
        # define name of remeshed .stl file (robust meshing)
        if mesh == "robust":
            self.resSeg = os.path.join(self.outputPath , self.segNm + "_RM.stl")  
        # endif
        # load remeshed file as temporary node
        [success, self.tempNode] = slicer.util.loadModel(self.resPath, returnNode=True)  
        # save remeshed temporary node under new filename and type
        slicer.util.saveNode(self.tempNode, self.resSeg)
        # delete temporary node
        slicer.mrmlScene.RemoveNode(self.tempNode)
        # load remeshed .stl file as result node
        [success, self.resultNode] = slicer.util.loadModel(self.resSeg, returnNode=True)  
        return self.resultNode, self.resPath

    # --------------------------------------------------------------------------------------------
    #                        Remove temp files
    # --------------------------------------------------------------------------------------------
    def removeTempFiles(self, mesh):
        if mesh == "robust":            
            rmflag = 'rm ' + os.path.join(self.outputPath , "robQuadHexDomMeshing.objtri.obj_V_flag.txt")
            rmsurout = 'rm ' + self.resPath + "_surout.obj"
            os.system(rmflag)
            os.system(rmsurout)
        # endif
        rmobj = 'rm ' + self.inputPath
        rmmtl = 'rm ' + os.path.join(self.outputPath , "inputSegmentation.mtl")
        rmmeshobj = 'rm ' + self.resPath
        os.system(rmobj)
        os.system(rmmtl)
        os.system(rmmeshobj)

    def computeNormals(self, inputNode):
        # compute normals
        model = inputNode
        arrow = vtk.vtkArrowSource()
        arrow.Update()
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(model.GetPolyDataConnection())
        normals.ComputePointNormalsOff()
        normals.ComputeCellNormalsOn()
        normals.SplittingOn()
        normals.FlipNormalsOff()
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.Update()
        centers = vtk.vtkCellCenters()
        centers.SetInputConnection(normals.GetOutputPort())
        glyph = vtk.vtkGlyph3D()
        glyph.SetInputData(normals.GetOutput())
        glyph.SetInputConnection(centers.GetOutputPort())
        glyph.SetSourceData(arrow.GetOutput())
        glyph.SetVectorModeToUseNormal()
        glyph.SetScaleModeToScaleByVector()
        glyph.SetScaleFactor(1)
        glyph.OrientOn()
        glyph.Update()
        slicer.modules.models.logic().AddModel(glyph.GetOutput())
        normalsNode = slicer.util.getNode('Model')
        return normalsNode

    # --------------------------------------------------------------------------------------------
    #                        Display at the end of segmentation
    # --------------------------------------------------------------------------------------------
    def displayEnd(self, inputNode):

        # center 3d view
        layoutManager = slicer.app.layoutManager()
        layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUp3DView)
        threeDWidget = layoutManager.threeDWidget(0)
        threeDView = threeDWidget.threeDView()
        threeDView.resetFocalPoint()
        n = inputNode.GetDisplayNode()
        n.SetEdgeVisibility(1)
        n.SetEdgeColor(0, 0, 0)

    # shows the normals on the mesh
    def showNormals(self, show):
        normalsFound = 0
        nodes = slicer.util.getNodesByClass('vtkMRMLModelNode')
        for f in nodes:
            if 'Model' in f.GetName():
                normalsFound = 1
                self.normalsNode = f
                break
            # endif
        # endfor
        if show:
            if not normalsFound:
                self.normalsNode = self.computeNormals(self.resultNode)
            # endif
            self.normalsNode.GetDisplayNode().SetVisibility(1)
        else:
            self.normalsNode.GetDisplayNode().SetVisibility(0)
        # endif

#===================================================================
#                           Test Class
#===================================================================
class SlicerRemeshingTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    # set up
    def setUp(self):
        slicer.mrmlScene.Clear(0)
        self.logic = SlicerRemeshingLogic()
        self.logic.setGlobalVariables()
        self.logic.checkBinaries()
    #enddef 
    
    def runTest(self):
        self.setUp()
        try:         
           import urllib           
           imFnm   = os.path.join(self.logic.vissimPath ,"cochlea.stl")
           rmFnm   = os.path.join(self.logic.vissimPath ,"cochlea_IM.stl")
           inputModelIMWeb = "https://cloud.uni-koblenz-landau.de/s/kXzg4zR9skokckB/download"
           inputModelRMWeb = "https://cloud.uni-koblenz-landau.de/s/mM6FaKxZAsHQJ8P/download"
           urllib.urlretrieve (inputModelIMWeb ,imFnm )
           #urllib.urlretrieve (inputModelRMWeb ,rmFnm )
           print("Downloading complete ...")
 
        except Exception as e:
                  print("Error: can not download sample files  ...")
                  print(e)   
                  return -1
        #end try-except 

        [successIM, self.inputModelIMNode] = slicer.util.loadModel( imFnm, returnNode=True)
        #[successRM, self.inputModelRMNode] = slicer.util.loadModel( rmFnm, returnNode=True)

        #if not (successIM and successRM) :
        if not (successIM) :
            print("Error: can not load sample file...")
            return -1
        else:
            print("Sample model is loaded ...")
        #endif 

        #--------------------------- Test instant meshing
        self.stm=time.time()

        self.testIM()

        self.etm=time.time()
        tm=self.etm - self.stm
        print("Time for instant meshing test: "+str(tm)+"  seconds")

        #--------------------------- Test robust meshing
        self.stm=time.time()

        self.testRM()
    
        self.etm=time.time()
        tm=self.etm - self.stm
        print("Time for robust meshing test: "+str(tm)+"  seconds")
    #enddef
    
    # Instant-Meshing test case
    def testIM(self):
        self.delayDisplay("Instant meshing test is started , please wait ...")

        vertex = "2800"
        smooth = "2"
        knn    = "10"
        angle  = "-1"
        posy   = " -p 6 "
        rosy   = " -r 6"
        self.logic.runIM( self.inputModelIMNode, vertex, smooth, knn, angle, posy, rosy)

        self.delayDisplay("Instant-Meshing test passed!")
    #enddef

    # Robust Quad/Hex-dominant Meshing test case
    def testRM(self):
        self.delayDisplay("Robust meshing test is started , please wait ...")
        
        self.inputModelRMNode = slicer.util.getNode('cochlea_IM')
        scale     = "3"
        smooth    = "10"
        dimension = "2" 
        self.logic.runRM(self.inputModelRMNode, scale, smooth, dimension)

        self.delayDisplay("Robust Quad/Hex-dominant Meshing test passed!")
    #enddef