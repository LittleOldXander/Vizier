import config
import asyncio
from helper import *
import discord
from discord.ext import commands
from discord.utils import get
from datetime import datetime


class Aug(commands.Cog):

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




    #definition of commands
    @commands.group(case_insensitive=True)
    @commands.guild_only()
    async def aug(self,ctx):
        '''
        Category for managing augmentaion requests.

        '''
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return    

        if ctx.invoked_subcommand is None:
            await ctx.send("Unknown request or poorly written. Please be more specific.\nIf you need help on this command, just type \"!help aug\".")

    @aug.command(name='request', pass_context=True,aliases=['add', 'create'])
    @commands.guild_only()
    async def request(self,ctx, x:int, y:int, description:str="RANDOM"):
        """ 
        Creates an augmentation request in your name for this server. 
        The augmentation request can be deleted only by you or an admin.
        
        Usage: !aug request xCoord(mandatory) yCoord(mandatory) shortDescription(optional)

        xCoord - must be an integer, represents the x coordinate of the hex
        yCoord - must be an integer, represents the y coordinate of the hex
        shortDescription - short description for the request / comment (max 45 chars)


        Example:    !aug request 1 1 "Mining Facility"  // if there are spaces in the description quotes must be used 
                                                            otherwise just the first word will be considered
                    !aug request 1 1 MB                 // since the description has no spaces no quotes are required
                    !aug request 1 1
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "aug-requests":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-aug-requests")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:        
                await cur.execute("SELECT id FROM augs WHERE guild = %s and server = %s and locationX = %s and locationY = %s",
                                            (ctx.message.guild.id,server,x,y))
                if cur.rowcount > 0:
                    embed = discord.Embed(
                        type= "rich",
                        title="Error adding request",
                        description="""There is already a request at those coordindates.
                        Request not added to the database.""",
                        color = red) #,color=Hex code
                    await ctx.send(embed=embed)
                    return
                date = datetime.now()

                await cur.execute ("""INSERT INTO augs (user_id, locationX, locationY,comment,request_time, guild, server)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (ctx.message.author.id,x,y,description,date.strftime("%Y-%m-%d %H:%M:%S"),ctx.message.guild.id,server))
                await conn.commit()
                embed = discord.Embed(
                        type= "rich",
                        title="Added augmentation request",
                        description="""The request you've made was added to the database.
                        Here are the details:""",
                        color = aqua) #,color=Hex code
                embed.add_field(name="Description", value="""```{desc:s}```""".format (desc=description),inline=False)
                embed.add_field(name="Requested by", value="{}".format (ctx.message.author.display_name),inline=True)
                embed.add_field(name="Location", value="/goto {} {}".format (x,y),inline=True)
                embed.add_field(name="Date", value="{}".format (date.strftime("%d %b %Y, %H:%M:%S")),inline=True)

                await ctx.send(embed = embed)

    @request.error
    async def request_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help aug request".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @aug.command(name='delete', pass_context=True,aliases=['remove', 'cancel'])
    @commands.guild_only()
    async def delRequest(self,ctx,x:int=-99999,y:int=-99999):
        """ 
        Creates an augmentation request in your name for this server. 
        Unless you have specifically been given the right you can only delete your own requests.
        
        Usage: Usage: !aug delRequest xCoord(mandatory) yCoord(mandatory)

        xCoord - must be an integer, represents the x coordinate of the hex
        yCoord - must be an integer, represents the y coordinate of the hex


        Example:    !aug delRequest 1 1

        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "aug-requests":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-aug-requests")
            return
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                    guild = ctx.message.guild.id

                    await cur.execute("SELECT id, user_id,comment FROM augs WHERE guild = %s and server = %s and locationX =%s and locationY = %s",
                                    (guild,server,x,y))
                    if cur.rowcount ==0:
                        await ctx.send ("Request doesn't exist. Nothing to delete.")
                        return

                    row = await cur.fetchone()
                    allowed = await self.checkPermissions(ctx,cur, "delete_requests")

                    if ctx.message.author.id != row[1] and not allowed:
                        embedColor = red
                        messageTitle = "Error"
                        embedDesc = """You do not have permission to delete this request.
                        Play nice and try to delete your own requests, not ones by others """
                    else:

                        await cur.execute("DELETE FROM augs WHERE guild = %s and server = %s and id = %s",
                                    (guild,server,row[0]))
                        await conn.commit()
                        embedColor = aqua
                        messageTitle = "Request deleted"
                        user = ctx.message.guild.get_member(row[1])
                        uName = user.display_name if user is not None else "MIA Member"
                        embedDesc =  "Request **{sName:s}** by **{owner:s}** at **/goto {x:d} {y:d}** deleted successfully.".format(x=x,y=y,sName=row[2], owner= uName)                    
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor) 
                        
                    await ctx.send (embed = embed)

    @delRequest.error
    async def delRequest_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help aug delete".
                ''')
        await ctx.send(error) #don't forget  to remove this in live


#########################################################################################################

    @aug.command(name='pickup', pass_context=True,aliases=['get', 'take'])
    @commands.guild_only()
    async def pickup(self,ctx,x:int=-99999,y:int=-99999, description:str=""):
        """ 
        Picks up the augmentation request at the specified coordinates. 
        The pickup can be deleted only by you or an admin.
        
        Usage: Usage: !aug pickup xCoord(mandatory) yCoord(mandatory) shortDescription(optional)

        xCoord - must be an integer, represents the x coordinate of the hex
        yCoord - must be an integer, represents the y coordinate of the hex
        shortDescription - short description for the pickup (max 45 chars)

        Example:    !aug pickup 1 1 "ETA 2h"
                    !aug pickup 1 1

        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "aug-requests":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-aug-requests")
            return 
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                    guild = ctx.message.guild.id

                    await cur.execute("SELECT id, user_id,comment,request_time,picked_by,picked_time,completed_time FROM augs WHERE guild = %s and server = %s and locationX =%s and locationY = %s",
                                    (guild,server,x,y))
                    if cur.rowcount ==0:
                        await ctx.send ("Request doesn't exist. Nothing to delete.")
                        return

                    row = await cur.fetchone()
                    addDetails = False
                    if row[1]==ctx.message.author.id:
                        messageTitle = "Seriously?"
                        embedDesc = """You can't pick up your own requests! 
                        You need a bot to manage what you augmented for yourself? """
                        embedColor = red
                    elif row[4] != None:
                        messageTitle = "Can't pick up request"
                        user = ctx.message.guild.get_member(row[4])
                        uName = user.display_name if user is not None else "MIA Member"
                        if row[6]!=None:
                            embedDesc =  "The request that you are trying to pick up has already been completed by {} at {}.".format(uName,row[6].strftime("%d %b %Y, %H:%M:%S"))
                        else:
                            embedDesc =  "The request that you are trying to pick up has already been picked up by {} at {}.".format(uName,row[5].strftime("%d %b %Y, %H:%M:%S"))
                        embedColor = red
                    else:
                        date = datetime.now()
                        await cur.execute("UPDATE augs SET picked_time=%s, picked_by =%s, pickupd_comment = %s WHERE guild = %s and server = %s and id = %s",
                                    (date.strftime("%Y-%m-%d %H:%M:%S"),ctx.message.author.id,description,guild,server,row[0]))
                        await conn.commit()
                        messageTitle = "Picked up request"
                        embedColor = green
                        embedDesc = """You have picked up the request at **{} {}**.

                        Thank you for your augmentation commander!!""".format(x,y)
                        addDetails=True

                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor) #,color=Hex code

                    if addDetails:
                        embed.add_field(name= "Details", value="""```{name:s}```""".format (name=row[2]),inline=False)
                        embed.add_field(name="Request Time",value=row[3].strftime("%d %b %Y, %H:%M:%S"),inline=True)
                        embed.add_field(name="Pickup Time",value=date.strftime("%d %b %Y, %H:%M:%S"),inline=True)
                        user = ctx.message.guild.get_member(row[1])
                        uName = user.display_name if user is not None else "MIA Member"
                        embed.add_field(name="Requested by", value=uName,inline=False)
                        embed.add_field(name="Location", value="/goto {x:d} {y:d}".format(x=x,y=y),inline=True)
                        
                        embed.add_field(name="­",value=description,inline=False)

                    await ctx.send(embed=embed)

    @pickup.error
    async def pickup_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help aug pickup".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @aug.command(name='complete', pass_context=True,aliases=['done', 'finish'])
    @commands.guild_only()
    async def completeFunc(self,ctx,x:int=-99999,y:int=-99999, description:str=""):
        """ 
        Completes previous picked up augmentation request at the specified coordinates. 
        
        
        Usage: Usage: !aug complete xCoord(mandatory) yCoord(mandatory)

        xCoord - must be an integer, represents the x coordinate of the hex
        yCoord - must be an integer, represents the y coordinate of the hex

        Example:    !aug complete 1 1
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "aug-requests":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-aug-requests")
            return 
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                    guild = ctx.message.guild.id

                    await cur.execute("SELECT id, user_id,comment,request_time,picked_by,picked_time,completed_time FROM augs WHERE guild = %s and server = %s and locationX =%s and locationY = %s",
                                    (guild,server,x,y))
                    if cur.rowcount ==0:
                        await ctx.send ("Request doesn't exist. Nothing to complete.")
                        return

                    row = await cur.fetchone()
                    addDetails = False
                    if row[4]!=ctx.message.author.id:
                        messageTitle = "Seriously?"
                        embedDesc = """You can't complete what you didn't pick up. """
                        embedColor = red
                    elif row[6] != None:
                        messageTitle = "Request already completed,"
                        user = ctx.message.guild.get_member(row[4])
                        uName = user.display_name if user is not None else "MIA Member"
                        embedDesc =  "The request that you are trying to complete has already been completed by {} at {}.".format(uName,row[6].strftime("%d %b %Y, %H:%M:%S"))
                        embedColor = red
                    else:
                        date = datetime.now()
                        await cur.execute("UPDATE augs SET completed_time=%s WHERE guild = %s and server = %s and id = %s",
                                    (date.strftime("%Y-%m-%d %H:%M:%S"),guild,server,row[0]))
                        await conn.commit()
                        messageTitle = "Completed request"
                        embedColor = green
                        embedDesc = """You have completed the request at **{} {}**.

                        Thank you for your augmentation commander!!""".format(x,y)
                        addDetails=True

                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor) #,color=Hex code

                    if addDetails:
                        embed.add_field(name= "Details", value="""```{name:s}```""".format (name=row[2]),inline=False)
                        embed.add_field(name="Requested",value=row[3].strftime("%d %b %Y, %H:%M:%S"),inline=True)
                        embed.add_field(name="Picked up",value=row[5].strftime("%d %b %Y, %H:%M:%S"),inline=True)
                        embed.add_field(name="Completed",value=date.strftime("%d %b %Y, %H:%M:%S"),inline=True)
                        user = ctx.message.guild.get_member(row[1])
                        uName = user.display_name if user is not None else "MIA Member"
                        embed.add_field(name="Requested by", value=uName,inline=False)
                        embed.add_field(name="Location", value="/goto {x:d} {y:d}".format(x=x,y=y),inline=True)
                        
                        embed.add_field(name="­",value=description,inline=False)

                    await ctx.send(embed=embed)

    @completeFunc.error
    async def complete_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help aug complete".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @aug.command(name='delPickup', pass_context=True,aliases=['dp'])
    @commands.guild_only()
    async def delPickup(self,ctx,x:int=-99999,y:int=-99999):
        """ 
        Removes the pickup at the  specified coordinates. 
        Unless you have specifically been given the right you can only delete your own pickups.
        
        Usage: Usage: !aug delPickup xCoord(mandatory) yCoord(mandatory) shortDescription(optional)

        xCoord - must be an integer, represents the x coordinate of the hex
        yCoord - must be an integer, represents the y coordinate of the hex
       

        Example:    !aug delPickup 1 1

        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "aug-requests":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-aug-requests")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                await cur.execute("SELECT id, picked_by, completed_time FROM augs WHERE guild = %s and server = %s and locationX =%s and locationY = %s",
                                    (guild,server,x,y))
                if cur.rowcount ==0:
                    await ctx.send ("The augmentation request doesn't exist. Nothing to delete from.")
                    return 

                allowed = await self.checkPermissions(ctx,cur, "delete_requests")
                row = await cur.fetchone()
                if row[1]!= ctx.message.author.id and not allowed:
                    messageTitle = "The pickup wasnt deleted"
                    embedDesc = """That isn't your pickup to delete.
                    Be nice!"""
                    embedColor = red
                else:
                    if row[2] is not None:
                        messageTitle = "The pickup has already been completed"
                        embedDesc = """Sorry commander, but the pickup you tried to delete was already completed so i can't delete the pickup."""
                        embedColor = orange
                    else:
                        await cur.execute("UPDATE augs SET picked_by= %s , pickupd_comment = %s, picked_time = %s WHERE guild = %s and server = %s and id = %s",
                                    (None,None,None, guild,server,row[0]))
                        await conn.commit()
                        messageTitle = "The pickup has been deleted"
                        embedDesc = """Sorry to hear that commander.
                        The pickup at **/goto {} {}** has been deleted.""".format (x,y)
                        embedColor = aqua
                
                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor) #,color=Hex code
                await ctx.send (embed=embed)

    @delPickup.error
    async def delPickup_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help aug delPickup".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @aug.command(name='list', hpass_context=True,aliases=['show', 'view'])
    @commands.guild_only()
    async def list(self,ctx,target:str="all", filter:str="open"):
        """ 
        Lists opened augmentation requests. 
        Unless you have specifically been given the right you can only delete your own pickups.
        
        Usage: Usage: !aug list target(optional, default "all") filter(optional, default "open")

        target - [all | mine | username] the owner of the requests to be shown (everyone if "all" is chosen)
                    If target isnt specified "all" will be used
        filter - [open | pending | complete | all] the status of the augmentation requests to be shown.
                    If all is chosen, even the completed augmentations will be shown.
                    if filter is not specified "open" will be used.


        Example:    !aug list 
                    !aug list mine - shows own augmentation request
                    !aug list pending - shows the currently being completed augmentations

        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "aug-requests":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-aug-requests")
            return 

        if target == "mine":
            target = ctx.message.author.display_name
        if target!="all":
            user_id = getIdByName(ctx,target)
        
            if user_id is None:
                await ctx.send ("""It seems that you misstyped the user for which you want to see the requests.
    Please try again with a valid username!""")
                return

        if filter not in ["open","pending","complete","all"]:
            await ctx.send ("Please use one of the following values for filter: open, pending, complete or all")
            return

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                query = """SELECT user_id, locationX, locationY, comment, picked_by, pickupd_comment,request_time,picked_time, completed_time
                             FROM augs WHERE guild = %s and server = %s"""
                if target != "all":
                    query += " and (user_id = {} or picked_by = {})".format ( user_id,user_id)
                
                if filter == "complete":
                    query += "AND completed_time IS NOT NULL"
                elif filter == "pending":
                    query += "AND picked_time IS NOT NULL AND completed_time IS NULL"
                elif filter == "open":
                    query += "AND picked_time IS NULL AND completed_time IS NULL"
                
                await cur.execute(  query,(guild,server))
                
                messageTitle = "Showing {} augmentations requests for {}".format(filter, target)
                embedColor = purple

                if cur.rowcount ==0:
                   
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle+" | 0 / 0",
                        description="**There are no {} augmentations requests.**".format(filter),
                        color = embedColor)
                    await ctx.send(embed=embed)
                else:
                    rows = await cur.fetchall()

                    rowExpression ='''embed.add_field(name="­", value="""```{name:s}```""".format (name=row[3]),inline=False)
user = ctx.message.guild.get_member(row[0])
uName = user.display_name if user is not None else "MIA Member"
puser = ctx.message.guild.get_member(row[4])
pName = puser.display_name if puser is not None else "MIA Member"

status = "open"
if row[8] is not None:
    status = "complete"
elif row[7] is not None:
    status = "pending"
else:
    status = "open"
embed.add_field(name="Location", value="/goto {x:d} {y:d}".format(x=row[1],y=row[2]),inline=True)
embed.add_field(name="Status", value=status,inline=True)

embed.add_field(name="Request",value="Requested at: {time:s} by **{creator:s}**".format(time=row[6].strftime("%d %b %Y, %H:%M:%S"),creator=uName),inline=False)
if row[8] is None:
    if row[7] is not None:
        embed.add_field(name="Pickup",value="Picked up at: {time:s} by **{creator:s}**".format(time=row[7].strftime("%d %b %Y, %H:%M:%S") ,creator=pName),inline=False)
else:
    embed.add_field(name="Pickup",value="Picked up at: {time:s} by **{creator:s}**. Completed at {ctime:s}".format(time=row[7].strftime("%d %b %Y, %H:%M:%S") if row[7] is not None else "-",creator=pName,ctime=row[8].strftime("%d %b %Y, %H:%M:%S")),inline=False)
                            '''

                    embeds = getEmbeds(ctx,rows, messageTitle,"­­Here's a list of the requests on record:",embedColor,rowExpression)

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

    @list.error
    async def list_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help aug list".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################   

    @aug.command(name='listFrom', pass_context=True,aliases=['lf', 'viewFrom', 'showFrom'])
    @commands.guild_only()
    async def listFrom(self,ctx,x:int,y:int):
        """ 
        Lists opened augmentation requests based on distance from the specified coordinates (closest first). 
        
        Usage: Usage: !aug listFrom xCoord(mandatory) yCoord(mandatory)

        xCoord - must be an integer, represents the x coordinate of the hex
        yCoord - must be an integer, represents the y coordinate of the hex


        Example:    !aug listFrom 20 20 
        """

        
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "aug-requests":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-aug-requests")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                query = """SELECT user_id, locationX, locationY, comment, request_time
                             FROM augs WHERE guild = %s and server = %s AND picked_time IS NULL AND completed_time IS NULL"""

                await cur.execute(  query,(guild,server))
                
                messageTitle = "Showing available augmentations from {} {}".format(x, y)
                embedColor = purple
              
                if cur.rowcount ==0:
                   
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle+" | 0 / 0",
                        description="**There are no open augmentations requests.**",
                        color = embedColor)
                    await ctx.send(embed=embed)
                    
                else:

                    rows = await cur.fetchall()

                    stationsList = []

                    for row in rows:
                        dist = hexDistance(Point(x,y),Point(row[1],row[2]))
                        user = ctx.message.guild.get_member(row[0]) 
                        uName = user.display_name if user is not None else "MIA Member"
                        stationsList.append({'user': uName,'x':row[1],'y':row[2],'name':row[3],"dist":dist, "time":row[4]})

                    stationsList.sort(key=lambda d: d["dist"], reverse=False)
                    
                    rowExpression ='''embed.add_field(name="­", value="""```{name:s}```""".format (name=row["name"]),inline=False)
embed.add_field(name="Location", value="/goto {x:d} {y:d}".format(x=row["x"],y=row["y"]),inline=True)
embed.add_field(name="Status", value="open",inline=True)
embed.add_field(name="Distance", value="{} hexes".format(row["dist"]),inline=True)
embed.add_field(name="Request",value="Requested at: {time:s} by **{creator:s}**".format(time=row["time"].strftime("%d %b %Y, %H:%M:%S"),creator=row["user"]),inline=False)
                            '''

                    embeds = getEmbeds(ctx,stationsList, messageTitle,"­­Here's a list of the requests on record:",embedColor,rowExpression)

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

    @listFrom.error
    async def listFrom_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help aug listFrom".
                ''')
        await ctx.send(error) #don't forget  to remove this in live