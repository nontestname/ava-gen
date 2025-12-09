"""
Storage abstractions for the AVA-Gen runtime.

Includes:
- SessionStore: minimal session history storage (in-memory + file-backed)
- ActionPlanStore: read-only access to generated actionplan JSON files
- LogStore: append-only logging for debugging / analysis
"""


