"""SCP + SSH push to Raspberry Pi."""

import logging
import subprocess
from pathlib import Path

from twitcast.config import Config

log = logging.getLogger(__name__)


def push_to_pi(config: Config, image_path: Path) -> bool:
    """Push rendered image to Pi via scp and trigger display update."""
    host = config.pi.host
    if not host:
        log.info("No Pi host configured, skipping Pi push")
        return False

    user = config.pi.user
    remote_path = config.pi.image_path
    display_script = config.pi.display_script

    dest = f"{user}@{host}:{remote_path}"
    try:
        subprocess.run(
            ["scp", "-o", "ConnectTimeout=10", str(image_path), dest],
            check=True,
            capture_output=True,
            text=True,
        )
        log.info("Image pushed to %s", dest)
    except subprocess.CalledProcessError as e:
        log.warning("scp to Pi failed: %s", e.stderr.strip())
        return False

    try:
        subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", f"{user}@{host}", display_script],
            check=True,
            capture_output=True,
            text=True,
        )
        log.info("Pi display update triggered")
        return True
    except subprocess.CalledProcessError as e:
        log.warning("ssh display trigger failed: %s", e.stderr.strip())
        return False
