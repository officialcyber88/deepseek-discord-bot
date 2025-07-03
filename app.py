#!/usr/bin/env python3
import os, sys, subprocess, threading, time, logging, asyncio, requests

import nest_asyncio; nest_asyncio.apply()
from aiohttp import ClientSession, TCPConnector, ClientTimeout
import orjson as json
import gradio as gr

# ─── Gradio + Ollama Configuration ─────────────────────────────────────────
OLLAMA_PORT    = int(os.getenv("OLLAMA_PORT", "11434"))
BASE_MODEL     = os.getenv("BASE_MODEL", "deepseek-r1:7b")
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "10"))
PREWARM_PROMPT = "ping"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger("gradio-bot")

_http = None
_sema = asyncio.Semaphore(MAX_CONCURRENT)

def start_ollama():
    proc = subprocess.Popen(
        ["ollama", "serve"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    def tail():
        for line in proc.stdout:
            if "error" in line.lower(): logger.error(line.rstrip())
    threading.Thread(target=tail, daemon=True).start()
    return proc

def wait_for_ollama():
    url = f"http://127.0.0.1:{OLLAMA_PORT}/"
    start, backoff = time.time(), 1
    while time.time() - start < 300:
        try:
            if requests.get(url, timeout=backoff).status_code < 500:
                return
        except:
            pass
        time.sleep(backoff); backoff = min(backoff*1.5, 5)
    logger.error("Ollama never ready"); sys.exit(1)

def prepare_model():
    subprocess.run(["ollama","pull",BASE_MODEL], check=True)
    quant = BASE_MODEL.replace("7b","7b-int8")
    chosen = BASE_MODEL
    try:
        subprocess.run(
            ["ollama","quantize",BASE_MODEL,"--int8","--tag",quant],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        chosen = quant
    except subprocess.CalledProcessError:
        pass
    # pre-warm
    _http.post(
        f"http://127.0.0.1:{OLLAMA_PORT}/api/chat",
        json={"model":chosen,"messages":[{"role":"user","content":PREWARM_PROMPT}],
              "max_tokens":32,"stream":False}
    )
    return chosen

async def _chat_async(prompt: str) -> str:
    payload = {"model":model_tag,"messages":[{"role":"user","content":prompt}],
               "max_tokens":512,"stream":False}
    async with _sema:
        async with _http.post(
            f"http://127.0.0.1:{OLLAMA_PORT}/api/chat",
            json=payload, timeout=ClientTimeout(sock_read=None)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json(loads=json.loads)
            return data["choices"][0]["message"]["content"]

def chat(prompt: str) -> str:
    return asyncio.get_event_loop().run_until_complete(_chat_async(prompt))

if __name__ == "__main__":
    # start Ollama
    start_ollama(); wait_for_ollama()
    conn = TCPConnector(limit=MAX_CONCURRENT*2, keepalive_timeout=30)
    _http = ClientSession(connector=conn)
    model_tag = prepare_model()

    demo = gr.Interface(
        fn=chat,
        inputs=gr.Textbox(lines=2, placeholder="Type here…"),
        outputs="text",
        title="Deepseek Chat",
        description="Ollama + Gradio + Discord Bot"
    )
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860"))
    )
