cmake_minimum_required(VERSION 3.10)
project(ViskoVDJPlugin)

set(CMAKE_CXX_STANDARD 14)

# Create a shared library (DLL on Windows)
add_library(ViskoVDJ SHARED src/visko_vdj_plugin.cpp)

# Link against Winsock for UDP
if(WIN32)
    target_link_libraries(ViskoVDJ wsock32 ws2_32)
endif()

# We need the VDJ SDK header to be in the src folder
target_include_directories(ViskoVDJ PRIVATE src)

