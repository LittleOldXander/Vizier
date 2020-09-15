import config

from helper import *
import discord
from discord.ext import commands
from discord.utils import get
from datetime import datetime



class Permission(commands.Cog):

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
    async def permission(self,ctx):
        '''
        Category for adding/removing/listing permissions.

        allowed_permissions = {perms:s}
        '''.format(perms = str(allowed_permissions))
        

        if ctx.invoked_subcommand is None:
            await ctx.send("Unknown request or poorly written. Please be more specific.\nIf you need help on this command, just type \"!help permission\".")

    


    @permission.command(name='add',pass_context=True)
    @commands.guild_only()
    async def add(self,ctx,permission:str ="", tr:str=""):
        '''Adds specified permission to specified role
        
        Usage: Usage: !permission add permission(mandatory) roleName(mandatory)

        permission - the permission you want to give to the specified role
                        Available permissions: {perms:s}
        target - the name of the role you want to give the permission


        Example:    !permission add delete_stations Oligarchs
        
        '''.format(perms = str(allowed_permissions))
        userid = ctx.message.author.id
        guild = ctx.message.guild.id

        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if not await self.checkPermissions(ctx,cur,"admin",permission):
                    await ctx.send ("You do not have permission to use this admin command.")
                    return

                if permission not in allowed_permissions:
                    await ctx.send ("Unknown permission. Please use '!help permission' for allowed permissions")
                    return

                roles = ctx.message.guild.roles
                targetRole = -1
                foundRole = False
                for role in roles:
                    if role.name == tr:
                        targetRole = role.id
                        foundRole=True
                        break

                if not foundRole:
                    await ctx.send ( "The role you targeted doesn't exist. Please check your spelling")
                    return


                await cur.execute("SELECT id, value FROM permissions WHERE guild = %s and reference = %s and target = %s",
                                    (guild,permission,targetRole))
                row =  await cur.fetchone()
                if row == None:
                    await cur.execute("INSERT INTO permissions(guild,target,reference,value) VALUES(%s,%s,%s,1)",
                                        (guild, targetRole,permission))
                else:
                    if (row[1]==1):
                        await ctx.send("The role '{role:s}' already had permission for '{ref:s}'. Nothing was updated!'".format(role=tr,ref=permission))
                        return
                    await cur.execute("UPDATE permissions SET value=1 where id = %s",
                                        (row[0]))
                await conn.commit()
                await ctx.send("The role '{role:s}' has been given permission for '{ref:s}'. The dark snail rises!'".format(role=tr,ref=permission))
    
    @add.error
    async def add_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('''Sorry but there is an error in your command.

                            Usage: !permission add permissionName role                        
                            ''')
        await ctx.send(error) #don't forget  to remove this in live

    @permission.command(name='remove',pass_context=True)
    @commands.guild_only()
    async def remove(self,ctx,permission:str ="", tr:str=""):
        '''Removes specified permission from specified role
        
        Usage: Usage: !permission remove permission(mandatory) roleName(mandatory)

        permission - the permission you want to give to the specified role
                        Available permissions: {perms:s}
        target - the name of the role you want to remove the permission from


        Example:    !permission add delete_stations Oligarchs
        
        '''.format(perms = str(allowed_permissions))

        userid = ctx.message.author.id
        guild = ctx.message.guild.id
      
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if not self.checkPermissions(ctx,cur,"admin",permission):
                    await ctx.send ("You do not have permission to use this admin command.")
                    return

                if permission not in allowed_permissions:
                    await ctx.send ("Unknown permission. Please use '!help permission' for allowed permissions")
                    return

                roles = ctx.message.guild.roles
                targetRole = -1
                foundRole = False
                for role in roles:
                    if role.name == tr:
                        targetRole = role.id
                        foundRole=True
                        break

                if not foundRole:
                    await ctx.send ( "The role you targeted doesn't exist. Please check your spelling")
                    return


                await cur.execute("SELECT id, value FROM permissions WHERE guild = %s and reference = %s and target = %s",
                                    (guild,permission,targetRole))
                row =  await cur.fetchone()
                if row == None:
                    await ctx.send("The role '{role:s}' doesn't have permission for '{ref:s}'. Nothing was removed!'".format(role=tr,ref=permission))
                    return
                else:
                    if (row[1]==0):
                        await ctx.send("The role '{role:s}' doesn't have permission for '{ref:s}. Nothing was removed!'".format(role=tr,ref=permission))
                        return
                    await cur.execute("UPDATE permissions SET value=0 where id = %s",
                                        (row[0]))
                    await conn.commit()
                await ctx.send("The permission '{ref:s}' has been revoked permission for '{role:s}'. The dark snail is hungry!'".format(role=tr,ref=permission))
    
    @remove.error
    async def remove_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('''Sorry but there is an error in your command.

                            Usage: !permission remove permissionName role                        
                            ''')
        await ctx.send(error) #don't forget  to remove this in live

    @permission.command(name='list', help='Lists all permissions granted on this server',pass_context=True)
    @commands.guild_only()
    async def list(self,ctx,target:str ="all"):
        userid = ctx.message.author.id
        guild = ctx.message.guild.id
      
        async with self.bot.pool.acquire() as conn:
            async with conn.cursor() as cur:
                if not self.checkPermissions(ctx,cur,"admin"):
                    await ctx.send ("You do not have permission to use this admin command.")
                    return
                if target == "all":
                    await cur.execute("SELECT target, reference FROM permissions WHERE guild = %s and value = 1",
                                    (guild))
                else:
                    await cur.execute("SELECT target, reference FROM permissions WHERE guild = %s and reference = %s and value = 1",
                                    (guild,target))
                if cur.rowcount == 0:
                    await ctx.send ("There are no permissions for this server @ {perm:s}".format(perm=target))
                    return
                rows = await cur.fetchall()
                returnStr = "The following permissions have been set:\n\n"
                for row in rows:
                    role = get(ctx.message.guild.roles, id=row[0])
                    returnStr += "{perm:s}\t|\t{role}\n".format(perm = row[1],role = role.name)
                
                await ctx.send (returnStr)
    @list.error
    async def list_error(self,ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('''Sorry but there is an error in your command.

                            Usage: !permission list                        
                            ''')
        await ctx.send(error) #don't forget  to remove this in live