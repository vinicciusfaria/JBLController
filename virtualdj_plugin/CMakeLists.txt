cmake_minimum_required(VERSION 3.10)
project(FariaFXPlugin)

set(CMAKE_CXX_STANDARD 14)

# Create a shared library (DLL on Windows)
add_library(FariaFX SHARED src/faria_vdj_plugin.cpp)

# Link against Winsock for UDP
if(WIN32)
    target_link_libraries(FariaFX wsock32 ws2_32)
    set_target_properties(FariaFX PROPERTIES LINK_FLAGS "/DEF:${CMAKE_CURRENT_SOURCE_DIR}/src/FariaFX.def")
endif()

# We need the VDJ SDK header to be in the src folder
target_include_directories(FariaFX PRIVATE src)

