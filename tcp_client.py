import asyncio

lock = asyncio.Lock()


async def tcp_write(drive_ip: str, port: int, message: str):
    async with lock:
        reader, writer = await asyncio.open_connection(drive_ip, port)
        writer.write(message.encode())
        await writer.drain()
        data = await reader.read(1024)
        writer.close()
        await writer.wait_closed()
        return data.decode()