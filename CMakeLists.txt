cmake_minimum_required(VERSION 3.5)

project(SlicerMeshing)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.uni-koblenz-landau.de/en/campus-koblenz/fb4/icv/vissim")
set(EXTENSION_CATEGORY "VisSimTools")
set(EXTENSION_CONTRIBUTORS "")
set(EXTENSION_DESCRIPTION "Interface for Instant-Meshing and Robust Quad/Hex-dominant Meshing to remesh segmentations.")
# set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/SlicerRemeshing.png")
# set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/SlicerRemeshing/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any
set(EXTENSION_BUILD_SUBDIRECTORY inner-build)

set(SUPERBUILD_TOPLEVEL_PROJECT inner)

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})
mark_as_superbuild(Slicer_DIR)

find_package(Git REQUIRED)
mark_as_superbuild(GIT_EXECUTABLE)

#-----------------------------------------------------------------------------
# SuperBuild setup
option(${EXTENSION_NAME}_SUPERBUILD "Build ${EXTENSION_NAME} and the projects it depends on." ON)
mark_as_advanced(${EXTENSION_NAME}_SUPERBUILD)
if(${EXTENSION_NAME}_SUPERBUILD)
  include("${CMAKE_CURRENT_SOURCE_DIR}/SuperBuild.cmake")
  return()
endif()

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SlicerRemeshing)
## NEXT_MODULE

#-----------------------------------------------------------------------------
#  install directory, install project name, install component, and install subdirectory.
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${instantMeshes_DIR};instantMeshes;RuntimeLibraries;/")
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${rhdm_DIR};rhdm;RuntimeLibraries;/")
set(CPACK_INSTALL_CMAKE_PROJECTS "${CPACK_INSTALL_CMAKE_PROJECTS};${CMAKE_BINARY_DIR};${EXTENSION_NAME};ALL;/")
MESSAGE(STATUS "CPACK_INSTALL_CMAKE_PROJECTS = ${CPACK_INSTALL_CMAKE_PROJECTS}") 

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})

