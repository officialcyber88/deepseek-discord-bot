#!/usr/bin/env python3
import os, sys, logging
import tkinter as tk
from tkinter import simpledialog, messagebox
from discord.ext import commands

# ─── GUI Input Widget ──────────────────────────────────────────────────────
def get_token_from_gui():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    token = simpledialog.askstring("Bot Token", "Enter your Discord Bot Token:")
    if not token:
        messagebox.showerror("Error", "No token provided. Exiting.")
        sys.exit(1)
    return token

# ─── Discord Bot Configuration ─────────────────────────────────────────────
DISCORD_TOKEN = get_token_from_gui()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger("discord-bot")

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong!")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
