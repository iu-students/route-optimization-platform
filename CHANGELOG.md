# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- v0.1.0 - MVPv1, get input files and solve the problem

### Added
- Implemented JSON file reading mechanism for vehicle, loader, and order data ([#TT-1](https://github.com/iu-students/route-optimization-platform/issues/35))
- Implemented JSON file generation function for individual driver/loader daily routes ([#TT-5](https://github.com/iu-students/route-optimization-platform/issues/39))
- Added route capacity validation for trucks to ensure orders do not exceed vehicle capacity ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))
- Added verification that truck capacity constraints are respected during route generation ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))

### Changed
- Route generation now validates truck capacity before creating final routes ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))

### Deprecated

### Removed

### Fixed

### Security
