import sys

if sys.platform != 'win32':  # pragma: no cover
    raise ImportError('Service CLI is only supported on Windows')

import win32serviceutil

from .service import VoiceTriggerService


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m src install|remove|start|stop|debug')
        sys.exit(1)

    action = sys.argv[1].lower()
    allowed = {"install", "remove", "start", "stop", "debug"}
    if action not in allowed:
        print(f'Unknown command: {action}')
        sys.exit(1)

    win32serviceutil.HandleCommandLine(
        VoiceTriggerService, argv=[sys.argv[0], action]
    )


if __name__ == '__main__':
    main()
