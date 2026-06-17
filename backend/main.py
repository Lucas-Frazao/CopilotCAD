"""CopilotCAD backend entry point — JSON-RPC server over stdio."""

import sys

from jsonrpcserver import dispatch, method, Success


@method
def ping() -> Success:
    return Success("pong")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        response = dispatch(line)
        if response:
            sys.stdout.write(response + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
