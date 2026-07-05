import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from typing import Optional
import json
import os

TOKEN = "MTMxNzYwNDEzMzIzMDA4NDEzNg.G14Bai.iS8D03tSkK9Cu88Gud1OzUa5DxkJaU1pAtiYyc"
PREFIX = "<"
WHITELIST_FILE = "whitelist.json"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ============================================
# WHITELIST SYSTEM
# ============================================

def load_whitelist():
    try:
        if os.path.exists(WHITELIST_FILE):
            with open(WHITELIST_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_whitelist(data):
    with open(WHITELIST_FILE, 'w') as f:
        json.dump(data, f, indent=4)

whitelist = load_whitelist()

def is_whitelisted(user_id: int, guild_id: int) -> bool:
    guild_id_str = str(guild_id)
    if guild_id_str not in whitelist:
        return False
    return str(user_id) in whitelist[guild_id_str]

def add_to_whitelist(user_id: int, guild_id: int):
    guild_id_str = str(guild_id)
    if guild_id_str not in whitelist:
        whitelist[guild_id_str] = []
    if str(user_id) not in whitelist[guild_id_str]:
        whitelist[guild_id_str].append(str(user_id))
        save_whitelist(whitelist)
        return True
    return False

def remove_from_whitelist(user_id: int, guild_id: int):
    guild_id_str = str(guild_id)
    if guild_id_str in whitelist:
        if str(user_id) in whitelist[guild_id_str]:
            whitelist[guild_id_str].remove(str(user_id))
            save_whitelist(whitelist)
            return True
    return False

# ============================================
# COMMANDS
# ============================================

@bot.tree.command(name="whitelist", description="[ADMIN] Add user to whitelist")
@app_commands.describe(user="The user to whitelist")
async def slash_whitelist(interaction: discord.Interaction, user: discord.User):
    try:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only admins can use this command!", ephemeral=True)
            return
        
        if add_to_whitelist(user.id, interaction.guild.id):
            embed = discord.Embed(
                title="✅ User Whitelisted",
                description=f"{user.mention} can now use bot commands!",
                color=discord.Color.green()
            )
            embed.set_footer(text="Made by Ibra | Only Revolution")
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ {user.mention} is already whitelisted!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="unwhitelist", description="[ADMIN] Remove user from whitelist")
@app_commands.describe(user="The user to unwhitelist")
async def slash_unwhitelist(interaction: discord.Interaction, user: discord.User):
    try:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only admins can use this command!", ephemeral=True)
            return
        
        if remove_from_whitelist(user.id, interaction.guild.id):
            embed = discord.Embed(
                title="✅ User Unwhitelisted",
                description=f"{user.mention} can no longer use bot commands!",
                color=discord.Color.red()
            )
            embed.set_footer(text="Made by Ibra | Only Revolution")
            embed.timestamp = datetime.now()
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"❌ {user.mention} is not whitelisted!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="join", description="Join VC for X hours")
@app_commands.describe(hours="Number of hours to stay (default: 100)")
async def slash_join(interaction: discord.Interaction, hours: Optional[int] = 100):
    await interaction.response.send_message("⏳ Joining...", ephemeral=True)
    
    try:
        # Check whitelist
        if not is_whitelisted(interaction.user.id, interaction.guild.id) and not interaction.user.guild_permissions.administrator:
            await interaction.edit_original_response(content="❌ You are not whitelisted! Ask an admin to add you.")
            return
        
        if not interaction.user.voice:
            await interaction.edit_original_response(content="❌ You need to be in a voice channel!")
            return
        
        if hours < 1:
            await interaction.edit_original_response(content="❌ Must be at least 1 hour!")
            return
        
        if hours > 8760:  # 1 year max
            await interaction.edit_original_response(content="❌ Max 8760 hours (1 year)!")
            return
        
        voice_channel = interaction.user.voice.channel
        
        if interaction.guild.voice_client:
            await interaction.edit_original_response(content="❌ Already in a voice channel!")
            return
        
        await voice_channel.connect()
        leave_time = datetime.now() + timedelta(hours=hours)
        
        embed = discord.Embed(
            title="🔊 Joined Voice Channel",
            description=f"Joined **{voice_channel.name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="⏰ Will stay for", value=f"**{hours} hours**", inline=True)
        embed.add_field(name="📅 Leaves at", value=f"<t:{int(leave_time.timestamp())}:F>", inline=True)
        embed.set_footer(text="Made by Ibra | Only Revolution")
        embed.timestamp = datetime.now()
        
        await interaction.edit_original_response(content=None, embed=embed)
        
        # Auto leave after hours
        await asyncio.sleep(hours * 3600)
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.followup.send(f"🔊 Left **{voice_channel.name}** after {hours} hours!")
            
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error: {str(e)}")

@bot.tree.command(name="leave", description="Leave voice channel")
async def slash_leave(interaction: discord.Interaction):
    await interaction.response.send_message("⏳ Leaving...", ephemeral=True)
    
    try:
        if not is_whitelisted(interaction.user.id, interaction.guild.id) and not interaction.user.guild_permissions.administrator:
            await interaction.edit_original_response(content="❌ You are not whitelisted!")
            return
        
        if not interaction.guild.voice_client:
            await interaction.edit_original_response(content="❌ Not in a voice channel!")
            return
        
        await interaction.guild.voice_client.disconnect()
        
        embed = discord.Embed(
            title="🔊 Left Voice Channel",
            description="Left the voice channel!",
            color=discord.Color.red()
        )
        embed.set_footer(text="Made by Ibra | Only Revolution")
        embed.timestamp = datetime.now()
        
        await interaction.edit_original_response(content=None, embed=embed)
    except Exception as e:
        await interaction.edit_original_response(content=f"❌ Error: {str(e)}")

@bot.tree.command(name="whitelist_list", description="[ADMIN] Show all whitelisted users")
async def slash_whitelist_list(interaction: discord.Interaction):
    try:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Admin only!", ephemeral=True)
            return
        
        guild_id = str(interaction.guild.id)
        if guild_id not in whitelist or not whitelist[guild_id]:
            await interaction.response.send_message("❌ No whitelisted users!", ephemeral=True)
            return
        
        users = whitelist[guild_id]
        user_mentions = []
        for user_id in users:
            user = bot.get_user(int(user_id))
            if user:
                user_mentions.append(user.mention)
            else:
                user_mentions.append(f"<@{user_id}>")
        
        embed = discord.Embed(
            title="📋 Whitelisted Users",
            description="\n".join(user_mentions) or "None",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Made by Ibra | Only Revolution")
        embed.timestamp = datetime.now()
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="ping", description="Check bot latency")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! **{round(bot.latency * 1000)}ms**")

# ============================================
# PREFIX COMMANDS
# ============================================

@bot.command(name='join')
async def prefix_join(ctx, hours: int = 100):
    try:
        if not is_whitelisted(ctx.author.id, ctx.guild.id) and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You are not whitelisted!")
            return
        
        if not ctx.author.voice:
            await ctx.send("❌ You need to be in a voice channel!")
            return
        
        if hours < 1:
            await ctx.send("❌ Must be at least 1 hour!")
            return
        
        voice_channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.send("❌ Already in a voice channel!")
            return
        
        await voice_channel.connect()
        leave_time = datetime.now() + timedelta(hours=hours)
        
        embed = discord.Embed(
            title="🔊 Joined Voice Channel",
            description=f"Joined **{voice_channel.name}**!",
            color=discord.Color.green()
        )
        embed.add_field(name="⏰ Will stay for", value=f"**{hours} hours**", inline=True)
        embed.add_field(name="📅 Leaves at", value=f"<t:{int(leave_time.timestamp())}:F>", inline=True)
        embed.set_footer(text="Made by Ibra | Only Revolution")
        embed.timestamp = datetime.now()
        
        await ctx.send(embed=embed)
        
        await asyncio.sleep(hours * 3600)
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send(f"🔊 Left **{voice_channel.name}** after {hours} hours!")
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='leave')
async def prefix_leave(ctx):
    try:
        if not is_whitelisted(ctx.author.id, ctx.guild.id) and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ You are not whitelisted!")
            return
        
        if not ctx.voice_client:
            await ctx.send("❌ Not in a voice channel!")
            return
        
        await ctx.voice_client.disconnect()
        await ctx.send("🔊 Left the voice channel!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='whitelist')
@commands.has_permissions(administrator=True)
async def prefix_whitelist(ctx, user: discord.User):
    if add_to_whitelist(user.id, ctx.guild.id):
        await ctx.send(f"✅ {user.mention} is now whitelisted!")
    else:
        await ctx.send(f"❌ {user.mention} is already whitelisted!")

@bot.command(name='unwhitelist')
@commands.has_permissions(administrator=True)
async def prefix_unwhitelist(ctx, user: discord.User):
    if remove_from_whitelist(user.id, ctx.guild.id):
        await ctx.send(f"✅ {user.mention} is no longer whitelisted!")
    else:
        await ctx.send(f"❌ {user.mention} is not whitelisted!")

@bot.command(name='whitelist_list')
@commands.has_permissions(administrator=True)
async def prefix_whitelist_list(ctx):
    guild_id = str(ctx.guild.id)
    if guild_id not in whitelist or not whitelist[guild_id]:
        await ctx.send("❌ No whitelisted users!")
        return
    
    users = whitelist[guild_id]
    user_mentions = []
    for user_id in users:
        user = bot.get_user(int(user_id))
        if user:
            user_mentions.append(user.mention)
        else:
            user_mentions.append(f"<@{user_id}>")
    
    await ctx.send(f"📋 Whitelisted Users:\n" + "\n".join(user_mentions))

@bot.command(name='ping')
async def prefix_ping(ctx):
    await ctx.send(f"🏓 Pong! **{round(bot.latency * 1000)}ms**")

# ============================================
# EVENTS
# ============================================
@bot.event
async def on_ready():
    print("=" * 50)
    print("🔊 VC STAY BOT - FOREVER")
    print("=" * 50)
    print(f"✅ Logged in as: {bot.user}")
    print(f"📡 Connected to: {len(bot.guilds)} servers")
    print(f"🔤 Prefix: {PREFIX}")
    print(f"📋 Whitelist: {len(whitelist)} servers")
    print("=" * 50)
    
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Only Revolution"
        )
    )
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync error: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)
