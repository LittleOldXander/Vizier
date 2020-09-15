import config
import math, re
import discord

allowed_permissions = ["list_stations","delete_stations", "cleanup_stations","delete_requests","manage_fobs", "admin"]


red = discord.Colour(0xFF0000)
purple = discord.Colour(0x800080)
orange = discord.Colour(0xFF5E13)
aqua = discord.Colour(0x7FFFD4)
green = discord.Colour(0x32CD32)


def chInfo (ctx):
    server = None
    command = None
    pattern = re.compile (config.CHANNEL_RE)
    match = re.match(pattern, ctx.message.channel.name)
    if (match):
        server = match.group(1)
        command = match.group(2)
    if server =="":
        server = None
    if command == "":
        command = None
    return server,command

def getIdByName(ctx, name):
    result = None
    users = ctx.message.guild.members

    for user in users:
        if user.display_name == name:
            result = user.id
    
    return result



def getEmbeds (ctx,rows,messageTitle,description,embedColor,rowExpression):
    embed = None
    embeds = []
    curItem = 0 
    curPage = 1
    noItems = 0

    print ("RESULTS_PER_PAGE:{} rows count:{}".format (config.RESULTS_PER_PAGE, len(rows)))

    if config.RESULTS_PER_PAGE<len(rows):
        noItems = config.RESULTS_PER_PAGE

    for row in rows:
        if (curItem % config.RESULTS_PER_PAGE == 0):
            if curPage * config.RESULTS_PER_PAGE<len(rows):
                noItems = config.RESULTS_PER_PAGE
            else:
                noItems = len(rows)-(curPage-1)*config.RESULTS_PER_PAGE
            sItem = (curPage-1)*config.RESULTS_PER_PAGE+1
            if (description != "­­"):
                embed = discord.Embed(
                    type= "rich",
                    title=messageTitle+" | {start:d} - {end:d} / {total:d}".format(start = sItem, end = sItem + noItems -1, total = len(rows)),
                    description = description,
                    color = embedColor)
            else:
                embed = discord.Embed(
                    type= "rich",
                    title=messageTitle+" | {start:d} - {end:d} / {total:d}".format(start = sItem, end = sItem + noItems -1, total = len(rows)),
                    color = embedColor)

        exec(rowExpression)

        curItem+=1
        if curItem == len(rows) or curItem % config.RESULTS_PER_PAGE == config.RESULTS_PER_PAGE-1:
            embeds.append(embed)
            curPage+=1

    return embeds



def hexDistance(start, dest):
    if (start.x == dest.x):
        return abs(dest.y - start.y)
    elif (start.y == dest.y):
        return abs(dest.x - start.x)
    else:
        dx = abs(dest.x - start.x)
        dy = abs(dest.y - start.y)
    if start.y < dest.y:
        return dx + dy - int(math.ceil(dx / 2.0))
    else:
        return dx + dy - int(math.floor(dx / 2.0))

class Point:
    def __init__(self,x_init,y_init):
        self.x = x_init
        self.y = y_init

    def shift(self, x, y):
        self.x += x
        self.y += y

    def __repr__(self):
        return "".join(["Point(", str(self.x), ",", str(self.y), ")"])