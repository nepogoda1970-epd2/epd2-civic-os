"""Audit Core service.

Owns `AuditEvent` (canon section 18.1). No other service reads or writes
this service's storage directly (INV-03). See ADR-003 for the hash-chain
design.
"""
