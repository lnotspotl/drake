# Entry point for the wheel build machinery; run with --help for more details.
# On Linux, wheels are build using Docker. On macOS, the host environment is
# used.

import sys

from drake.tools.wheel.wheel_builder.common import die
from drake.tools.wheel.wheel_builder.common import do_main as main


if __name__ == '__main__':
    if sys.platform == 'linux':
        from drake.tools.wheel.wheel_builder import linux as platform
    else:
        die('Building wheels is not supported on this platform '
            f'(\'{sys.platform}\')')

    main(args=sys.argv[1:], platform=platform)
