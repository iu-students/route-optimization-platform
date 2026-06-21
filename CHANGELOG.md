# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- v0.1.0 - MVPv1, get input files and solve the problem

### Added
- Implemented JSON file reading mechanism for vehicle, loader, and order data ([#TT-1] (link))
- Implemented JSON file generation function for individual driver/loader daily routes ([#TT-5] (link))
- Added shift duration verification for loaders and drivers to ensure route start times do not exceed shift end times ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/37))

### Changed
- Route generation now validates shift constraints for loaders and drivers before assigning routes ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/37))
### Deprecated

### Removed

### Fixed

### Security
