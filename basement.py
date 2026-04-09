import discord
from discord.ext import commands
import os

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# ================== BOT ==================
bot = commands.Bot(command_prefix="!", intents=intents)

# ================== READY ==================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ================== COMMANDS ==================
@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong!")

@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command()
async def server(ctx):
    await ctx.send(f"📊 عدد الأعضاء: {ctx.guild.member_count}")

# ================== KICK ==================
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason"):
    try:
        await member.kick(reason=reason)
        await ctx.send(f"👢 تم طرد {member} | السبب: {reason}")
    except:
        await ctx.send("❌ مقدرتش أطرده")

# ================== BAN ==================
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    try:
        await member.ban(reason=reason)
        await ctx.send(f"🔨 تم حظر {member} | السبب: {reason}")
    except:
        await ctx.send("❌ مقدرتش أبنده")

# ================== ERRORS ==================
@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ معندكش صلاحية")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ لازم تحدد الشخص")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ معندكش صلاحية")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ لازم تحدد الشخص")

# ================== TOKEN ==================
token = os.getenv("TOKEN")

if not token:
    print("❌ مفيش TOKEN! حطه في Railway Variables")
else:
    bot.run(token)
