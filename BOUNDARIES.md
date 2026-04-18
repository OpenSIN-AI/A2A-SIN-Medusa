# A2A-SIN-Medusa Boundaries

## Role
`A2A-SIN-Medusa` owns the MCP Factory workflows, autonomous tool synthesis, and Capability-Gap orchestration.

## This repo should own
- autonomous MCP synthesis, routing, and coordination flows
- capability-gap reception, recovery, and tool-injection handling
- MCP Factory contracts used by the OpenSIN-Neural-Bus
- runbooks tied to autonomous tool generation and sandboxed testing

## This repo must not own
- individual platform logic for the tools it synthesizes
- organization SSOT docs or architecture canon
- downstream business logic unrelated to Medusa ownership

## Hard rules
- Keep changes scoped to Medusa synthesis loops and tool generation.
- Move static tool behavior back to the repos that own those specific domains.
- Keep reusable contracts focused on autonomous synthesis and capability detection.
