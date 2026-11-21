"""Bound local HTTP intake by received bytes and total body-read time."""
import asyncio

from starlette.responses import PlainTextResponse


class RequestBodyLimit:
    def __init__(self, app, maximum_bytes=100_000, timeout_seconds=5):
        self.app = app
        self.maximum_bytes = maximum_bytes
        self.timeout_seconds = timeout_seconds

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        lengths = [value for key, value in scope.get('headers', []) if key.lower() == b'content-length']
        try:
            if len(lengths) > 1:
                raise ValueError()
            declared = int(lengths[0]) if lengths else 0
            if declared < 0:
                raise ValueError()
        except ValueError:
            return await PlainTextResponse('Invalid content length', status_code=400)(scope, receive, send)
        if declared > self.maximum_bytes:
            return await PlainTextResponse('Pilot request is too large', status_code=413)(scope, receive, send)
        parts, size, too_large = [], 0, False
        try:
            async with asyncio.timeout(self.timeout_seconds):
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    data = message.get('body', b'')
                    size += len(data)
                    if size > self.maximum_bytes:
                        too_large = True
                        break
                    parts.append(data)
                    if not message.get('more_body', False):
                        break
        except TimeoutError:
            return await PlainTextResponse('Pilot request body timed out', status_code=408)(scope, receive, send)
        if too_large:
            return await PlainTextResponse('Pilot request is too large', status_code=413)(scope, receive, send)
        body, delivered = b''.join(parts), False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return await receive()  # Preserve downstream disconnect observation.

        await self.app(scope, bounded_receive, send)
