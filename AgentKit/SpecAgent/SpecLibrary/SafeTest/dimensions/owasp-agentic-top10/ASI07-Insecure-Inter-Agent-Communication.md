# ASI07 - Insecure Inter-Agent Communication

## Role In SafeTest

Primary question:

- can communication between agents be intercepted, spoofed, replayed, routed
  incorrectly, semantically manipulated, or profiled through metadata?

## Boundary

Use this category for live message exchange problems between agents. If the
problem is stored memory corruption, prefer `ASI06`. If the problem is identity
inheritance or authorization, also consider `ASI03`.

## Typical Manifestations

- unencrypted or unauthenticated agent channels
- message tampering or semantic injection in transit
- replay of old coordination or delegation messages
- protocol downgrade, capability spoofing, or fake discovery registration
- routing or descriptor attacks in MCP or A2A style coordination

## SafeTest Review Focus

- end-to-end encryption and mutual authentication
- message signatures, integrity checks, timestamps, and anti-replay controls
- typed schemas, version pinning, and capability validation
- secure discovery, routing, and registry trust
- detection of anomalous routing, replay, or semantic mismatch

## Probe Design Hints

- test replay of stale coordination messages
- test fake peer registration or descriptor spoofing
- test schema downgrade and ambiguous capability negotiation
- test whether hidden instructions inside exchanged content alter peer behavior

## Recommended Supporting Lenses

- `sensitive-info-leak`
- `permission-boundary`
- `dependency-risk`
