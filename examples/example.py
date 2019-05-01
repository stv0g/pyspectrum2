import logging
import argparse
import asyncio

import backend


async def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--log', type=str)
    parser.add_argument('--host', type=str, required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--service.backend_id', type=int, metavar="ID",
                        required=True)
    parser.add_argument('-j', type=str, metavar="JID", required=True)
    parser.add_argument('config', type=str)

    args = parser.parse_args()

    if args.log is None:
        args.log = '/var/log/spectrum2/{}/backends/backend.log'.format(args.j)

    logging.basicConfig(
        # filename=args.log,
        format='%(asctime)-15s %(levelname)s %(name)s: %(message)s',
        level=logging.DEBUG if args.debug else logging.INFO
    )

    loop = asyncio.get_event_loop()

    await loop.create_connection(
        lambda: backend.ExampleBackend(args.j, args.config),
        args.host, args.port)

    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
