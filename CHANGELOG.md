# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Released]
- v0.1.0 - MVPv1, get input files and solve the problem

### Added

- Implemented JSON file reading mechanism for vehicle, loader, and order data ([#TT-1](https://github.com/iu-students/route-optimization-platform/issues/35))
- Implemented JSON file generation function for individual driver/loader daily routes ([#TT-5](https://github.com/iu-students/route-optimization-platform/issues/39))
- Added route capacity validation for trucks to ensure orders do not exceed vehicle capacity ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))
- Added verification that truck capacity constraints are respected during route generation ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))
- Added shift duration verification for loaders and drivers to ensure route start times do not exceed shift end times ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/37))
- Added order time window verification to ensure estimated arrival times at each delivery point fall within specified intervals ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/38))
- Added REST API endpoints for submitting routing problems and receiving solutions ([#TT-6](https://github.com/iu-students/route-optimization-platform/issues/41))
  - `POST /solve` - Accepts JSON with vehicle, loader, and order data; starts computations
  - `GET /solution` - Returns generated routes or status of computations   
  - `GET /health` - Service health check endpoint
- Deployed MVP v1 to production hosting ([#TT-7](https://github.com/iu-students/route-optimization-platform/issues/40))
- Application now accessible via public URL ([#TT-7](https://github.com/iu-students/route-optimization-platform/issues/40))



### Changed
- Route generation now validates truck capacity before creating final routes ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/36))
- Route generation now validates shift constraints for loaders and drivers before assigning routes ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/37))
- Route generation now validates time window constraints for all delivery points sequentially ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/38))

### Deprecated

### Removed

### Fixed

### Security

## [Unreleased]
