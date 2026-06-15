import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
import json


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='boing ', intents=intents, help_command=None)


@bot.event
async def on_ready():
    print('Logged in.')

    # Sync slash commands
    await bot.tree.sync()



async def main():
    with open('token.json', 'r', encoding='utf-8') as f:
        token = json.load(f)['token']

    async with bot:
        await bot.load_extension('src.bf.commands.help')
        await bot.load_extension('src.bf.commands.fisch')
        await bot.load_extension('src.bf.commands.words')
        await bot.load_extension('src.bf.commands.py_exec')
        await bot.start(token)


if __name__ == '__main__':
    asyncio.run(main())