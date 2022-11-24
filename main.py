import aiohttp 
import asyncio
import os
import base64
import itertools
import uvicorn

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

# 1. load urls from secrets.

def fetch_sub_urls(secrets_dir, names):
    urls = []
    for name in names:
        with open(os.path.join(secrets_dir, name)) as f:
            url = f.read().strip()
            print("Found {} -- {}".format(name, url))
            urls.append(url)
    return urls

# url -> [vmess]
async def url2vmess(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print("Status:", response.status)
            print("Content-type:", response.headers['content-type'])
            sub = await response.read()
            return base64.b64decode(sub + b'=' * (-len(sub) % 4)).decode().splitlines()

# [vmess] -> b64: str
def vmess2base64(vmesses):
    all_vmess = "\n".join(vmesses)
    b64_bytes = base64.b64encode(all_vmess.encode())
    return b64_bytes.decode()

# returns b64: str
async def aggregate_urls():
    secrets_dir = os.environ.get("AGGV2SUB_SECRETS_DIR", "/run/secrets/v2ray_subscriptions")
    names = os.environ.get("AGGV2SUB_SECRETS_NAMES", ":".join(["v2spacex", "tomlink", "feiniaoyun"])).split(":")
    urls = fetch_sub_urls(secrets_dir, names)
    vmesses = [url2vmess(url) for url in urls]
    tasks = [asyncio.create_task(url2vmess(url)) for url in urls]
    vmesses = await asyncio.gather(*tasks)
    flattened_vmesses = list(itertools.chain(*vmesses))
    print("All VMess links:")
    print(flattened_vmesses)
    return vmess2base64(flattened_vmesses)

app = FastAPI()

@app.get("/", response_class=PlainTextResponse)
async def root():
    return await aggregate_urls()

listen_port = int(os.environ.get("AGGV2SUB_LISTEN_PORT", "8056"))
listen_address = os.environ.get("AGGV2SUB_LISTEN_ADDRESS", "0.0.0.0")

def run():
    uvicorn.run("main:app", port=listen_port, host=listen_address)

if __name__ == '__main__':
    run()
