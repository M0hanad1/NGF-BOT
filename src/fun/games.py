import discord
import time
from random import choice, randint
from discord.ext import commands
from asyncio import TimeoutError
from src.score.score import Score
from src.fun.tictactoe import TicTacToe
from src.fun.random import Random
from src.fun.roshambo import Roshambo
from src.functions.functions import create_embeds, create_image, arabic_convert


class Fun:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.temp = {}
        self.assets_path = './assets/'
        self.words_path = self.assets_path + 'words/'
        self.img_path = self.assets_path + 'img/'
        self.data = Score(self.bot)

    def temp_check(self, ctx):
        server_id = ctx.guild.id
        channel_id = ctx.channel.id

        if server_id not in self.temp:
            self.temp[server_id] = []

        if channel_id not in self.temp[server_id]:
            self.temp[server_id].append(channel_id)
            return False

        return True

    def temp_remove(self, ctx):
        server_id = ctx.guild.id
        channel_id = ctx.channel.id

        self.temp[server_id].remove(channel_id)

        if len(self.temp[server_id]) == 0:
            del self.temp[server_id]

    async def typing_games(self, ctx, lang, game, mood):
        if self.temp_check(ctx):
            if mood:
                return await ctx.respond(embed=create_embeds(ctx, ('There\'s already a game in this channel', '')), ephemeral=True)

            return await ctx.reply(embed=create_embeds(ctx, ('There\'s already a game in this channel', '')))

        lang = lang.lower()
        lang_files = [f'{self.words_path}english_words.txt', f'{self.words_path}arabic_words.txt']

        if lang == 'en' or lang == 'english':
            the_lang = lang_files[0]

        elif lang == 'ar' or lang == 'arabic':
            the_lang = lang_files[1]

        else:
            the_lang = choice(lang_files)

        with open(the_lang, encoding='utf-8') as f:
            word = choice(f.readlines()).replace('\n', '')

            if the_lang == lang_files[1]:
                create_image(arabic_convert(word), self.img_path + 'temp_img.png')

            else:
                create_image(word, self.img_path + 'temp_img.png')

        file, embed = discord.File(f'{self.img_path}temp_img.png', filename='img.png'), create_embeds(ctx, (f'Try to {"write" if game == "fast" else "spell"}:', ''), embed_image='attachment://img.png')

        if mood:
            temp = await ctx.respond(file=file, embed=embed)
            temp = await temp.original_message()

        else:
            temp = await ctx.reply(file=file, embed=embed)

        start = time.time()

        try:
            word = word.replace('ة', 'ه')
            message = await self.bot.wait_for('message', check= lambda msg: (game == 'fast' and msg.content.lower().replace('ة', 'ه') == word) or (game == 'spell' and msg.content.lower().strip().replace('ة', 'ه') == ' '.join([i for i in word])), timeout=7 if game == 'fast' else 9)
            result = str(time.time() - start)[:4]
            await message.reply(embed=create_embeds(ctx, (f'You Won\nYou took: `{result}` Seconds', ''), embed_author=(message.author.name, message.author.display_avatar), embed_footer=('', '')))
            self.data.upgrade_score(ctx, message.author)

        except TimeoutError:
            embed = create_embeds(ctx, (f'Time out\nNo one get it', ''), embed_footer=('', ''))
            await temp.reply(embed=embed)

        self.temp_remove(ctx)

    async def random(self, ctx, mood):
        view = Random(ctx, mood)
        embed = create_embeds(ctx, ('Try to guess the random number!\nYou have `3` chances', ''))
        view.message = await ctx.respond(embed=embed, view=view) if mood else await ctx.reply(embed=embed, view=view)
        await view.wait()

        if view.value:
            self.data.upgrade_score(ctx, ctx.author)

    def roll(self, ctx, min, max):
        if min > max:
            return (create_embeds(ctx, ('The min number should be less than the max number', '')), True)

        return (create_embeds(ctx, (f'The random number: `{randint(min, max)}`', '')), False)

    def magic_ball(self, ctx, question):
        responses = ['As I see it, yes.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'It is certain.', 'It is decidedly so.', 'Most likely.', 'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'Outlook good.', 'Reply hazy, try again.', 'Signs point to yes.', 'Very doubtful.', 'Without a doubt.', 'Yes.', 'No.', 'Yes - definitely.', 'You may rely on it.']
        return create_embeds(ctx, embed_field=[('Question:', f'```\n{question}```', False), ('Answer:', f'```\n{choice(responses)}```', True)])

    def choose(self, ctx, choices):
        choices = [i for i in choices.strip().replace('،', ',').split(',') if len(i) > 0]

        if len(choices) == 0:
            raise commands.BadArgument

        return create_embeds(ctx, ('I choose:', f'```\n{choice(choices)}```'))

    async def tictactoe(self, ctx, member: discord.Member, mood):
        if ctx.author.id == member.id:
            return (create_embeds(ctx, ('You can\'t play with yourself', '')), True)

        if member.bot:
            return (create_embeds(ctx, ('You can\'t play with a bot', '')), True)

        view = TicTacToe(ctx, ctx.author, member, mood)
        embed = create_embeds(ctx, (f'It\'s `X`\'s turn', f'**It\'s {ctx.author.mention} turn**'), (ctx.author.name, ctx.author.display_avatar), thumbnail=ctx.author.display_avatar)
        content = f'**{ctx.author.mention} VS {member.mention}**'
        view.message = await ctx.respond(content=content, embed=embed, view=view) if mood else await ctx.reply(content=content, embed=embed, view=view)

    async def roshambo(self, ctx, member: discord.Member, mood):
        if member:
            if ctx.author.id == member.id:
                return (create_embeds(ctx, ('You can\'t play with yourself', '')), True)

            if member.bot and member.id != self.bot.user.id:
                return (create_embeds(ctx, ('You can\'t play with a bot', '')), True)

        member = member if member else self.bot.user

        view = Roshambo(ctx, [ctx.author, member], mood, self.bot)
        embed = create_embeds(ctx, ('', f'**It\'s {ctx.author.mention} turn\nChoose one of Rock, Paper and Scissors**'), (ctx.author.name, ctx.author.display_avatar), thumbnail=ctx.author.display_avatar)
        content = f'**{ctx.author.mention} VS {member.mention}**'
        view.message = await ctx.respond(content=content, embed=embed, view=view) if mood else await ctx.reply(content=content, embed=embed, view=view)
