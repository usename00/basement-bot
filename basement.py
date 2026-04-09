import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= READY =================
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(e)

    print(f"🔥 Logged in as {bot.user}")

# ================= SLASH COMMANDS =================

@bot.tree.command(name="helloworld", description="test")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("hello")

# ----------- KICK -----------
@bot.tree.command(name="kick", description="kick a member")
@commands.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("you cant kick a higher role member", ephemeral=True)
        return

    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"kicked {member} | reason: {reason}")
    except:
        await interaction.response.send_message("you cant kick this member", ephemeral=True)

# ----------- BAN -----------
@bot.tree.command(name="ban", description="ban a member")
@commands.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if member.top_role >= interaction.user.top_role:
        await interaction.response.send_message("you cant ban a higher role member", ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"user banned {member} | reason: {reason}")
    except:
        await interaction.response.send_message("i cant ban this member", ephemeral=True)

# ================= TOKEN =================
token = os.getenv("TOKEN")

if not token:
    print("❌ مفيش TOKEN")
else:
bot.run(TOKEN)

# ================= LOGS =================

LOG_CHANNEL_ID = 1491880119638163487  # حط هنا ID الروم بتاع اللوجات

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"member joined: {member.mention}")

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"member left: {member}")

@bot.event
async def on_member_ban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"user banned: {user}")

@bot.event
async def on_member_unban(guild, user):
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel:
        await channel.send(f"user unbanned: {user}")
