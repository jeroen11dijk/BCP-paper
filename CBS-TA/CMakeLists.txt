cmake_minimum_required(VERSION 3.5)

project(libMultiRobotPlanning)

find_package(Boost 1.58 REQUIRED COMPONENTS program_options)
find_package(PkgConfig)
pkg_check_modules(YamlCpp yaml-cpp)

# check if Doxygen is installed
find_package(Doxygen)

if (DOXYGEN_FOUND)
  # set input and output files
  set(DOXYGEN_IN ${CMAKE_CURRENT_SOURCE_DIR}/doc/Doxyfile.in)
  set(DOXYGEN_OUT ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile)

  # request to configure the file
  configure_file(${DOXYGEN_IN} ${DOXYGEN_OUT} @ONLY)
  message("Doxygen build started")

  # note the option ALL which allows to build the docs together with the application
  add_custom_target( docs
    COMMAND ${DOXYGEN_EXECUTABLE} ${DOXYGEN_OUT}
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    COMMENT "Generating API documentation with Doxygen"
    VERBATIM )
else (DOXYGEN_FOUND)
  message("Doxygen need to be installed to generate the doxygen documentation")
endif (DOXYGEN_FOUND)

# clang-tidy target (linter & static code analysis)
add_custom_target(clang-tidy
  COMMAND CMAKE_EXPORT_COMPILE_COMMANDS=ON run-clang-tidy ${CMAKE_CURRENT_SOURCE_DIR})

# clang-format
set(ALL_SOURCE_FILES
  ${CMAKE_CURRENT_SOURCE_DIR}/include/libMultiRobotPlanning/cbs_ta.hpp
  ${CMAKE_CURRENT_SOURCE_DIR}/include/libMultiRobotPlanning/next_best_assignment.hpp
  ${CMAKE_CURRENT_SOURCE_DIR}/example/cbs_ta.cppzed_sipp.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/example/next_best_assignment.cpp
)

add_custom_target(clang-format
  COMMAND clang-format -i ${ALL_SOURCE_FILES}
)

# tests
add_custom_target(run-test
  COMMAND python3 -m unittest discover -s ${CMAKE_CURRENT_SOURCE_DIR}/test
)

add_custom_target(everything
  DEPENDS clang-format clang-tidy docs run-test
)

# Enable C++14 and warnings
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_FLAGS  "${CMAKE_CXX_FLAGS} -Wall -Wextra")

# Creates compile database used by clang-tidy.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include_directories(
  include
)

# Examples

## cbs_ta
add_executable(cbs_ta
  example/cbs_ta.cpp
)
target_link_libraries(cbs_ta
  ${Boost_LIBRARIES}
  yaml-cpp
)