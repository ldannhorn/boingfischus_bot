import discord
from discord.ext import commands

class Help(commands.Cog):
    bot: commands.Bot

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    def execute(self) -> str:
        return f'{''.join([f'boing {cmd.name}: {cmd.description}\n' for cmd in self.bot.commands])}'


    @commands.command(name='help', description='Übersicht über alle Befehle')
    async def help(self, ctx: commands.Context[commands.Bot]) -> None:
        help = self.execute()
        await ctx.send(help)
    

    @discord.app_commands.command(
        name='boinghelp',
        description='Übersicht über alle Befehle'
    )
    async def boinghelp(self, interaction: discord.Interaction) -> None:
        help = self.execute()
        await interaction.response.send_message(help)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))