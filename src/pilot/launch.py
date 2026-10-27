"""Single-worker pilot launcher, including the verified Windows loop mitigation."""
import argparse
import asyncio
import sys


def configure_event_loop():
    """Set policy only in this explicitly launched process, before app imports.

    Python 3.12/NeMo synchronous checks reproduced a Windows Proactor cleanup
    failure. Selector checks exited normally. Importing this module has no side
    effects; Linux and the existing API/agent entry points remain unchanged.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        return "windows-selector"
    return "platform-default"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the supervised AMI analyst pilot")
    parser.add_argument("--host", choices=("127.0.0.1", "0.0.0.0"), default="127.0.0.1",
                        help="Use 0.0.0.0 only inside a container published to localhost")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    configure_event_loop()
    import uvicorn
    uvicorn.run("src.pilot.api:create_app", factory=True, host=args.host, port=args.port,
                workers=1, access_log=False, loop="asyncio")


if __name__ == "__main__":
    main()
