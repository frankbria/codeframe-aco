"""BeadsClient main interface (stub for Phase 2 completion).

This module will contain the main BeadsClient class that provides the
public API for interacting with Beads. Currently a stub to allow
fixture tests to pass.
"""

from typing import Optional


def create_beads_client(
    db_path: Optional[str] = None,
    timeout: int = 30,
    sandbox: bool = False
):
    """Factory function to create a BeadsClient instance.

    Args:
        db_path: Path to .beads/ directory (auto-discovered if None)
        timeout: Timeout for bd commands in seconds
        sandbox: If True, disable daemon and Git sync for testing

    Returns:
        BeadsClient instance

    Note:
        This is a stub implementation for Phase 2. Full implementation
        will be added in Phase 3+ when implementing user stories.
    """
    # Stub implementation
    return {"db_path": db_path, "timeout": timeout, "sandbox": sandbox}
