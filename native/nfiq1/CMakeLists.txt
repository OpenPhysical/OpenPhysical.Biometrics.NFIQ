# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (c) 2026 Mistial Developer

cmake_minimum_required(VERSION 3.20)
project(openphysical_nfiq1 VERSION 1.0 LANGUAGES C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_VISIBILITY_PRESET hidden)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(OP_NBIS_SANITIZERS "" CACHE STRING "Comma-separated Clang/GCC sanitizers: address, undefined, or both")
if(OP_NBIS_SANITIZERS AND NOT CMAKE_C_COMPILER_ID MATCHES "Clang|GNU")
  message(FATAL_ERROR "Sanitizers require Clang or GCC")
endif()
set(MINDTCT
 upstream/mindtct/src/lib/mindtct/ridges.c
 upstream/mindtct/src/lib/mindtct/log.c
 upstream/mindtct/src/lib/mindtct/block.c
 upstream/mindtct/src/lib/mindtct/util.c
 upstream/mindtct/src/lib/mindtct/contour.c
 upstream/mindtct/src/lib/mindtct/loop.c
 upstream/mindtct/src/lib/mindtct/link.c
 upstream/mindtct/src/lib/mindtct/init.c
 upstream/mindtct/src/lib/mindtct/sort.c
 upstream/mindtct/src/lib/mindtct/maps.c
 upstream/mindtct/src/lib/mindtct/line.c
 upstream/mindtct/src/lib/mindtct/getmin.c
 upstream/mindtct/src/lib/mindtct/dft.c
 upstream/mindtct/src/lib/mindtct/morph.c
 upstream/mindtct/src/lib/mindtct/free.c
 upstream/mindtct/src/lib/mindtct/mytime.c
 upstream/mindtct/src/lib/mindtct/xytreps.c
 upstream/mindtct/src/lib/mindtct/binar.c
 upstream/mindtct/src/lib/mindtct/imgutil.c
 upstream/mindtct/src/lib/mindtct/isempty.c
 upstream/mindtct/src/lib/mindtct/matchpat.c
 upstream/mindtct/src/lib/mindtct/remove.c
 upstream/mindtct/src/lib/mindtct/chaincod.c
 upstream/mindtct/src/lib/mindtct/quality.c
 upstream/mindtct/src/lib/mindtct/minutia.c
 upstream/mindtct/src/lib/mindtct/detect.c
 upstream/mindtct/src/lib/mindtct/globals.c
 upstream/mindtct/src/lib/mindtct/shape.c
)
# Verify provenance even when configuring CMake directly rather than through Python.
find_package(Python3 REQUIRED COMPONENTS Interpreter)
execute_process(COMMAND "${Python3_EXECUTABLE}"
  "${CMAKE_CURRENT_SOURCE_DIR}/../../scripts/source_provenance.py"
  "${CMAKE_CURRENT_SOURCE_DIR}" COMMAND_ERROR_IS_FATAL ANY)

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/allocator-provenance.json" ALLOCATOR_PROVENANCE)
foreach(NAME op_alloc.c op_alloc.h)
  string(JSON EXPECTED GET "${ALLOCATOR_PROVENANCE}" files "${NAME}" sha256)
  file(SHA256 "${CMAKE_CURRENT_SOURCE_DIR}/${NAME}" ACTUAL)
  if(NOT ACTUAL STREQUAL EXPECTED)
    message(FATAL_ERROR "Vendored allocator checksum mismatch: ${NAME}. Update from its canonical NBIS source.")
  endif()
endforeach()

# Fail closed if an upstream change makes any adaptation ambiguous or inapplicable.
function(op_replace_once VARIABLE BEFORE AFTER)
  set(CONTENT "${${VARIABLE}}")
  string(FIND "${CONTENT}" "${BEFORE}" POSITION)
  if(POSITION LESS 0)
    message(FATAL_ERROR "NBIS adaptation source pattern is missing: ${BEFORE}")
  endif()
  string(LENGTH "${BEFORE}" LENGTH)
  math(EXPR NEXT "${POSITION} + ${LENGTH}")
  string(SUBSTRING "${CONTENT}" ${NEXT} -1 REMAINDER)
  string(FIND "${REMAINDER}" "${BEFORE}" DUPLICATE)
  if(NOT DUPLICATE LESS 0)
    message(FATAL_ERROR "NBIS adaptation source pattern is ambiguous: ${BEFORE}")
  endif()
  string(REPLACE "${BEFORE}" "${AFTER}" CONTENT "${CONTENT}")
  set(${VARIABLE} "${CONTENT}" PARENT_SCOPE)
endfunction()
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/upstream/mindtct/src/lib/mindtct/minutia.c" MINUTIA)
op_replace_once(MINUTIA "exit(-430);" "return(-430);")
op_replace_once(MINUTIA "exit(-431);" "free(minutiae); return(-431);")
op_replace_once(MINUTIA "minutiae->alloc += incr_minutiae;\n   minutiae->list = (MINUTIA **)realloc(minutiae->list,\n                                     minutiae->alloc * sizeof(MINUTIA *));\n   if(minutiae->list == (MINUTIA **)NULL){" "MINUTIA **new_list = (MINUTIA **)realloc(minutiae->list, (minutiae->alloc + incr_minutiae) * sizeof(MINUTIA *));\n   if(new_list == (MINUTIA **)NULL){")
op_replace_once(MINUTIA "exit(-432);" "return(-432);")
# Install the successful realloc only after its failure check.
op_replace_once(MINUTIA "return(-432);\n   }\n\n   return(0);" "return(-432);\n   }\n   minutiae->list = new_list;\n   minutiae->alloc += incr_minutiae;\n   return(0);")
if(MINUTIA MATCHES "exit\\(")
  message(FATAL_ERROR "The allocation error patch did not remove all process exits")
endif()
file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/minutia.c" "${MINUTIA}")
if(WIN32)
 file(READ "${CMAKE_CURRENT_SOURCE_DIR}/upstream/mindtct/include/mytime.h" MYTIME)
 string(REPLACE "#include <sys/times.h>" "#include <time.h>" MYTIME "${MYTIME}")
 file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/mytime.h" "${MYTIME}")
 file(READ "${CMAKE_CURRENT_SOURCE_DIR}/upstream/commonnbis/include/util.h" UTIL_HEADER)
 string(REPLACE "#include <sys/times.h>" "#include <time.h>" UTIL_HEADER "${UTIL_HEADER}")
 file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/util.h" "${UTIL_HEADER}")
endif()
list(FILTER MINDTCT EXCLUDE REGEX "/minutia.c$")
configure_file(upstream/an2k/include/an2k.h.src an2k.h COPYONLY)
file(GLOB BLAS CONFIGURE_DEPENDS upstream/commonnbis/src/lib/cblas/*.c)
set(MLP upstream/pcasys/src/lib/mlp)
set(SOURCES ${MINDTCT} "${CMAKE_CURRENT_BINARY_DIR}/minutia.c"
 upstream/commonnbis/src/lib/util/bres.c upstream/nfiq/src/lib/nfiq/nfiq.c
 upstream/nfiq/src/lib/nfiq/nfiqgbls.c upstream/nfiq/src/lib/nfiq/znorm.c
 ${MLP}/runmlp.c ${MLP}/acsmaps.c ${MLP}/acs.c ${MLP}/mlpcla.c upstream/commonnbis/src/lib/util/memalloc.c upstream/commonnbis/src/lib/util/ssxstats.c ${BLAS})
set_source_files_properties(${SOURCES} PROPERTIES COMPILE_OPTIONS "-include;${CMAKE_CURRENT_SOURCE_DIR}/op_alloc.h")
add_library(openphysical_nfiq1 SHARED op_nfiq1.c op_alloc.c ${SOURCES})
set_source_files_properties(op_nfiq1.c op_alloc.c PROPERTIES COMPILE_OPTIONS "-Wall;-Wextra;-Werror")
target_include_directories(openphysical_nfiq1 PRIVATE "${CMAKE_CURRENT_BINARY_DIR}"
 upstream/mindtct/include upstream/commonnbis/include upstream/nfiq/include upstream/pcasys/include)
if(WIN32)
 set_target_properties(openphysical_nfiq1 PROPERTIES PREFIX "")
 target_compile_definitions(openphysical_nfiq1 PRIVATE _CRT_SECURE_NO_WARNINGS _USE_MATH_DEFINES WIN32_LEAN_AND_MEAN NOMINMAX)
else()
 find_package(Threads REQUIRED)
 target_link_libraries(openphysical_nfiq1 PRIVATE m Threads::Threads)
endif()
if(OP_NBIS_SANITIZERS)
 target_compile_options(openphysical_nfiq1 PRIVATE -fsanitize=${OP_NBIS_SANITIZERS} -fno-omit-frame-pointer)
 target_link_options(openphysical_nfiq1 PRIVATE -fsanitize=${OP_NBIS_SANITIZERS})
endif()
include(CTest)
if(BUILD_TESTING)
 target_compile_definitions(openphysical_nfiq1 PRIVATE OP_NBIS_TESTING)
 add_executable(nfiq1_tests ../../tests/native/test_nfiq1.c ../../tests/native/munit/munit.c)
 target_include_directories(nfiq1_tests PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}" ../../tests/native/munit)
 target_compile_definitions(nfiq1_tests PRIVATE OP_NBIS_TESTING NFIQ_FIXTURES="${CMAKE_CURRENT_SOURCE_DIR}/../../tests/fixtures")
 target_link_libraries(nfiq1_tests PRIVATE openphysical_nfiq1)
 if(OP_NBIS_SANITIZERS)
  target_compile_options(nfiq1_tests PRIVATE -fsanitize=${OP_NBIS_SANITIZERS} -fno-omit-frame-pointer)
  target_link_options(nfiq1_tests PRIVATE -fsanitize=${OP_NBIS_SANITIZERS})
 endif()
 if(WIN32)
  add_test(NAME nfiq1_tests COMMAND nfiq1_tests)
 else()
  add_test(NAME nfiq1_tests COMMAND nfiq1_tests --no-fork)
 endif()
else()
 install(TARGETS openphysical_nfiq1 RUNTIME DESTINATION . LIBRARY DESTINATION .)
endif()
