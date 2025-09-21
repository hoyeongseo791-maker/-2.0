import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime
import pytz
import os
import random
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 환경변수 로딩
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", "0"))
CHAT_CHANNEL_ID = int(os.getenv("CHAT_CHANNEL_ID", "0"))
R4_ROLE_ID = int(os.getenv("R4_ROLE_ID", "0"))
MANAGER_ROLE_ID = int(os.getenv("MANAGER_ROLE_ID", "0"))
R3_ROLE_ID = int(os.getenv("R3_ROLE_ID", "0"))
KOREAN_ROLE_ID = int(os.getenv("KOREAN_ROLE_ID", "0"))
ENGLISH_ROLE_ID = int(os.getenv("ENGLISH_ROLE_ID", "0"))

loop_flags = {"morning": False, "sunday": False}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    chat_channel = bot.get_channel(CHAT_CHANNEL_ID)
    if chat_channel:
        await chat_channel.send("영이봇2.0 준비완료!")

    if not morning_message.is_running():
        morning_message.start()
    if not sunday_message.is_running():
        sunday_message.start()

# 역할 버튼
class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="R4", style=discord.ButtonStyle.primary, custom_id="r4"))
        self.add_item(Button(label="관리자", style=discord.ButtonStyle.success, custom_id="manager"))
        self.add_item(Button(label="R3~1", style=discord.ButtonStyle.danger, custom_id="r3"))

@bot.command(name="역할")
async def role_cmd(ctx):
    await ctx.send("원하시는 역할을 선택해주세요:", view=RoleView())

# 국가 버튼
class CountryView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Korean", style=discord.ButtonStyle.primary, custom_id="kr"))
        self.add_item(Button(label="English", style=discord.ButtonStyle.success, custom_id="en"))

@bot.command(name="국가")
async def country_cmd(ctx):
    await ctx.send("국가를 선택해주세요:", view=CountryView())

# 명령어 안내
@bot.command(name="명령어")
async def command_list(ctx):
    await ctx.send("사용 가능한 명령어: !역할 / !국가 / !명령어 / !청소 / !영이")

# 랜덤 메시지
@bot.command(name="영이")
async def youngi(ctx):
    messages = ["안녕하세요~", "오늘도 즐겁게!", "무엇을 도와드릴까요?", "영이는 귀여워요!", "오늘도 파이팅!", "나 불렀어?"]
    await ctx.send(random.choice(messages))

# 청소
@bot.command(name="청소")
async def clean(ctx):
    deleted = await ctx.channel.purge(limit=5)
    await ctx.send(f"{len(deleted)}개의 메시지를 삭제했습니다.", delete_after=3)

# 버튼 핸들링
@bot.event
async def on_interaction(interaction):
    if interaction.data["component_type"] == 2:
        cid = interaction.data["custom_id"]
        member = interaction.user
        guild = member.guild

        if cid == "r4":
            await member.add_roles(guild.get_role(R4_ROLE_ID))
            await interaction.response.send_message("R4 역할이 부여되었습니다!", ephemeral=True)
        elif cid == "manager":
            await member.add_roles(guild.get_role(MANAGER_ROLE_ID))
            await interaction.response.send_message("관리자 역할이 부여되었습니다!", ephemeral=True)
        elif cid == "r3":
            await member.add_roles(guild.get_role(R3_ROLE_ID))
            await interaction.response.send_message("R3~1 역할이 부여되었습니다!", ephemeral=True)
        elif cid == "kr":
            await member.add_roles(guild.get_role(KOREAN_ROLE_ID))
            await interaction.response.send_message("Korean 역할이 부여되었습니다!", ephemeral=True)
        elif cid == "en":
            await member.add_roles(guild.get_role(ENGLISH_ROLE_ID))
            await interaction.response.send_message("English 역할이 부여되었습니다!", ephemeral=True)

# 새로운 유저
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        await channel.send(f"""{member.mention}님 환영합니다!!

환영합니다!! 간단하게 서버소개 도와드릴게요! 
1. 서버에 역할이 존재합니다. /!역할/ /!국가/를 채팅에 입력하시면 선택지가 생성됩니다. 선택후에 채널입장권한이 부여됩니다
2. 상호간에 즐거운 게임환경을 위해 규칙채널에서 규칙확인후 이용바랍니다.
3. 추가적인 서버증설혹은 오류있을시 서버관리자에게 문의 부탁드립니다.""")

# 정기 메시지
@tasks.loop(minutes=1)
async def morning_message():
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    if now.hour == 9 and now.minute == 0:
        channel = bot.get_channel(CHAT_CHANNEL_ID)
        if channel:
            await channel.send("좋은아침이에요! 다들 라오킹접속해서 일일보상 챙겨!")

@tasks.loop(minutes=1)
async def sunday_message():
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    if now.weekday() == 6 and now.hour == 23 and now.minute == 0:
        channel = bot.get_channel(CHAT_CHANNEL_ID)
        if channel:
            await channel.send("다들 주말동안 잘 쉬었어? 내일은 일하러 가야하니까 다들 일찍 자 고생해!!")

keep_alive()
bot.run(TOKEN)
