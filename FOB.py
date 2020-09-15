import config
from helper import *
import re
import asyncio
import discord
from discord.ext import commands
from discord.utils import get
from datetime import datetime



class FOB(commands.Cog):

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
    async def fob(self,ctx):
        '''
        Category for managing FOB fleets.

        '''
        

        if ctx.invoked_subcommand is None:
            await ctx.send("Unknown request or poorly written. Please be more specific.\nIf you need help on this command, just type \"!help fob\".")

#########################################################################################################

    @fob.command(name='addFOB',pass_context=True,aliases=[ 'create'])
    @commands.guild_only()
    async def addFOBFunc(self,ctx,name:str="Untitled FOB", fleetCap:int = 0, x:int=0,y:int=0):
        """ 
        Creates a FOB in the database. 
        
        Usage: !fob addFOB name fleetCap xPos(optional) yPos(optional) 
        name        - the name of the FOB(max 20 chars). Add / remove is done based on this.
        fleetCap    - the fleetCap of the FOB. The warnings will be thrown based on this value
        xCoord      - must be an integer, represents the x coordinate of the hex 
        yCoord      - must be an integer, represents the y coordinate of the hex
       


        Example:    !fob addFOB "Random FOB" 0 1 1  // if there are spaces in the description quotes must be used 
                                                            otherwise just the first word will be considered
                    !fob addFOB FOB1 10             
        """

        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 
        
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id FROM fobs where name = %s and guild = %s AND server = %s",(name,ctx.message.guild.id,server))

                if cur.rowcount > 0:
                    embed = discord.Embed(
                        type= "rich",
                        title="Error adding FOB",
                        description="""There is already a FOB with that name.
                        FOB not added to the database.""",
                        color = red) #,color=Hex code
                    await ctx.send(embed=embed)
                    return

                await cur.execute("""
                INSERT INTO fobs (guild,server,name, locationX, locationY, operating)
                VALUES (%s,%s,%s,%s,%s,%s)""",
                (ctx.message.guild.id,server,name,x,y,fleetCap))

                await conn.commit()

                embed = discord.Embed(
                        type= "rich",
                        title="Added FOB",
                        description="""The FOB has been added to the database here are the details:""",
                        color = purple) #,color=Hex code

                embed.add_field(name="Name", value="""```{desc:s}```""".format (desc=name),inline=False)
                embed.add_field(name="Location", value="/goto {} {}".format (x,y),inline=True)
                embed.add_field(name="Operating fleets", value="0/{}".format (fleetCap),inline=True)
                await ctx.send(embed=embed)




    @addFOBFunc.error
    async def addFOB_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
                Sorry but there is an error in your command. Please use "!help fob addfob".
                ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='rename',pass_context=True)
    @commands.guild_only()
    async def renameFunc(self,ctx,oldName:str, newName:str):
        """ 
        Renames the specified FOB. 
        
        Usage: !fob rename oldName newName

        oldName        - the current name of the FOB(max 20 chars). This is the FOB that will be renamed.
        newName        - the new name of the FOB(max 20 chars). This is what the new name will be.
        
        Example:    !fob rename "Random FOB" "Not so Random"  // if there are spaces in the names quotes must be used 
                                                                otherwise just the first word will be used for that variable
                    !fob rename Random NotRandom                  // since neither of the names has a space, no quotes are required

        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 
        
        if oldName ==newName:
            await ctx.send ("New name is the same as the old one. Nothing to rename.")
            return 


        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT id,locationX,locationY, operating , 
                    IFNULL(`destroyer`, 0) + IFNULL(`frigate`, 0) + IFNULL(`recon`, 0) + IFNULL(`gunship`, 0)
                    + IFNULL(`trooper`, 0) + IFNULL(`carrier`, 0) + IFNULL(`dreadnought`, 0) + IFNULL(`corvette`, 0) 
                    + IFNULL(`patrol`, 0) + IFNULL(`scout`, 0) + IFNULL(`industrial`, 0) as count
                    FROM fobs WHERE guild = %s and server = %s and name = %s"""

                    await cur.execute(  query,(guild,server,oldName))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not rename FOB"
                        embedDesc = """There is no FOB with that name!

                        Sorry, nothing was renamed.
                        """
                    else:
                        row = await cur.fetchone()

                        await cur.execute ("UPDATE fobs SET name = %s WHERE guild = %s and server = %s and id = %s",(newName,guild,server,row[0]))
                        await conn.commit()

                        embedColor = aqua
                        messageTitle = "Renamed FOB successfully"
                        embedDesc = "Added the FOB to the database:"
                        addDetails = True

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                if addDetails:
                    embed.add_field(name="Name", value="""```{name:s}```""".format (name=newName),inline=False)
                    embed.add_field(name="Location", value="/goto {} {}".format (row[1],row[2]),inline=True)
                    embed.add_field(name="Operating", value="{} / {}".format (row[4],row[3]),inline=True)
                await ctx.send(embed=embed)

    @renameFunc.error
    async def rename_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            server, cmd = chInfo (ctx)
            if server is None or  cmd is None:
                return
            await ctx.send(
                '''
Sorry but there is an error in your command. Please use "!help fob rename".
                ''')
        await ctx.send(error) #don't forget  to remove this in live


#########################################################################################################

    @fob.command(name='cap',pass_context=True)
    @commands.guild_only()
    async def capFunc(self,ctx,name:str, newCap:int):
        """ 
        Updates the fleet cap of the specified FOB. 
        
        Usage: !fob cap name fleetCap

        name        - the name of the FOB to change the fleet cap for.
        fleetCap        - the new value for the fleet cap for the specified FOB.
        
        Example:    !fob cap "Random FOB" 10    // if there are spaces in the name quotes must be used 
                                                    otherwise just the first word will be used for that variable
                    !fob cap Random 10          // since neither of the names has a space, no quotes are required

        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 
        


        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT id,locationX,locationY, operating , 
                    IFNULL(`destroyer`, 0) + IFNULL(`frigate`, 0) + IFNULL(`recon`, 0) + IFNULL(`gunship`, 0)
                    + IFNULL(`trooper`, 0) + IFNULL(`carrier`, 0) + IFNULL(`dreadnought`, 0) + IFNULL(`corvette`, 0) 
                    + IFNULL(`patrol`, 0) + IFNULL(`scout`, 0) + IFNULL(`industrial`, 0) as count,name
                    FROM fobs WHERE guild = %s and server = %s and name = %s"""

                    await cur.execute(  query,(guild,server,name))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not update FOB"
                        embedDesc = """There is no FOB with that name!

                        Sorry, nothing was updated.
                        """
                    else:
                        row = await cur.fetchone()

                        if newCap == row[3]:
                            embedDesc = """New cap  is the same as the old one.
                            Nothing was updated!"""
                            embedColor = red
                            messageTitle = "Error updating cap"
                            return 
                        else:
                            await cur.execute ("UPDATE fobs SET operating = %s WHERE guild = %s and server = %s and id = %s",(newCap,guild,server,row[0]))
                            await conn.commit()
                            if (row[4]>=newCap):
                                embedColor = orange
                                messageTitle = "Updated FOB's operating cap successfully. WARNING!!!!"
                                embedDesc = """Added the FOB to the database. 

                                **Pay attention to the cap!**
                                
                                """
                            else:
                                embedColor = aqua
                                messageTitle = "Updated FOB's operating cap successfully"
                                embedDesc = "Added the FOB to the database:"
                            addDetails = True

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                if addDetails:
                    embed.add_field(name="Name", value="""```{name:s}```""".format (name=name),inline=False)
                    embed.add_field(name="Location", value="/goto {} {}".format (row[1],row[2]),inline=True)
                    embed.add_field(name="Operating", value="{} / {}".format (row[4],newCap),inline=True)
                await ctx.send(embed=embed)

    @capFunc.error
    async def cap_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob cap".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='pos',pass_context=True)
    @commands.guild_only()
    async def posFunc(self,ctx,name:str, x:int, y:int):
        """ 
        Updates the location of the specified FOB. 
        
        Usage: !fob pos name xPos yPos

        name        - the name of the FOB to change the position for.
        xCoord      - must be an integer, represents the x coordinate of the hex 
        yCoord      - must be an integer, represents the y coordinate of the hex
        
        Example:    !fob pos "Random FOB" 10 10     // if there are spaces in the name quotes must be used 
                                                        otherwise just the first word will be used for that variable
                    !fob pos Random 10 10           // since neither of the names has a space, no quotes are required

        To be implemented
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT id,locationX,locationY, operating , 
                    IFNULL(`destroyer`, 0) + IFNULL(`frigate`, 0) + IFNULL(`recon`, 0) + IFNULL(`gunship`, 0)
                    + IFNULL(`trooper`, 0) + IFNULL(`carrier`, 0) + IFNULL(`dreadnought`, 0) + IFNULL(`corvette`, 0) 
                    + IFNULL(`patrol`, 0) + IFNULL(`scout`, 0) + IFNULL(`industrial`, 0) as count
                    FROM fobs WHERE guild = %s and server = %s and name = %s"""

                    await cur.execute(  query,(guild,server,name))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not update FOB"
                        embedDesc = """There is no FOB with that name!

                        Sorry, nothing was updated.
                        """
                    else:
                        row = await cur.fetchone()
                        if row[1] == x and row[2] == y:
                            embedColor = red
                            messageTitle = "Error updating position"
                            embedDesc = """The new position is the same as the old one
                            Nothing was updated!"""
                        else:
                            await cur.execute ("UPDATE fobs SET locationX = %s, locationY= %s WHERE guild = %s and server = %s and id = %s",(x,y,guild,server,row[0]))
                            await conn.commit()

                            embedColor = aqua
                            messageTitle = "Updated FOB successfully"
                            embedDesc = "Updated FOB's location:"
                            addDetails = True

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                if addDetails:
                    embed.add_field(name="Name", value="""```{name:s}```""".format (name=name),inline=False)
                    embed.add_field(name="Location", value="/goto {} {}".format (x,y),inline=True)
                    embed.add_field(name="Operating", value="{} / {}".format (row[4],row[3]),inline=True)
                await ctx.send(embed=embed)

    @posFunc.error
    async def pos_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob pos".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='delete', pass_context=True)
    @commands.guild_only()
    async def deleteFunc(self,ctx,name:str):
        """ 
        Deletes the specified FOB from the database. 
        
        Usage: !fob delete name

        name        - the name of the FOB to be deleted.
       
        
        Example:    !fob delete "Random FOB"    // if there are spaces in the name quotes must be used 
                                                    otherwise just the first word will be used for that variable
                    !fob delete Random          // since neither of the names has a space, no quotes are required

        
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT id FROM fobs WHERE guild = %s and server = %s and name = %s"""

                    await cur.execute(  query,(guild,server,name))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not delete FOB"
                        embedDesc = """There is no FOB with that name!

                        Sorry, nothing was deleted.
                        """
                    else:
                        row = await cur.fetchone()
                        await cur.execute ("DELETE FROM fobs WHERE guild = %s and server = %s and id = %s",(guild,server,row[0]))
                        await conn.commit()

                        embedColor = aqua
                        messageTitle = "Deleted FOB successfully"
                        embedDesc = """The {} FOB was deleted :(
                            May the dark snail have his revenge!!!!""".format (name)

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                await ctx.send(embed=embed)

    @deleteFunc.error
    async def delete_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob delete".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='add', pass_context=True)
    @commands.guild_only()
    async def addFunc(self,ctx,name:str,*args):
        """ 
        Adds fleets to the specified FOB. 
        
        Usage: !fob add name nbFleet type [nbFleet type] [nbFleet type]...

        name        - the name of the FOB to which the fleets will be added.
                    after this at least 1 pair of number type must be present
                    the types are: destroyer, frigate, recon, gunship, trooper, carrier, dreadnought, corvette, patrol, scout, industrial
        
        Example:    !fob add "Random FOB" 2 frigates 2 corvettes 4 carriers    

        
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = True #await self.checkPermissions(ctx,cur, "manage_fobs")

                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT id,locationX,locationY, operating , 
                    IFNULL(`destroyer`, 0) + IFNULL(`frigate`, 0) + IFNULL(`recon`, 0) + IFNULL(`gunship`, 0)
                    + IFNULL(`trooper`, 0) + IFNULL(`carrier`, 0) + IFNULL(`dreadnought`, 0) + IFNULL(`corvette`, 0) 
                    + IFNULL(`patrol`, 0) + IFNULL(`scout`, 0) + IFNULL(`industrial`, 0) as count
                    FROM fobs WHERE guild = %s and server = %s and name = %s"""

                    await cur.execute(  query,(guild,server,name))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not add to the FOB"
                        embedDesc = """There is no FOB with that name!

                        Sorry, nothing was added.
                        """
                    else:
                        row = await cur.fetchone()
                        
                        pattern = re.compile ("(\d*)\s?(destroyer|destro|frigate|frig|recon|dreadnought|dread|corvette|corv|trooper|gunship|bomber|industrial|indie|scout|patrol|carrier)")

                        items = re.finditer(pattern," ".join(args))

                        addedFleets = 0
                        addedString = "Added:\n"
                        for item in items:
                            qty = int(item.group(1))
                            fleet = item.group(2)
                            if item.group(2) == "carrier" :
                                await cur.execute ("UPDATE fobs SET carrier = carrier+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets = addedFleets+ qty
                                addedString = addedString + "{} carrier(s)\n".format(item.group(1))
                            elif item.group(2) == "frigate" or item.group(2) == "frig":
                                await cur.execute ("UPDATE fobs SET frigate = frigate+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} frigate(s)\n".format(item.group(1))
                            elif item.group(2) == "destroyer" or item.group(2) == "destro":
                                await cur.execute ("UPDATE fobs SET destroyer = destroyer+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} destroyer(s)\n".format(item.group(1))
                            elif item.group(2) == "recon":
                                await cur.execute ("UPDATE fobs SET recon = recon+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} recon(s)\n".format(item.group(1))
                            elif item.group(2) == "dreadnought" or item.group(2) == "dread":
                                await cur.execute ("UPDATE fobs SET dreadnought = dreadnought+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} dreadnought(s)\n".format(item.group(1))
                            elif item.group(2) == "corvette" or item.group(2) == "corv":
                                await cur.execute ("UPDATE fobs SET corvette = corvette+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} corvette(s)\n".format(item.group(1))
                            elif item.group(2) == "trooper":
                                await cur.execute ("UPDATE fobs SET trooper = trooper+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} trooper(s)\n".format(item.group(1))
                            elif item.group(2) == "gunship" or item.group(2) == "bomber":
                                await cur.execute ("UPDATE fobs SET gunship = gunship+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} gunship(s)\n".format(item.group(1))
                            elif item.group(2) == "industrial" or item.group(2) == "indie":
                                await cur.execute ("UPDATE fobs SET industrial = industrial+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} industrial(s)\n".format(item.group(1))
                            elif item.group(2) == "patrol":
                                await cur.execute ("UPDATE fobs SET patrol = patrol+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} patrol(s)\n".format(item.group(1))
                            elif item.group(2) == "scout" :
                                await cur.execute ("UPDATE fobs SET scout = scout+%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} scout(s)\n".format(item.group(1))
                            
                        if (row[4]+addedFleets>row[3]):
                            embedColor = red
                            messageTitle = "Operating fleet limit exceeded"
                            embedDesc = """DON'T SEND THE FLEETS. OPERATING FLEET LIMIT EXCEED!!!!!!!

                            Your deployments weren't added to the database"""
                        else:
                            await conn.commit()
                            await cur.execute ("""INSERT INTO fob_history (guild,server,fob,user,changes)
                            VALUES (%s,%s,%s,%s,%s)""", (guild,server,row[0],ctx.message.author.id,addedString))
                            await conn.commit()

                            embedColor = aqua
                            messageTitle = "Added to FOB successfully"
                            embedDesc = "Added {} fleets to {}\n\n".format (addedFleets, name)
                            embedDesc+addedString

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                
                await ctx.send(embed=embed)

    @addFunc.error
    async def add_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob add".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='remove', pass_context=True)
    @commands.guild_only()
    async def removeFunc(self,ctx,name:str,*args):
        """ 
        Removes fleets from the specified FOB. 
        
        Usage: !fob remove name nbFleet type [nbFleet type] [nbFleet type]...

        name        - the name of the FOB from which the fleets will be removed.
                    after this at least 1 pair of number type must be present
                    the types are: destroyer, frigate, recon, gunship, trooper, carrier, dreadnought, corvette, patrol, scout, industrial
        
        Example:    !fob remove "Random FOB" 2 frigates 2 corvettes 4 carriers    

        
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = True #await self.checkPermissions(ctx,cur, "manage_fobs")

                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT id,locationX,locationY, operating , 
                    IFNULL(`destroyer`, 0) + IFNULL(`frigate`, 0) + IFNULL(`recon`, 0) + IFNULL(`gunship`, 0)
                    + IFNULL(`trooper`, 0) + IFNULL(`carrier`, 0) + IFNULL(`dreadnought`, 0) + IFNULL(`corvette`, 0) 
                    + IFNULL(`patrol`, 0) + IFNULL(`scout`, 0) + IFNULL(`industrial`, 0) as count,
                    destroyer,frigate,recon,gunship,trooper,carrier,dreadnought,corvette,patrol,scout,industrial
                    FROM fobs WHERE guild = %s and server = %s and name = %s"""

                    await cur.execute(  query,(guild,server,name))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not remove from the FOB"
                        embedDesc = """There is no FOB with that name!

                        Sorry, nothing was removed.
                        """
                    else:
                        row = await cur.fetchone()
                        
                        pattern = re.compile ("(\d*)\s?(destroyer|destro|frigate|frig|recon|dreadnought|dread|corvette|corv|trooper|gunship|bomber|industrial|indie|scout|patrol|carrier)")

                        items = re.finditer(pattern," ".join(args))
                        addedFleets = 0
                        addedString = "Removed:\n"
                        error = False
                        errorString = ""
                        for item in items:
                            qty = int(item.group(1))
                            fleet = item.group(2)
                            if item.group(2) == "carrier" :
                                if qty>row[10]:
                                    await ctx.send ("You can't remove more carriers than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET carrier = carrier-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets =addedFleets+ qty
                                addedString = addedString + "{} carrier(s)\n".format(item.group(1))
                            elif item.group(2) == "frigate" or item.group(2) == "frig":
                                if qty>row[6]:
                                    await ctx.send ("You can't remove more frigates than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET frigate = frigate-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} frigate(s)\n".format(item.group(1))
                            elif item.group(2) == "destroyer" or item.group(2) == "destro":
                                if qty>row[5]:
                                    await ctx.send ("You can't remove more destroyers than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET destroyer = destroyer-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} destroyer(s)\n".format(item.group(1))
                            elif item.group(2) == "recon":
                                if qty>row[7]:
                                    await ctx.send ("You can't remove more recons than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET recon = recon-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} recon(s)\n".format(item.group(1))
                            elif item.group(2) == "dreadnought" or item.group(2) == "dread":
                                if qty>row[11]:
                                    await ctx.send ("You can't remove more dreadnoughts than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET dreadnought = dreadnought-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} dreadnought(s)\n".format(item.group(1))
                            elif item.group(2) == "corvette" or item.group(2) == "corv":
                                if qty>row[12]:
                                    await ctx.send ("You can't remove more corvettes than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET corvette = corvette-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} corvette(s)\n".format(item.group(1))
                            elif item.group(2) == "trooper":
                                if qty>row[9]:
                                    await ctx.send ("You can't remove more carriers than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET trooper = trooper-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} trooper(s)\n".format(item.group(1))
                            elif item.group(2) == "gunship" or item.group(2) == "bomber":
                                if qty>row[8]:
                                    await ctx.send ("You can't remove more carriers than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET gunship = gunship-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} gunship(s)\n".format(item.group(1))
                            elif item.group(2) == "industrial" or item.group(2) == "indie":
                                if qty>row[15]:
                                    await ctx.send ("You can't remove more carriers than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET industrial = industrial-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} industrial(s)\n".format(item.group(1))
                            elif item.group(2) == "patrol":
                                if qty>row[13]:
                                    await ctx.send ("You can't remove more carriers than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET patrol = patrol-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} patrol(s)\n".format(item.group(1))
                            elif item.group(2) == "scout" :
                                if qty>row[14]:
                                    await ctx.send ("You can't remove more carriers than available on the FOB")
                                    return
                                await cur.execute ("UPDATE fobs SET scout = scout-%s WHERE guild = %s and server = %s and id = %s",(qty,guild,server,row[0]))
                                addedFleets += qty
                                addedString += "{} scout(s)\n".format(item.group(1))
                            
                        if (row[4]-addedFleets<0):
                            embedColor = red
                            messageTitle = "Less than 0 fleets in the FOB??? WTF?"
                            embedDesc = """IF YOU REMOVE THIS, THERE WOULD BE LESS THAN 0 FLEETS IN THE FOB!!!!!!!

                            Your deployments weren't removed from the database"""
                        else:
                            await conn.commit()
                            await cur.execute ("""INSERT INTO fob_history (guild,server,fob,user,changes)
                            VALUES (%s,%s,%s,%s,%s)""", (guild,server,row[0],ctx.message.author.id,addedString))
                            await conn.commit()

                            embedColor = aqua
                            messageTitle = "Removed from the FOB successfully"
                            embedDesc = "Removed {} fleets from {}\n\n".format (addedFleets, name)
                            embedDesc+addedString

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                
                await ctx.send(embed=embed)

    @removeFunc.error
    async def remove_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob remove".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='breakdown',pass_context=True)
    @commands.guild_only()
    async def breakdownFunc(self,ctx,name:str):
        """ 
        Shows the breakdown of fleets for the specified FOB. 
        
        Usage: !fob breakdown name 

        name        - the name of the FOB from which the fleets will be removed.
                    after this at least 1 pair of number type must be present
        
        Example:    !fob breakdown "Random FOB"

        
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = True #await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT id,locationX,locationY, operating , 
                    IFNULL(`destroyer`, 0) + IFNULL(`frigate`, 0) + IFNULL(`recon`, 0) + IFNULL(`gunship`, 0)
                    + IFNULL(`trooper`, 0) + IFNULL(`carrier`, 0) + IFNULL(`dreadnought`, 0) + IFNULL(`corvette`, 0) 
                    + IFNULL(`patrol`, 0) + IFNULL(`scout`, 0) + IFNULL(`industrial`, 0) as count,
                    destroyer,frigate,recon,gunship,trooper,carrier,dreadnought,corvette,patrol,scout,industrial
                    FROM fobs WHERE guild = %s and server = %s and name = %s"""

                    await cur.execute(  query,(guild,server,name))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not get breakdown for FOB"
                        embedDesc = """There is no FOB with that name!

                        Sorry, nothing to be seen.
                        """
                    else:
                        addDetails = True
                        row = await cur.fetchone()

                        embedColor = aqua
                        messageTitle = "Breakdown for {}".format(name)
                        embedDesc = """The station operates **{}/{}** fleets.
                        Here are the details:""".format (row[4],row[3])
                        addDetails = True

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                if addDetails:
                    embed.add_field(name="Name", value="""```{name:s}```""".format (name=name),inline=False)
                    embed.add_field(name="Location", value="/goto {} {}".format (row[1],row[2]),inline=True)
                    embed.add_field(name="Operating", value="{} / {}".format (row[4],row[3]),inline=True)

                    breakdown = ""

                    if row[10]!=0:
                        breakdown = breakdown + "Carriers :\t\t\t**{}** fleets (**{}**)\n".format (row[10], row[10]*200)
                    if row[11]!=0:
                        breakdown = breakdown + "Dreadnoughts :\t\t\t**{}** fleets (**{}**)\n".format (row[11], row[11]*200)
                    if row[6]!=0:
                        breakdown = breakdown + "Frigates :\t\t\t**{}** fleets (**{}**)\n".format (row[6], row[6]*400)
                    if row[5]!=0:
                        breakdown = breakdown + "Destroyers :\t\t\t**{}** fleets (**{}**)\n".format (row[5], row[5]*400)
                    if row[8]!=0:
                        breakdown = breakdown + "Gunships :\t\t\t**{}** fleets (**{}**)\n".format (row[8], row[8]*120)
                    if row[7]!=0:
                        breakdown = breakdown + "Recons :\t\t\t**{}** fleets (**{}**)\n".format (row[7], row[7]*400)
                    if row[13]!=0:
                        breakdown = breakdown + "Patrols :\t\t\t**{}** fleets (**{}**)\n".format (row[13], row[13]*800)
                    if row[12]!=0:
                        breakdown = breakdown + "Corvettes :\t\t\t**{}** fleets (**{}**)\n".format (row[12], row[12]*800)
                    if row[14]!=0:
                        breakdown = breakdown + "Scouts :\t\t\t**{}** fleets (**{}**)\n".format (row[14], row[14]*800)
                    if row[9]!=0:
                        breakdown = breakdown + "Troopers :\t\t\t**{}** fleets (**{}**)\n".format (row[9], row[9]*1)
                    if row[15]!=0:
                        breakdown = breakdown + "Industrials :\t\t\t**{}** fleets (**{}**)\n".format (row[15], row[15]*300)

                    
                    embed.add_field(name="Breakdown", value=breakdown,inline=False)


                await ctx.send(embed=embed)

    @breakdownFunc.error
    async def breakdown_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob breakdown".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='list', pass_context=True)
    @commands.guild_only()
    async def listFunc(self,ctx):
        """ 
        Shows the history of the fleets added and removed from the FOB. 
        
        Usage: !fob history name 

        name        - the name of the FOB from which the fleets will be removed.
                    after this at least 1 pair of number type must be present
        
        Example:    !fob history "Random FOB"

        
        """
        

        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 
        
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = True # await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
               
                    await ctx.send(embed=embed)
                else:
                    query = """SELECT name,locationX,locationY, operating , 
                    IFNULL(`destroyer`, 0) + IFNULL(`frigate`, 0) + IFNULL(`recon`, 0) + IFNULL(`gunship`, 0)
                    + IFNULL(`trooper`, 0) + IFNULL(`carrier`, 0) + IFNULL(`dreadnought`, 0) + IFNULL(`corvette`, 0) 
                    + IFNULL(`patrol`, 0) + IFNULL(`scout`, 0) + IFNULL(`industrial`, 0) as count
                    FROM fobs WHERE guild = %s and server = %s """

                    await cur.execute(  query,(guild,server))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not get list of FOBs"
                        embedDesc = """There are no FOBs defined on this server!
                        Please ask an admin to add one,
                        
                        """
                        embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
               
                        await ctx.send(embed=embed)
                    else:
                        rows = await cur.fetchall()
                        

                        embedColor = purple
                        messageTitle =  "Available FOBs"
                        embedDesc = "The list of FOBs:"
                        

                        rowExpression ='''embed.add_field(name="­", value="""```{name:s}```""".format (name=row[0]),inline=False)
embed.add_field(name="Location", value="/goto **{} {}**".format(row[1],row[2]),inline=True)
embed.add_field(name="Operating Limit", value="{}/{}".format(row[4],row[3]),inline=True)
'''

                        embeds = getEmbeds(ctx,rows, messageTitle,embedDesc, embedColor,rowExpression)

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
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob list".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################


    @fob.command(name='history', pass_context=True)
    @commands.guild_only()
    async def historyFunc(self,ctx,name:str):
        """ 
        Shows the history of the fleets added and removed from the FOB. 
        
        Usage: !fob history name 

        name        - the name of the FOB from which the fleets will be removed.
                    after this at least 1 pair of number type must be present
        
        Example:    !fob history "Random FOB"

        
        """
        

        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 
        
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                    embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
               
                    await ctx.send(embed=embed)
                else:
                    query = """SELECT f.name, fh.user, fh.changes, fh.date
                                FROM fob_history fh
                                LEFT JOIN fobs f
                                ON fh.fob = f.id 
                                WHERE fh.guild = %s and fh.server = %s and f.name = %s and fh.date < < (NOW() - INTERVAL 20 HOUR)"""
                    
                    await cur.execute(  query,(guild,server,name))
                   
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not get history for FOB"
                        embedDesc = """There is no history for the FOB with that name!

                        Sorry, nothing to be seen.
                        """
                        embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
               
                        await ctx.send(embed=embed)
                    else:
                        rows = await cur.fetchall()
                        logList = []
                        for row in rows:
                            u = ctx.message.guild.get_member(row[1])
                            un = u.display_name if u is not None else "MIA Member"
                            logList.append({'name':row[0],'date':row[3], 'user': un,'message': row[2].replace("\n"," ")} )

                        embedColor = purple
                        messageTitle =  "Change history for {}".format(name)
                        embedDesc = "The list of changes for {}:".format(name)
                        

                        rowExpression ='''embed.add_field(name="­", value="""```{name:s}```""".format (name=row["user"]),inline=False)
embed.add_field(name="FOB", value=row["name"],inline=True)
embed.add_field(name="Date", value="{time:s}".format(time=row["date"].strftime("%d %b %Y, %H:%M:%S")),inline=True)
embed.add_field(name="Details",value=row["message"],inline=False)
'''
                       
                        embeds = getEmbeds(ctx,logList, messageTitle,embedDesc, embedColor,rowExpression)

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

    @historyFunc.error
    async def history_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob history".
            ''')
        await ctx.send(error) #don't forget  to remove this in live

#########################################################################################################

    @fob.command(name='delHistory', pass_context=True)
    @commands.guild_only()
    async def delHistoryFunc(self,ctx,name:str):
        """ 
        Shows the history of the fleets added and removed from the FOB. 
        
        Usage: !fob delHistory name 

        name        - the name of the FOB from which the fleets will be removed.
                    after this at least 1 pair of number type must be present
                    
        
        Example:    !fob delHistory "Random FOB"

        
        """
        server, cmd = chInfo (ctx)
        if server is None or  cmd is None:
            return
        
        if cmd != "fob-op-limit":
            await ctx.send ("This is not the place to use this command!. Please use *servername*-fob-op-limit")
            return 

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                guild = ctx.message.guild.id
                
                allowed = await self.checkPermissions(ctx,cur, "manage_fobs")
                addDetails = False
                if not allowed:
                    embedColor = red
                    messageTitle = "Error"
                    embedDesc = """You do not have permission to manage FOBs.
                    Sorry!
                    """
                else:
                    query = """SELECT f.name, fh.fob,fh.id
                                FROM fob_history fh
                                LEFT JOIN fobs f
                                ON fh.fob = f.id 
                                WHERE fh.guild = %s and fh.server = %s and f.name = %s"""

                    await cur.execute(  query,(guild,server,name))
                    
                    if cur.rowcount == 0:
                        embedColor = red
                        messageTitle = "Could not delete FOB"
                        embedDesc = """There is no history for a FOB with that name!

                        Sorry, nothing was deleted.
                        """
                    else:
                        row = await cur.fetchone()
                        await cur.execute ("DELETE FROM fob_history WHERE guild = %s and server = %s and fob = %s",(guild,server,row[1]))
                        await conn.commit()

                        embedColor = aqua
                        messageTitle = "Deleted FOB history successfully"
                        embedDesc = """The {} history was deleted.""".format (name)

                embed = discord.Embed(
                        type= "rich",
                        title=messageTitle,
                        description=embedDesc,
                        color = embedColor)
                await ctx.send(embed=embed)

    @delHistoryFunc.error
    async def delHistory_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
            '''
            Sorry but there is an error in your command. Please use "!help fob delHistory".
            ''')
        await ctx.send(error) #don't forget  to remove this in live