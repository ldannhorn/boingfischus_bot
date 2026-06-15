import discord
from discord.ext import commands
from pathlib import Path

class Words(commands.Cog):
    bot: commands.Bot
    words: tuple[str, ...]

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        words_path = Path(__file__).parent.parent / 'resources' / 'words_de.txt'
        try:
            self.words = tuple(
                words_path.read_text(encoding='utf-8').splitlines()
            )
        except FileNotFoundError:
            self.words = ()
            print(f'Word list not found: {words_path}')
        except OSError as e:
            self.words = ()
            print(f'Failed to load word list: {e}')

    
    def ex_wortmit(self, substr: str) -> tuple[str, ...]:
        substr = substr.lower()

        matches = [word for word in self.words if substr in word]

        if not matches:
            return ('Kein Wort gefunden.',)
        
        messages: list[str] = []
        current = ''

        for word in matches:
            entry = word if not current else f', {word}'

            if len(current) + len(entry) > 2000:
                messages.append(current)
                current = word
            else:
                current += entry

        if current:
            messages.append(current)
        
        messages.append(f'{len(matches)} Wörter mit "{substr}" gefunden.')

        return tuple(messages)


    @commands.command(name='wortmit', description='(1 Argument) Findet Wörter, die den angegebenen Substring enthalten.')
    async def wortmit(self, ctx: commands.Context[commands.Bot], substr: str) -> None:
        for msg in self.ex_wortmit(substr):
            await ctx.send(msg)
    

    @discord.app_commands.command(
        name='boing-wort-mit',
        description='Findet Wörter, die den angegebenen Substring enthalten.'
    )
    async def boingwortmit(self, interaction: discord.Interaction, substr: str) -> None:
        messages = self.ex_wortmit(substr)

        await interaction.response.send_message(messages[0])
        for msg in messages[1:]:
            await interaction.followup.send(msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Words(bot))