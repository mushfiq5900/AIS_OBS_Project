# generated from ament/cmake/core/templates/nameConfig.cmake.in

# prevent multiple inclusion
if(_teb_obstacle_avoidance_CONFIG_INCLUDED)
  # ensure to keep the found flag the same
  if(NOT DEFINED teb_obstacle_avoidance_FOUND)
    # explicitly set it to FALSE, otherwise CMake will set it to TRUE
    set(teb_obstacle_avoidance_FOUND FALSE)
  elseif(NOT teb_obstacle_avoidance_FOUND)
    # use separate condition to avoid uninitialized variable warning
    set(teb_obstacle_avoidance_FOUND FALSE)
  endif()
  return()
endif()
set(_teb_obstacle_avoidance_CONFIG_INCLUDED TRUE)

# output package information
if(NOT teb_obstacle_avoidance_FIND_QUIETLY)
  message(STATUS "Found teb_obstacle_avoidance: 0.1.0 (${teb_obstacle_avoidance_DIR})")
endif()

# warn when using a deprecated package
if(NOT "" STREQUAL "")
  set(_msg "Package 'teb_obstacle_avoidance' is deprecated")
  # append custom deprecation text if available
  if(NOT "" STREQUAL "TRUE")
    set(_msg "${_msg} ()")
  endif()
  # optionally quiet the deprecation message
  if(NOT teb_obstacle_avoidance_DEPRECATED_QUIET)
    message(DEPRECATION "${_msg}")
  endif()
endif()

# flag package as ament-based to distinguish it after being find_package()-ed
set(teb_obstacle_avoidance_FOUND_AMENT_PACKAGE TRUE)

# include all config extra files
set(_extras "")
foreach(_extra ${_extras})
  include("${teb_obstacle_avoidance_DIR}/${_extra}")
endforeach()
