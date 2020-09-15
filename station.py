
import config 
from helper import *

import discord
from discord.ext import commands
import asyncio
import re,math
import asyncio
from datetime import datetime


class Station(commands.Cog):
    """ 
    Commands for station: 

    !station create x y [stationName] [stationDescription]
    !station delete x y
    !station check x y
    !station list [all|user]
    !station cleanup
    """

    def __init__(self, bot):
        self.bot = bot

    async def checkPermissions(self,ctx,cur, permission="",scope=""):
        
       
        if ctx.message.author == ctx.message.guild.owner:
            return True
        elif permission == "admin" and scope == "admin":
            return False
        guild = ctx.message.guild.id
        
        await cur.execute("SELECT target FROM permissions WHERE guild = %s and reference = %s and value = 1",
                                (guild,permission))
        if cur.rowcount==0:
            return False
        else:
            found = False
            rows = await cur.fetchall()
            rolesIds=[role.id for role in ctx.message.author.roles]
            for row in rows:
                if row[0] in rolesIds:
                    found = True
                    break
            return found



    @commands.group(case_insensitive=True)
    @commands.guild_only()
    async def station(self,ctx):
        '''
        !station create x y [name] [description]
        !station delete x y //to delete other people's stations requires permission
        !station check x y
        !station list [mine | all | user]   //if no target is specified default is "mine"'
                                            //to list other people's stations requires permission
        !station cleanup                                    
        '''
        

        if ctx.invoked_subcommand is None:
            await ctx.send("Unknown request or poorly written. Please be more specific.\nIf you need help on this command, just type \"!help station\".")


    @station.command(name='create',pass_context=True)
    @commands.guild_only()
    async def createFunc(self,ctx,x:int,y:int,sName:str="Unnamed",description:str="­"):
        """ 
        Creates a station claim in your name. The claim can be deleted only by you or an admin.
        Warns if there are any stations within 10 hexes.

        Usage: Usage: !station create xCoord(mandatory) yCoord(mandatory) stationName(optional) stationDescription(optional)

        xCoord - must be an integer, represents the x coordinate of the hex
        yCoord - must be an integer, represents the y coordinate of the hex
        stationName - the name of the station, if not specified 'Unnamed' will be used (max 45 chars)
        stationDescription - short description for the station / comment (max 45 chars)

        Example: !station create 1 1 "My first station" "Short description(up to 45 chars) here"
        """

        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "station-claims":
           await ctx.send ("This is not the place to use this command!. Please use #{}-station-claims".format(server))

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:        
                await cur.execute("SELECT user_id, locationX, locationY, station_name AS name, station_comment AS comment, claim_time FROM claims WHERE guild = %s and server = %s",
                                            (ctx.message.guild.id,server))
                stationsList = []
                minDist = 99999
                if (cur.rowcount > 0):
                    rows = await cur.fetchall()
                   
                    
                    for row in rows:
                        dist = hexDistance(Point(x,y),Point(row[1],row[2]))
                        if dist < minDist:
                            minDist = dist
                        if dist<=config.WARN_DISTANCE:
                            user = ctx.message.guild.get_member(row[0])
                            uName = user.display_name if user is not None else "MIA Member"
                            stationsList.append({'user':uName,'x':row[1],'y':row[2],'name':row[3],'comment':row[4],"dist":dist, "time":row[5]})
                if minDist == 99999:
                    minDist = -1
                stationsList.sort(key=lambda x: x["dist"], reverse=False)
                                         
                if len(stationsList)>0:
                    if minDist != 0:
                        messageTitle = "Claim added with warnings"
                        embedColor = orange
                        embedDesc = """
                        Your claim has beed added to the database for {server:s}.
                        There are {sLen:d} stations within {warn:d} hexes. Closest station is {dist:d} hexes away.

                        **Owner:** {owner:s}
                        **Station name:** {sname:s}
                        **Location:** /goto {x:d} {y:d} 
                        **Description:** {desc:s}
                        ­
                        ---------------------------------------------------------------------
                        """.format(server=server,sLen=len(stationsList),dist= minDist, warn = config.WARN_DISTANCE,owner=ctx.message.author.display_name, sname = sName, x=x, y=y,desc = description)
                    else:
                        embedColor = red
                        messageTitle = "Claim not added - claim already exists"
                        embedDesc = "Your claim hasn't been added to the database. The claim already exists"
                        embed = discord.Embed(
                            type= "rich",
                            title=messageTitle,
                            description=embedDesc,
                            color = embedColor) #,color=Hex code
                        await ctx.send(embed=embed)
                        return
                else:
                    await cur.execute("""INSERT INTO claims (user_id,  locationX, locationY, station_name, station_comment, guild, server)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s);""",
                                        (ctx.message.author.id, x,y, sName, description,ctx.message.guild.id,server))
                    await conn.commit()
                    messageTitle = "Claim added"
                    embedColor = aqua
                    embedDesc =  """
                    Your claim has beed added to the database for {server:s}.
                    There are {sLen:d} stations within {warn:d} hexes. Closest station is {dist:d} hexes away.
                    """.format(server=server,sLen=len(stationsList),dist= minDist, warn = config.WARN_DISTANCE)
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor) #,color=Hex code
                    await ctx.send(embed=embed)
                    return
                

                #embed.set_author(name=self.bot.user.display_name)
                
                
                await cur.execute("""INSERT INTO claims (user_id,  locationX, locationY, station_name, station_comment, guild, server)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s);""",
                                        (ctx.message.author.id, x,y, sName, description,ctx.message.guild.id,server))
                await conn.commit()
                rowExpression ='''
embed.add_field(name= "Conflicts" if curItem % config.RESULTS_PER_PAGE == 0 else "­" , value="""```{name:s}```""".format (name=row["name"]),inline=False)
embed.add_field(name="Owner", value=row["user"])
embed.add_field(name="Location", value="/goto {x:d} {y:d}".format(x=row["x"],y=row["y"]))
date_time = row["time"]
embed.add_field(name="Details",value="""Distance: ** {dist:d}** hexes
Created at: {time:s}""".format(dist = row["dist"],time=date_time.strftime("%d %b %Y, %H:%M:%S")),inline=False)
'''
                embeds = getEmbeds(ctx, stationsList, messageTitle,embedDesc, embedColor,rowExpression)

                index = 0
                msg = None
                action = ctx.send
                left = '⏪'
                right = '⏩'

                def predicate(message, l, r):
                    def check(reaction, user):
                        if reaction.message.id != message.id or user == self.bot.user:
                            return False
                        if l and reaction.emoji == left:
                            return True
                        if r and reaction.emoji == right:
                            return True
                        return False
                    return check

                while True:
                    res = await action(embed=embeds[index])
                    
                    if len(embeds)>1:
                        if res is not None:
                            msg = res
                        #l = index != 0
                        #r = index != len(embeds) - 1
                        l=True
                        r=True
                        #if l:
                        await msg.add_reaction(left) 
                        #if r:
                        await msg.add_reaction(right)
                        pending_tasks = [self.bot.wait_for('reaction_add',check=predicate(msg, l, r)),
                                        self.bot.wait_for('reaction_remove',check=predicate(msg, l, r))]
                        done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                        for task in done_tasks: 
                            react, user = await task
                        if react.emoji == left:
                            if index >0:
                                index -= 1
                            else:
                                index = len(embeds)-1
                        elif react.emoji == right:
                            
                            if index < len(embeds)-1:
                                index += 1
                            else:
                                index = 0
                        action = msg.edit
                    else: 
                        return
         
    @createFunc.error
    async def create_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help station create".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @station.command(name='check',pass_context=True)
    @commands.guild_only()
    async def checkFunc(self,ctx,x:int,y:int):
        ''' Checks for station claims within 10 hexes of the specified coordinates.

            Usage: Usage: !station check xCoord(mandatory) yCoord(mandatory)

            xCoord - must be an integer, represents the x coordinate of the hex
            yCoord - must be an integer, represents the y coordinate of the hex

            Example: !station check 1 1
            '''
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "station-claims":
           await ctx.send ("This is not the place to use this command!. Please use #{}-station-claims".format(server))
        

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id, locationX, locationY, station_name AS name, station_comment AS comment, claim_time FROM claims WHERE guild = %s and server = %s",
                                        (ctx.message.guild.id,server))
                
                stationsList = []
                if cur.rowcount >0:
                    rows = await cur.fetchall()
                    minDist = 99999
                    for row in rows:
                        dist = hexDistance(Point(x,y),Point(row[1],row[2]))
                        if dist < minDist:
                            minDist = dist
                        if dist<=config.WARN_DISTANCE:
                            user = ctx.message.guild.get_member(row[0])
                            uName = user.display_name if user is not None else "MIA Member"
                            stationsList.append({'user': uName,'x':row[1],'y':row[2],'name':row[3],'comment':row[4],"dist":dist, "time":row[5]})
                    
                    stationsList.sort(key=lambda x: x["dist"], reverse=False)

                messageTitle = "Checking for stations within {maxRadius:d} hexes of [{x:d},{y:d}]".format(maxRadius = config.WARN_DISTANCE, x=x,y=y)
                
                                                                    
                if len(stationsList)>0:
                    embedColor = orange
                    embedDesc = """**Bad news commander!**
There are {stations:d} stations within {warn:d} hexes of [{x:d},{y:d}]. They're listed below:
""".format (stations= len(stationsList), warn = config.WARN_DISTANCE,x=x,y=y)
                else:
                    embedColor = aqua
                    embedDesc =  "You're clear for [{x:d},{y:d}].\nThere are no stations within {warn:d} hexes. Closest station is {dist:d} hexes away.".format(dist= minDist, warn = config.WARN_DISTANCE,x=x,y=y)
                
                embed = discord.Embed(
                    type= "rich",
                    title=messageTitle,
                    description=embedDesc,
                    color = embedColor) #,color=Hex code                

                if len(stationsList)>0:
                    rowExpression ='''embed.add_field(name="­", value="""```{name:s}```""".format (name=row["name"]),inline=False)
embed.add_field(name="Owner", value=row["user"])
embed.add_field(name="Location", value="/goto {x:d} {y:d}".format(x=row["x"],y=row["y"]))
date_time = row["time"]
embed.add_field(name="Details",value="""Distance: ** {dist:d}** hexes
Created at: {time:s}""".format(dist = row["dist"],time=date_time.strftime("%d %b %Y, %H:%M:%S")),inline=False)
'''

                    embeds = getEmbeds(ctx,stationsList, messageTitle,embedDesc, embedColor,rowExpression)

                    index = 0
                    msg = None
                    action = ctx.send
                    left = '⏪'
                    right = '⏩'

                    def predicate(message, l, r):
                        def check(reaction, user):
                            if reaction.message.id != message.id or user == self.bot.user:
                                return False
                            if l and reaction.emoji == left:
                                return True
                            if r and reaction.emoji == right:
                                return True
                            return False
                        return check

                    while True:
                        res = await action(embed=embeds[index])
                        
                        if len(embeds)>1:
                            if res is not None:
                                msg = res
                            #l = index != 0
                            #r = index != len(embeds) - 1
                            l=True
                            r=True
                            #if l:
                            await msg.add_reaction(left) 
                            #if r:
                            await msg.add_reaction(right)
                            pending_tasks = [self.bot.wait_for('reaction_add',check=predicate(msg, l, r)),
                                            self.bot.wait_for('reaction_remove',check=predicate(msg, l, r))]
                            done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                            for task in done_tasks: 
                                react, user = await task
                            if react.emoji == left:
                                if index >0:
                                    index -= 1
                                else:
                                    index = len(embeds)-1
                            elif react.emoji == right:
                                
                                if index < len(embeds)-1:
                                    index += 1
                                else:
                                    index = 0
                            action = msg.edit
                        else: 
                            return

    
    @checkFunc.error
    async def check_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help station check".
                ''')
        await ctx.send(error) #don't forget  to remove this in live
    
#########################################################################################################

    @station.command(name='list',pass_context=True)
    @commands.guild_only()
    async def listFunc(self,ctx,target:str="all"):
        ''' 
        Shows a list of the registered claims.

        [target] - optional argument refering to the filter of the list
                    Possible values: all , mine, *username*  

        Example:    !station list
                    !station list all
                    !station list SomeDude
                    !station list mine
        '''
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "station-claims":
           await ctx.send ("This is not the place to use this command!. Please use #{}-station-claims".format(server))
           return

        if target =="mine":
            target = ctx.message.author.display_name
        if target != "all":
            targetId = getIdByName(ctx, target)
            if targetId == None:
                await ctx.send ("The specified user doesn't exist!. Please choose 'mine', 'all' or a valid username ")
                return
        
        async with self.bot.pool.acquire() as conn: 
            async with conn.cursor() as cur:
                allowed = True #await self.checkPermissions(ctx,cur, "list_stations")
               
                if target!=ctx.message.author.display_name and not allowed:
                    embed = discord.Embed(
                        type= "rich",
                        title="Error",
                        description="You do not have permission to list the claims of others.",
                        color = red)  
                    await ctx.send (embed = embed)
                    return

                if target == "all":
                    await cur.execute("SELECT user_id, locationX, locationY, station_name AS name, station_comment AS comment, claim_time FROM claims WHERE guild = %s and server = %s",
                                    (ctx.message.guild.id,server))
                else:
                    
                    await cur.execute("SELECT user_id, locationX, locationY, station_name AS name, station_comment AS comment, claim_time FROM claims WHERE guild = %s and server = %s and user_id =%s",
                                    (ctx.message.guild.id,server,targetId))
  

                embedColor = purple
                if cur.rowcount ==0:
                    messageTitle = "Showing claims for {}".format(target)
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle+" | 0 / 0",
                        description="**There are no claims yet.**",
                        color = embedColor)
                    await ctx.send(embed=embed)
                else:
                    messageTitle = "Showing claims for {target:s}".format(target=target)

                    rows = await cur.fetchall()
                    rowExpression ='''embed.add_field(name="­", value="""```{name:s}```""".format (name=row[3]),inline=False)
user = ctx.message.guild.get_member(row[0])
uName = user.display_name if user is not None else "MIA Member"
embed.add_field(name="Owner", value=uName,inline=True)
embed.add_field(name="Location", value="/goto {x:d} {y:d}".format(x=row[1],y=row[2]),inline=True)
date_time = row[5]
embed.add_field(name="Details",value="Created at: {time:s}".format(time=date_time.strftime("%d %b %Y, %H:%M:%S")),inline=False)
                        '''
                    embeds = getEmbeds(ctx,rows, messageTitle,"­­",embedColor,rowExpression)

                    index = 0
                    msg = None
                    action = ctx.send
                    left = '⏪'
                    right = '⏩'

                    def predicate(message, l, r):
                        def check(reaction, user):
                            if reaction.message.id != message.id or user == self.bot.user:
                                return False
                            if l and reaction.emoji == left:
                                return True
                            if r and reaction.emoji == right:
                                return True
                            return False
                        return check
                    while True:
                        res = await action(embed=embeds[index])
                        
                        if len(embeds)>1:
                            if res is not None:
                                msg = res
                            #l = index != 0
                            #r = index != len(embeds) - 1
                            l=True
                            r=True
                            #if l:
                            await msg.add_reaction(left) 
                            #if r:
                            await msg.add_reaction(right)
                            pending_tasks = [self.bot.wait_for('reaction_add',check=predicate(msg, l, r)),
                                            self.bot.wait_for('reaction_remove',check=predicate(msg, l, r))]
                            done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                            for task in done_tasks: 
                                react, user = await task
                            if react.emoji == left:
                                if index >0:
                                    index -= 1
                                else:
                                    index = len(embeds)-1
                            elif react.emoji == right:
                                
                                if index < len(embeds)-1:
                                    index += 1
                                else:
                                    index = 0
                            action = msg.edit
                        else: 
                            return
    
    @listFunc.error
    async def list_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help station list".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @station.command(name='delete',pass_context=True)
    @commands.guild_only()
    async def deleteFunc(self,ctx,x:int,y:int):
        ''' 
        Deletes a claim at the specified coordinates.
        Unless you have been given the permission, only deleting own claims is allowed.

        xCoord - the x coordinate of the station (mandatory)
        yCoord - the y coordinate of the station (mandatory)

        Example:    !station delete 100 -200
        '''

        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "station-claims":
           await ctx.send ("This is not the place to use this command!. Please use #{}-station-claims".format(server))

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                    guild = ctx.message.guild.id

                    await cur.execute("SELECT id, user_id, station_name FROM claims WHERE guild = %s and server = %s and locationX =%s and locationY = %s",
                                    (guild,server,x,y))
                    if cur.rowcount ==0:
                        await ctx.send ("Station doesn't exist. Nothing to delete.")
                        return

                    row = await cur.fetchone()
                    allowed = await self.checkPermissions(ctx,cur, "delete_stations")

                    claim_id = row[0]
                    user_id = row[1]
                    station_name = row[2]

                    if ctx.message.author.id != user_id and not allowed:
                        embedColor = red
                        messageTitle = "Error"
                        embedDesc = "You do not have permission to delete this claim"
                    else:
                        await cur.execute("DELETE FROM claims WHERE guild = %s and server = %s and id = %s",
                                    (guild,server,claim_id))
                        await conn.commit()
                        embedColor = aqua
                        messageTitle = "Claim deleted"
                        user = ctx.message.guild.get_member(user_id)
                        uName = user.display_name if user is not None else "MIA Member"
                        embedDesc =  "Claim **{sName:s}** by **{owner:s}** at **/goto {x:d} {y:d}** deleted successfully.".format(x=x,y=y,sName=row[2], owner= uName)                    
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor) 
                        
                    await ctx.send (embed = embed)

    @deleteFunc.error
    async def delete_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help station delete".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @station.command(name='cleanup',pass_context=True)
    @commands.guild_only()
    async def cleanupFunc(self,ctx,x:int=-99999,y:int=-99999):
        ''' 
        Deletes the claims of all users who don't have access to this channel.
        Only users who have been given permission can use this command

        Example:    !station cleanup
        '''
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "station-claims":
           await ctx.send ("This is not the place to use this command!. Please use #{}-station-claims".format(server))
        
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                allowed = await self.checkPermissions(ctx,cur, "cleanup_stations")


                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = "You do not have permission to cleanup stations"
                else:
                    await cur.execute("SELECT id,user_id FROM claims WHERE guild = %s and server = %s",
                                        (ctx.message.guild.id,server))
                    claimCount = 0
                    if cur.rowcount>0:
                        rows = await cur.fetchall()
                        userIds=[member.id for member in ctx.message.channel.members]

                        for row in rows:
                            if row[1] not in userIds:
                                await cur.execute("DELETE FROM claims WHERE guild = %s and server = %s and id = %s",
                                            (ctx.message.guild.id,server,row[0]))
                                claimCount = claimCount+1
                        await conn.commit()
                        embedColor = aqua
                        messageTitle = "Claim cleanup"
                        embedDesc = "Deleted {cc:d} claims.".format(cc=claimCount)   
                embed = discord.Embed(
                    type= "rich",
                    title=messageTitle,
                    description=embedDesc,
                    color = embedColor) 
                    
                await ctx.send (embed = embed)

    @cleanupFunc.error
    async def cleanup_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help station cleanup".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

                