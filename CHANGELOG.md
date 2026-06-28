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

## [Released]

- v0.2.0 - MVPv2, optional order handling, separate vehicle/loader routing, input validation

### Added

- Implemented optional order penalty system: orders with `"optional": 1` are assigned a skip cost from `order_penalty` in weights; orders with `"optional": 0` have infinite skip cost ([#TT-1](https://github.com/iu-students/route-optimization-platform/issues/59)) 
- Added fulfillment cost calculation for optional orders, summing all additional costs (fuel, loader work, etc.) ([#TT-1](https://github.com/iu-students/route-optimization-platform/issues/59)) 
- Implemented decision-making logic that compares skip cost vs fulfillment cost to determine whether an order should be skipped ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/60)) 
- Created separate `Truck` and `Loader` data models with dedicated fields ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/62)) 
- Added database migrations for the new entity models with data migration support ([#TT-3](https://github.com/iu-students/route-optimization-platform/issues/62)) 
- Implemented independent route generation for vehicles and loaders - routes no longer depend on each other ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/63)) 
- Added arrival time synchronization logic to minimize difference between vehicle and loader arrival times at delivery points ([#TT-4](https://github.com/iu-students/route-optimization-platform/issues/63)) 
- Implemented input JSON validation function that checks for mandatory blocks and fields, correct data types, and physical meaning of values ([TT-5](https://github.com/iu-students/route-optimization-platform/issues/64)) 
  - Validates presence of all required blocks (depot, orders, weights, general parameters)
  - Validates order fields (id, x, y, volume, time_window, vehicle_service_time, loader_cnt, loader_service_time, optional)
  - Validates depot fields (id, x, y, load_time) and weights fields (order_penalty, take_vehicle, add_loader, fuel_cost, loader_work)
  - Validates numeric constraints (non-negative volumes, positive capacities/speeds, time window ordering, optional field 0/1)
  - Returns HTTP 400 with detailed error JSON on validation failure
- Added validation integration into API: invalid input is rejected before routing begins ([TT-5](https://github.com/iu-students/route-optimization-platform/issues/64))

### Changed

- Routing algorithm now produces separate independent routes for vehicles and loaders ([TT-4](https://github.com/iu-students/route-optimization-platform/issues/63)) 
- Route generation evaluates optional order profitability before including orders in final routes ([#TT-2](https://github.com/iu-students/route-optimization-platform/issues/60))

### Deprecated

### Removed

### Fixed

### Security

## [Unreleased]