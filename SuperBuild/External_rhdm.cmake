
set(proj rhdm)

# Set dependency list
set(${proj}_DEPENDS   ""   )

# Include dependent projects if any
ExternalProject_Include_Dependencies(${proj} PROJECT_VAR proj)

if(${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})
  message(FATAL_ERROR "Enabling ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj} is not supported !")
endif()

# Sanity checks
if(DEFINED rhdm_DIR AND NOT EXISTS ${rhdm_DIR})
  message(FATAL_ERROR "rhdmM_DIR [${rhdm_DIR}] variable is defined but corresponds to nonexistent directory")
endif()

if(NOT DEFINED ${proj}_DIR AND NOT ${CMAKE_PROJECT_NAME}_USE_SYSTEM_${proj})

  if(NOT DEFINED git_protocol)
    set(git_protocol "git")
  endif()

  set(${proj}_INSTALL_DIR ${CMAKE_BINARY_DIR}/${proj}-install)
  set(${proj}_DIR ${CMAKE_BINARY_DIR}/${proj}-build)

  ExternalProject_Add(
    ${proj}
    ${${proj}_EP_ARGS}
    SOURCE_DIR ${CMAKE_BINARY_DIR}/${proj}
    #SOURCE_SUBDIR src # requires CMake 3.7 or later
    BINARY_DIR ${proj}-build
    INSTALL_DIR ${${proj}_INSTALL_DIR}
    GIT_REPOSITORY "https://github.com/MedicalImageAnalysisTutorials/rhdm"
    CMAKE_CACHE_ARGS
      -DGIT_EXECUTABLE:STRING=${GIT_EXECUTABLE}
      -DITK_DIR:STRING=${ITK_DIR}
      -DBUILD_CLI:BOOL=ON
      -DCMAKE_CXX_COMPILER:FILEPATH=${CMAKE_CXX_COMPILER}
      -DCMAKE_CXX_FLAGS:STRING=${ep_common_cxx_flags}
      -DCMAKE_C_COMPILER:FILEPATH=${CMAKE_C_COMPILER}
      -DCMAKE_C_FLAGS:STRING=${ep_common_c_flags}
      -DCMAKE_CXX_STANDARD:STRING=11 #${CMAKE_CXX_STANDARD}
      -DCMAKE_CXX_STANDARD_REQUIRED:BOOL=${CMAKE_CXX_STANDARD_REQUIRED}
      -DCMAKE_CXX_EXTENSIONS:BOOL=${CMAKE_CXX_EXTENSIONS}
      -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
      -DCMAKE_BUILD_TYPE:STRING=${CMAKE_BUILD_TYPE}
      -DBUILD_TESTING:BOOL=OFF
      -DCMAKE_MACOSX_RPATH:BOOL=0
      # location of build outputs in the build tree
      -DCMAKE_RUNTIME_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${Slicer_THIRDPARTY_BIN_DIR}
      -DCMAKE_LIBRARY_OUTPUT_DIRECTORY:PATH=${CMAKE_BINARY_DIR}/${Slicer_THIRDPARTY_LIB_DIR}
      -DCMAKE_ARCHIVE_OUTPUT_DIRECTORY:PATH=${CMAKE_ARCHIVE_OUTPUT_DIRECTORY}
      # location of build outputs in the installation folder
      -Drhdm_RUNTIME_DIR:STRING=${Slicer_INSTALL_THIRDPARTY_LIB_DIR}
    #--Build step-----------------
    #--Install step-----------------
    # Don't perform installation at the end of the build
    INSTALL_COMMAND ""
    DEPENDS
      ${${proj}_DEPENDS}
    )
else()
  ExternalProject_Add_Empty(${proj} DEPENDS ${${proj}_DEPENDS})
endif()
mark_as_superbuild(${proj}_DIR:PATH)
