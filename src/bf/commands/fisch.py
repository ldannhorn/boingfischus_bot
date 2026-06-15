import discord
from discord.ext import commands

class Fisch(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    
    def execute(self) -> str:
        return 'Boingfisch'


    @commands.command(name='fisch', description='Boingfisch')
    async def fisch(self, ctx: commands.Context[commands.Bot]) -> None:
        await ctx.send(self.execute())
    

    @discord.app_commands.command(
        name='boingfisch',
        description='Boingfisch'
    )
    async def boingfisch(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(self.execute())


async def setup(bot: commands.Bot):
    await bot.add_cog(Fisch(bot))