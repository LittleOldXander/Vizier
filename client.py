import config
from station import Station
from permission import Permission
from aug import Aug
from FOB import FOB

import discord
from discord.ext import commands

import sqlalchemy as sa
import sqlalchemy.types as types
from sqlalchemy import func
import aiomysql
from aiomysql.sa import create_engine


metadata = sa.MetaData()

#initialize bot
bot = commands.Bot(command_prefix='!',case_insensitive=True)

@bot.event
async def on_ready():
    bot.pool = await aiomysql.create_pool(user=config.DB_USER, db=config.DB_NAME, host=config.DB_HOST, password=config.DB_PASS, loop=bot.loop)

    print('Logged in')
    print(bot.user.name)
    print(bot.user.id)
    print('--------------')
    game = discord.Game(config.STATUS_GAME)
    await bot.change_presence(status=discord.Status.online, activity = game)

@bot.check
async def globally_block_dms(ctx):
        return ctx.guild is not None

@bot.command(name='+',help="Alias for !fob add (to be implemented)",pass_context=True)
async def plus(ctx,name,*args):
    await ctx.invoke(bot.get_command('fob add'), name, *args)

@bot.command(name='-',help="Alias for !fob remove (to be implemented)",pass_context=True)
async def minus(ctx,name,*args):
   await ctx.invoke(bot.get_command('fob remove'), name, *args)

@bot.command(name='addClaim',pass_context=True)
async def addClaim(ctx,x:int,y:int,sName:str="Unnamed",description:str="­"):
    await ctx.invoke(bot.get_command('station create'), x,y,sName,description)

@bot.command(name='delClaim',pass_context=True)
async def delClaim(ctx,x:int,y:int):
    await ctx.invoke(bot.get_command('station delete'), x,y)

#@bot.command(name='getInfo',pass_context=True)
#async def infoFunc(ctx):
#    await ctx.send(ctx.message.guild.id)

bot.add_cog(Station(bot))
bot.add_cog(Permission(bot))
bot.add_cog(Aug(bot))
bot.add_cog(FOB(bot))
bot.run(config.DISCORD_TOKEN)


