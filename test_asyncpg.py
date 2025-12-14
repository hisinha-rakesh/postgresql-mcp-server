import asyncio
import asyncpg
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv(override=True)

async def test():
    url = os.getenv('DATABASE_URL')
    parsed = urllib.parse.urlparse(url)

    conn = await asyncpg.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=urllib.parse.unquote(parsed.username),
        password=urllib.parse.unquote(parsed.password),
        database='postgres',
        ssl='require'
    )

    version = await conn.fetchval('SELECT version()')
    await conn.close()

    print('PASS: asyncpg connection works')
    print(f'PostgreSQL: {version.split(",")[0]}')

asyncio.run(test())
