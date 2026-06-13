import discord
from discord.ext import commands
import json


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='boing ', intents=intents)


@bot.command()
async def fisch(ctx):
    await ctx.send('Boingfisch')



with open('token.json', 'r') as f:
    token = json.load(f)['token']

bot.run(token)