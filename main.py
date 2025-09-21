# 영이봇 2.0 - 메인 파일 (수정판)
# - R4/관리자 버튼: 역할신청방 안내만 전송 (역할 부여 안 함)
# - 역할 ID/채널 ID 미설정 시 안전 가드 추가
# - Interaction에서 member/guild None 가드

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
WELCOME_CHANNEL_ID       = get_id("WELCOME_CHANNEL_ID")     # 🖐️환영합니다🖐️
CHAT_CHANNEL_ID          = get_id("CHAT_CHANNEL_ID")        # 🔊수다방🔊
ROLE_REQUEST_CHANNEL_ID  = get_id("ROLE_REQUEST_CHANNEL_ID")# 역할신청방

# 역할 ID
ROLE_R4_ID     = get_id("ROLE_R4_ID")        # R4
ROLE_ADMIN_ID  = get_id("ROLE_ADMIN_ID")     # 관리자
ROLE_R3_1_ID   = get_id("ROLE_R3_1_ID")      # R3~1
ROLE_KR_ID     = get_id("ROLE_KOREAN_ID")    # Korean
ROLE_EN_ID     = get_id("ROLE_ENGLISH_ID")   # English

# 루프 중복 방지 플래그
loops_started = False

SEOUL = pytz.timezone("Asia/Seoul")

# -------- Views --------
class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="R4",     style=discord.ButtonStyle.primary, custom_id="role_r4"))
        self.add_item(Button(label="관리자",  style=discord.ButtonStyle.danger,  custom_id="role_admin"))
        self.add_item(Button(label="R3~1",   style=discord.ButtonStyle.success, custom_id="role_r3_1"))

class CountryView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Korean",  style=discord.ButtonStyle.primary, custom_id="country_kr"))
        self.add_item(Button(label="English", style=discord.ButtonStyle.success, custom_id="country_en"))

# -------- Bot Events --------
@bot.event
async def on_ready():
    global loops_started
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

    # Persistent View 등록
    try:
        bot.add_view(RoleView())
        bot.add_view(CountryView())
    except Exception as e:
        print(f"[WARN] add_view 실패: {e}")

    # 부팅 알림
    chat = bot.get_channel(CHAT_CHANNEL_ID)
    if chat:
        try:
            await chat.send("영이봇2.0준비완료!")
        except Exception as e:
            print(f"[WARN] 부팅 메시지 실패: {e}")
    else:
        print("[WARN] CHAT_CHANNEL_ID 채널을 찾지 못했습니다.")

    # 루프(스케줄러) 중복 방지
    if not loops_started:
        if not every_morning.is_running():
            every_morning.start()
        if not sunday_11pm.is_running():
            sunday_11pm.start()
        loops_started = True

@bot.event
async def on_member_join(member: discord.Member):
    ch = bot.get_channel(WELCOME_CHANNEL_ID)
    if not ch:
        print("[WARN] WELCOME_CHANNEL_ID 채널을 찾지 못했습니다.")
        return

    text = (
        "환영합니다!! 간단하게 서버소개 도와드릴게요!\n"
        "1. 서버에 역할이 존재합니다. /!역할/ /!국가/를 채팅에 입력하시면 선택지가 생성됩니다. "
        "선택후에 채널입장권한이 부여됩니다\n"
        "2. 상호간에 즐거운 게임환경을 위해 규칙채널에서 규칙확인후 이용바랍니다.\n"
        "3. 추가적인 서버증설혹은 오류있을시 서버관리자에게 문의 부탁드립니다."
    )
    try:
        await ch.send(f"{member.mention}\n{text}")
    except Exception as e:
        print(f"[WARN] 환영 메시지 실패: {e}")

# -------- Helpers --------
async def safe_add_role(member: discord.Member, role: discord.Role, inter: discord.Interaction, ok_msg: str):
    """역할이 None이거나 권한 부족 시 에러를 삼키고 안내"""
    if role is None:
        return await inter.response.send_message("서버에 해당 역할이 아직 설정되지 않았어요. (관리자에게 문의)", ephemeral=True)
    try:
        if not inter.response.is_done():
            await inter.response.defer(ephemeral=True, thinking=False)
        await member.add_roles(role, reason="Bot role assignment")
        await inter.followup.send(ok_msg, ephemeral=True)
    except discord.Forbidden:
        await inter.followup.send("역할을 부여할 권한이 없어요. (봇 권한 확인)", ephemeral=True)
    except Exception as e:
        await inter.followup.send(f"잠시 오류가 발생했어요. ({e.__class__.__name__})", ephemeral=True)

# -------- Interaction --------
@bot.event
async def on_interaction(inter: discord.Interaction):
    data = inter.data or {}
    cid = data.get("custom_id")
    if not cid:
        return

    if not inter.guild:
        return await inter.response.send_message("DM에서는 사용할 수 없어요.", ephemeral=True)

    # member 보장
    member = inter.user
    if not isinstance(member, discord.Member):
        try:
            member = await inter.guild.fetch_member(inter.user.id)
        except Exception:
            return await inter.response.send_message("멤버 정보를 불러오지 못했어요.", ephemeral=True)

    guild = inter.guild

    # --- 역할 버튼 ---
    if cid == "role_r4":
        ch = bot.get_channel(ROLE_REQUEST_CHANNEL_ID) if ROLE_REQUEST_CHANNEL_ID else None
        if ch:
            try:
                await ch.send(f"{member.mention} 님, **R4 역할** 신청 안내 📥\n"
                              f"역할신청방의 양식에 맞춰 작성해 주세요. 심사 후 권한이 부여됩니다.")
            except Exception as e:
                print(f"[WARN] R4 신청 안내 전송 실패: {e}")
        # 사용자에겐 에페메럴 확인
        return await inter.response.send_message("R4 신청 안내를 역할신청방에 전송했습니다!", ephemeral=True)

    if cid == "role_admin":
        ch = bot.get_channel(ROLE_REQUEST_CHANNEL_ID) if ROLE_REQUEST_CHANNEL_ID else None
        if ch:
            try:
                await ch.send(f"{member.mention} 님, **관리자 역할** 신청 안내 📥\n"
                              f"역할신청방의 양식에 맞춰 작성해 주세요. 심사 후 권한이 변경됩니다.")
            except Exception as e:
                print(f"[WARN] 관리자 신청 안내 전송 실패: {e}")
        return await inter.response.send_message("관리자 신청 안내를 역할신청방에 전송했습니다!", ephemeral=True)

    if cid == "role_r3_1":
        role = guild.get_role(ROLE_R3_1_ID) if ROLE_R3_1_ID else None
        return await safe_add_role(member, role, inter, "R3~1 역할을 부여했어요!")

    # --- 국가 버튼 ---
    if cid == "country_kr":
        role = guild.get_role(ROLE_KR_ID) if ROLE_KR_ID else None
        return await safe_add_role(member, role, inter, "Korean 역할을 부여했어요!")

    if cid == "country_en":
        role = guild.get_role(ROLE_EN_ID) if ROLE_EN_ID else None
        return await safe_add_role(member, role, inter, "English 역할을 부여했어요!")

# -------- Commands --------
@bot.command(name="역할")
async def cmd_roles(ctx: commands.Context):
    await ctx.send("부여할 역할을 선택하세요!", view=RoleView())

@bot.command(name="국가")
async def cmd_country(ctx: commands.Context):
    await ctx.send("언어 역할을 선택하세요!", view=CountryView())

@bot.command(name="명령어")
async def cmd_help(ctx: commands.Context):
    await ctx.send(
        "사용 가능한 명령어:\n"
        "• `!역할`  역할 선택 버튼 표시\n"
        "• `!국가`  언어 역할 버튼 표시\n"
        "• `!청소`  최근 5개 메시지 삭제\n"
        "• `!명령어`  이 도움말 표시\n"
        "• `!영이`  랜덤 귀여운 멘트"
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
    try:
        deleted = await ctx.channel.purge(limit=5)
        await ctx.send(f"{len(deleted)}개의 메시지를 삭제했어요.", delete_after=3)
    except discord.Forbidden:
        await ctx.send("메시지를 지울 권한이 없어요. (manage_messages 권한 필요)")

@cmd_clean.error
async def _clean_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("이 명령어를 사용할 권한이 없어요. (manage_messages)")

# -------- Schedulers --------
@tasks.loop(minutes=1)
async def every_morning():
    now = datetime.now(SEOUL)
    if now.hour == 9 and now.minute == 0:  # 매일 09:00
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            try:
                await ch.send("좋은아침이에요! 다들 라오킹접속해서 일일보상 챙겨!")
            except Exception as e:
                print(f"[WARN] every_morning 전송 실패: {e}")

@tasks.loop(minutes=1)
async def sunday_11pm():
    now = datetime.now(SEOUL)
    if now.weekday() == 6 and now.hour == 23 and now.minute == 0:  # 일 23:00
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            try:
                await ch.send("다들 주말동안 잘 쉬었어? 내일은 일하러 가야하니까 다들 일찍 자 고생해!!")
            except Exception as e:
                print(f"[WARN] sunday_11pm 전송 실패: {e}")

# -------- Keep Alive & Run --------
keep_alive()
bot.run(DISCORD_BOT_TOKEN)
