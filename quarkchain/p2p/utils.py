import datetime
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
import logging
import os
import signal
from typing import Tuple

import rlp


def sxor(s1: bytes, s2: bytes) -> bytes:
    if len(s1) != len(s2):
        raise ValueError("Cannot sxor strings of different length")
    return bytes(x ^ y for x, y in zip(s1, s2))


def roundup_16(x: int) -> int:
    """Rounds up the given value to the next multiple of 16."""
    remainder = x % 16
    if remainder != 0:
        x += 16 - remainder
    return x


def get_devp2p_cmd_id(msg: bytes) -> int:
    """Return the cmd_id for the given devp2p msg.

    The cmd_id, also known as the payload type, is always the first entry of the RLP, interpreted
    as an integer.
    """
    return rlp.decode(msg[:1], sedes=rlp.sedes.big_endian_int)


def time_since(start_time: datetime.datetime) -> Tuple[int, int, int, int]:
    delta = datetime.datetime.now() - start_time
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return delta.days, hours, minutes, seconds


# colors from devp2p/utils.py
# ###### colors ###############

COLOR_FAIL = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_UNDERLINE = "\033[4m"
COLOR_END = "\033[0m"

colors = ["\033[9%dm" % i for i in range(0, 7)]
colors += ["\033[4%dm" % i for i in range(1, 8)]


def cstr(num, txt):
    return "%s%s%s" % (colors[num % len(colors)], txt, COLOR_END)


def cprint(num, txt):
    print(cstr(num, txt))


if __name__ == "__main__":
    for i in range(len(colors)):
        cprint(i, "test")


CPU_EMPTY_VALUES = {None, 0}


_executor = None  # : Executor


def get_asyncio_executor(cpu_count: int = None) -> Executor:
    global _executor

    """
    I don't see a need for ProcessPoolExecutor in QuarkChain, just use thread executor
    """
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=1)
    return _executor

    """
    Returns a global `ProcessPoolExecutor` instance.

    NOTE: We use the ProcessPoolExecutor to offload CPU intensive tasks to
    separate processes to ensure we don't block the main networking process.
    This pattern will only work correctly if used within a single process.  If
    multiple processes use this executor API we'll end up with more workers
    than there are CPU cores at which point the networking process will be
    competing with all the worker processes for CPU resources.  At the point
    where we need this in more than one process we will need to come up with a
    different solution
    """

    if _executor is None:
        # Use CPU_COUNT - 1 processes to make sure we always leave one CPU idle
        # so that it can run asyncio's event loop.
        if cpu_count is None:
            os_cpu_count = os.cpu_count()
            if os_cpu_count in CPU_EMPTY_VALUES:
                # Need this because os.cpu_count() returns None when the # of
                # CPUs is indeterminable.
                logger = logging.getLogger("p2p")
                logger.warning(
                    "Could not determine number of CPUs, defaulting to 1 instead of %s",
                    os_cpu_count,
                )
                cpu_count = 1
            else:
                cpu_count = max(1, os_cpu_count - 1)
        # The following block of code allows us to gracefully handle
        # `KeyboardInterrupt` in the worker processes.  This is accomplished
        # via two "hacks".
        #
        # First: We set the signal handler for SIGINT to the special case
        # `SIG_IGN` which instructs the process to ignore SIGINT, while
        # preserving the original signal handler.  We do this because child
        # processes inherit the signal handlers of their parent processes.
        #
        # Second, we have to force the executor to initialize the worker
        # processes, as they are not initialized on instantiation, but rather
        # lazily when the first work is submitted.  We do this by calling the
        # private method `_start_queue_management_thread`.
        #
        # Finally, we restore the original signal handler now that we know the
        # child processes have been initialized to ensure that
        # `KeyboardInterrupt` in the main process is still handled normally.
        original_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        _executor = ProcessPoolExecutor(cpu_count)
        _executor._start_queue_management_thread()  # type: ignore
        signal.signal(signal.SIGINT, original_handler)
    return _executor
