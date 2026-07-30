cmake_minimum_required(VERSION 3.14)
project(hve_core C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Strict warnings
if(CMAKE_C_COMPILER_ID STREQUAL "GNU" OR CMAKE_C_COMPILER_ID STREQUAL "Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
elseif(MSVC)
    add_compile_options(/W4 /WX)
endif()

# Header-only library (interface target)
add_library(hve_core INTERFACE)
target_include_directories(hve_core INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Exhaustive test executable
add_executable(hve_exhaustive_test hve_test.c)
target_link_libraries(hve_exhaustive_test PRIVATE hve_core)

# CTest integration
enable_testing()
add_test(NAME hve_exhaustive_tests COMMAND hve_exhaustive_test)
