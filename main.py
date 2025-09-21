# 영이봇 2.0 - 메인 파일 (수정 보완 버전)
import os
import random
from datetime import datetime

import pytz
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button

from keep_alive import keep_alive

# -------- Intents / Bot --------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------- Env helpers --------
def get_token(key: str) -> str:
    v = os.getenv(key, "").strip()
    if not v:
        print(f"[WARN] 환경변수 {key} 가 비어있습니다.")
    return v

def get_id(key: str) -> int:
    v = os.getenv(key, "").strip()
    try:
        return int(v)
    except Exception:
        if v:
            print(f"[WARN] 환경변수 {key} 값이 정수가 아닙니다: {v}")
        return 0

# 필수 토큰
DISCORD_BOT_TOKEN = get_token("DISCORD_BOT_TOKEN")

# 채널 ID
WELCOME_CHANNEL_ID = get_id("WELCOME_CHANNEL_ID")   # 🖐️환영합니다🖐️
CHAT_CHANNEL_ID    = get_id("CHAT_CHANNEL_ID")      # 🔊수다방🔊
ROLE_REQUEST_CHANNEL_ID = get_id("ROLE_REQUEST_CHANNEL_ID")  # 역할신청방

# 역할 ID
ROLE_R4_ID     = get_id("ROLE_R4_ID")        # R4
ROLE_ADMIN_ID  = get_id("ROLE_ADMIN_ID")     # 관리자
ROLE_R3_1_ID   = get_id("ROLE_R3_1_ID")      # R3~1

ROLE_KR_ID     = get_id("ROLE_KOREAN_ID")    # Korean
ROLE_EN_ID     = get_id("ROLE_ENGLISH_ID")   # English

# 루프 중복 방지 플래그
loops_started = False

SEOUL = pytz.timezone("Asia/Seoul")

# -------- Persistent Views (역할/국가 버튼) --------
class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="R4", style=discord.ButtonStyle.primary, custom_id="role_r4"))
        self.add_item(Button(label="관리자", style=discord.ButtonStyle.danger, custom_id="role_admin"))
        self.add_item(Button(label="R3~1", style=discord.ButtonStyle.success, custom_id="role_r3_1"))

class CountryView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Korean", style=discord.ButtonStyle.primary, custom_id="country_kr"))
        self.add_item(Button(label="English", style=discord.ButtonStyle.success, custom_id="country_en"))

# -------- Bot Events --------
@bot.event
async def on_ready():
    global loops_started
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

    bot.add_view(RoleView())
    bot.add_view(CountryView())

    chat = bot.get_channel(CHAT_CHANNEL_ID)
    if chat:
        await chat.send("영이봇2.0준비완료!")

    if not loops_started:
        if not every_morning.is_running():
            every_morning.start()
        if not sunday_11pm.is_running():
            sunday_11pm.start()
        loops_started = True

@bot.event
async def on_member_join(member: discord.Member):
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if ch:
        text = (
            "환영합니다!! 간단하게 서버소개 도와드릴게요!\n"
            "1. 서버에 역할이 존재합니다. /!역할/ /!국가/를 채팅에 입력하시면 선택지가 생성됩니다. "
            "선택후에 채널입장권한이 부여됩니다\n"
            "2. 상호간에 즐거운 게임환경을 위해 규칙채널에서 규칙확인후 이용바랍니다.\n"
            "3. 추가적인 서버증설혹은 오류있을시 서버관리자에게 문의 부탁드립니다."
        )
        await ch.send(f"{member.mention}\n{text}")

# -------- Button Handlers --------
async def safe_add_role(inter: discord.Interaction, role_id: int, success_text: str):
    if not inter.response.is_done():
        await inter.response.defer(ephemeral=True)

    guild = inter.guild
    member = inter.user

    role = guild.get_role(role_id) if guild else None
    if role is None:
        await inter.followup.send(f"역할(ID {role_id})을 찾을 수 없어요.", ephemeral=True)
        return

    try:
        await member.add_roles(role, reason="button assign")
        await inter.followup.send(success_text, ephemeral=True)
    except discord.Forbidden:
        await inter.followup.send("봇 권한이 부족합니다. (역할 관리 권한 확인)", ephemeral=True)
    except discord.HTTPException:
        await inter.followup.send("역할 부여 실패(디스코드 오류).", ephemeral=True)

@bot.event
async def on_interaction(inter: discord.Interaction):
    data = inter.data or {}
    cid = data.get("custom_id")
    if not cid:
        return

    if cid == "role_r4":
        req_ch = bot.get_channel(ROLE_REQUEST_CHANNEL_ID)
        if req_ch:
            await req_ch.send(f"{inter.user.mention} R4 역할 신청은 양식대로 올려주시면 심사 후 권한이 부여됩니다.")
        await inter.response.send_message("R4 신청 안내가 역할신청방에 전송되었습니다.", ephemeral=True)

    elif cid == "role_admin":
        req_ch = bot.get_channel(ROLE_REQUEST_CHANNEL_ID)
        if req_ch:
            await req_ch.send(f"{inter.user.mention} 관리자 역할 신청은 양식대로 올려주시면 심사 후 권한이 부여됩니다.")
        await inter.response.send_message("관리자 신청 안내가 역할신청방에 전송되었습니다.", ephemeral=True)

    elif cid == "role_r3_1":
        await safe_add_role(inter, ROLE_R3_1_ID, "R3~1 역할을 부여했습니다!")

    elif cid == "country_kr":
        await safe_add_role(inter, ROLE_KR_ID, "Korean 역할을 부여했습니다!")

    elif cid == "country_en":
        await safe_add_role(inter, ROLE_EN_ID, "English 역할을 부여했습니다!")

# -------- Commands --------
@bot.command(name="역할")
async def cmd_roles(ctx: commands.Context):
    await ctx.send("원하는 역할을 선택하세요:", view=RoleView())

@bot.command(name="국가")
async def cmd_country(ctx: commands.Context):
    await ctx.send("국가를 선택하세요:", view=CountryView())

@bot.command(name="명령어")
async def cmd_help(ctx: commands.Context):
    await ctx.send(
        "사용 가능한 명령어:\n"
        "• `!역할`  역할 선택 버튼 표시\n"
        "• `!국가`  국가 선택 버튼 표시\n"
        "• `!청소`  최근 5개 메시지 삭제\n"
        "• `!명령어`  이 도움말 표시\n"
        "• `!영이`  랜덤 멘트"
    )

@bot.command(name="영이")
async def cmd_youngi(ctx: commands.Context):
    msgs = [
        "안냥! 영이 왔어 🐾",
        "오늘도 반짝반짝 ✨ 파이팅!",
        "부르면 달려오는 영이봇 2.0!",
        "간식... 아니 명령어 주세요 😆",
        "영이는 모두를 응원해요 💪",
        "라오킹 출첵 잊지 마~!"
    ]
    await ctx.send(random.choice(msgs))

@bot.command(name="청소")
@commands.has_permissions(manage_messages=True)
async def cmd_clean(ctx: commands.Context):
    deleted = await ctx.channel.purge(limit=5)
    await ctx.send(f"{len(deleted)}개의 메시지를 삭제했어요.", delete_after=3)

# -------- Tasks --------
@tasks.loop(minutes=1)
async def every_morning():
    now = datetime.now(SEOUL)
    if now.hour == 9 and now.minute == 0:
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            await ch.send("좋은아침이에요! 다들 라오킹접속해서 일일보상 챙겨!")

@tasks.loop(minutes=1)
async def sunday_11pm():
    now = datetime.now(SEOUL)
    if now.weekday() == 6 and now.hour == 23 and now.minute == 0:
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            await ch.send("다들 주말동안 잘 쉬었어? 내일은 일하러 가야하니까 다들 일찍 자 고생해!!")

# -------- Keep Alive & Run --------
keep_alive()
bot.run(DISCORD_BOT_TOKEN)
