# 영이봇 2.1 - Render + GitHub + keep_alive
# 변경 요약
# - 환영문 안내 유지
# - !보안 프리픽스 명령 + /보안 슬래시 명령(Modal) 동시 지원
# - on_ready에서 slash sync
# - 기타 기존 기능 그대로 유지
#
# 필요 라이브러리: discord.py>=2.3, Flask, pytz (slash Modal 사용)
# Python 3.13 사용 시 requirements에 audioop-lts 권장 또는 runtime.txt로 3.12 고정

import os
import random
from datetime import datetime

import pytz
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button

from keep_alive import keep_alive

# ---------------- Intents & Bot ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Helpers ----------------
def _get_token(key: str) -> str:
    v = os.getenv(key, "").strip()
    if not v:
        print(f"[WARN] 환경변수 {key} 가 비어있습니다.")
    return v

def _get_id(key: str) -> int:
    v = os.getenv(key, "").strip()
    try:
        return int(v)
    except Exception:
        if v:
            print(f"[WARN] 환경변수 {key} 값이 정수가 아닙니다: {v}")
        return 0

# 필수 토큰
DISCORD_BOT_TOKEN = _get_token("DISCORD_BOT_TOKEN")

# ----- 채널 ID -----
WELCOME_CHANNEL_ID       = _get_id("WELCOME_CHANNEL_ID")        # 환영 채널
CHAT_CHANNEL_ID          = _get_id("CHAT_CHANNEL_ID")           # 수다방 채널
ROLE_REQUEST_CHANNEL_ID  = _get_id("ROLE_REQUEST_CHANNEL_ID")   # 역할신청방 채널
SECURITY_CHANNEL_ID      = _get_id("SECURITY_CHANNEL_ID")       # 📥보안채널📥
SERVER_ADMIN_CHANNEL_ID  = _get_id("SERVER_ADMIN_CHANNEL_ID")   # ⚠서버-관리실⚠

# ----- 역할 ID -----
ROLE_R4_ID              = _get_id("ROLE_R4_ID")                 # R4
ROLE_ADMIN_ID           = _get_id("ROLE_ADMIN_ID")              # 관리자(Manager)
ROLE_R3_1_ID            = _get_id("ROLE_R3_1_ID")               # R3~1
ROLE_KR_ID              = _get_id("ROLE_KOREAN_ID")             # Korean
ROLE_EN_ID              = _get_id("ROLE_ENGLISH_ID")            # English
ROLE_SECURITY_CERT_ID   = _get_id("ROLE_SECURITY_CERT_ID")      # 보안인증서

# ----- 기타 -----
SECURITY_PASSWORD = os.getenv("SECURITY_PASSWORD", "0920").strip()
SEOUL = pytz.timezone("Asia/Seoul")
loops_started = False

# ---------------- Views ----------------
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

# ---------------- Events ----------------
@bot.event
async def on_ready():
    global loops_started
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    bot.add_view(RoleView())
    bot.add_view(CountryView())

    # 슬래시 커맨드 동기화
    try:
        synced = await bot.tree.sync()
        print(f"[INFO] Slash commands synced: {[c.name for c in synced]}")
    except Exception as e:
        print(f"[WARN] Slash sync failed: {e}")

    ch = bot.get_channel(CHAT_CHANNEL_ID)
    if ch:
        await ch.send("영이봇2.1 준비완료!")

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
        return
    text = (
        "환영합니다!! 간단하게 서버소개 도와드릴게요!\n"
        "1. 서버에 역할이 존재합니다. /!역할/ /!국가/를 채팅에 입력하시면 선택지가 생성됩니다. 선택후에 채널입장권한이 부여됩니다 \n"
        "2. 보안을위해 카카오톡에서 전달받은 비밀번호를 보안채널에 /!보안/을 입력후 영이봇의 안내에따라 비밀번호를 눌러주세요\n"
        "3. 상호간에 즐거운 게임환경을 위해 규칙채널에서 규칙확인후 이용바랍니다. \n"
        "4. 추가적인 서버증설혹은 오류있을시 서버관리자에게 문의 부탁드립니다."
    )
    await ch.send(f"{member.mention}\n{text}")

# ---------------- Interaction (Buttons) ----------------
@bot.event
async def on_interaction(inter: discord.Interaction):
    data = inter.data or {}
    cid = data.get("custom_id")
    if not cid:
        return

    guild = inter.guild
    if guild is None:
        return
    member = inter.user if isinstance(inter.user, discord.Member) else guild.get_member(inter.user.id)

    try:
        # 3초 제한 회피: 먼저 응답 예약
        await inter.response.defer(ephemeral=True)

        # 역할 버튼들
        if cid == "role_r3_1" and ROLE_R3_1_ID:
            role = guild.get_role(ROLE_R3_1_ID)
            if role:
                await member.add_roles(role)
                await inter.followup.send("R3~1 역할을 부여했어요!", ephemeral=True)
                return

        if cid == "role_r4":
            req = bot.get_channel(ROLE_REQUEST_CHANNEL_ID)
            if req:
                await req.send(f"{member.mention} 님이 **R4 역할**을 신청했습니다. 양식 확인 후 심사 진행합니다.")
            await inter.followup.send("R4 역할은 **역할신청방**에 양식대로 올려주세요! 심사 후 권한이 변경됩니다.", ephemeral=True)
            return

        if cid == "role_admin":
            req = bot.get_channel(ROLE_REQUEST_CHANNEL_ID)
            if req:
                await req.send(f"{member.mention} 님이 **관리자 역할**을 신청했습니다. 양식 확인 후 심사 진행합니다.")
            await inter.followup.send("관리자 역할은 **역할신청방**에 양식대로 올려주세요! 심사 후 권한이 변경됩니다.", ephemeral=True)
            return

        # 국가 버튼들
        if cid == "country_kr" and ROLE_KR_ID:
            role = guild.get_role(ROLE_KR_ID)
            if role:
                await member.add_roles(role)
                await inter.followup.send("Korean 역할을 부여했어요!", ephemeral=True)
                return

        if cid == "country_en" and ROLE_EN_ID:
            role = guild.get_role(ROLE_EN_ID)
            if role:
                await member.add_roles(role)
                await inter.followup.send("English 역할을 부여했어요!", ephemeral=True)
                return

        await inter.followup.send("처리할 수 없는 버튼입니다. 관리자에게 문의해주세요.", ephemeral=True)

    except Exception as e:
        print(f"[ERROR] on_interaction 실패: {e}")

# ---------------- Modal for Slash Security ----------------
class SecurityPasswordModal(discord.ui.Modal, title="보안 인증"):
    pwd = discord.ui.TextInput(label="비밀번호", placeholder="예: 0920", required=True, min_length=1, max_length=32)

    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    async def on_submit(self, interaction: discord.Interaction):
        if SECURITY_CHANNEL_ID and interaction.channel_id != SECURITY_CHANNEL_ID:
            await interaction.response.send_message("이 명령어는 지정된 보안채널에서만 사용할 수 있어요.", ephemeral=True)
            return
        pw = str(self.pwd.value).strip()
        if pw == SECURITY_PASSWORD:
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("길드 컨텍스트를 찾지 못했어요.", ephemeral=True)
                return
            role = guild.get_role(ROLE_SECURITY_CERT_ID)
            if not role:
                await interaction.response.send_message("서버에서 '보안인증서' 역할을 찾지 못했어요.", ephemeral=True)
                return
            try:
                await self.member.add_roles(role, reason="보안 비밀번호 인증 (slash)")
                await interaction.response.send_message(f"✅ 인증 성공! {self.member.mention} 님께 {role.mention} 역할을 부여했어요.", ephemeral=True)
            except discord.Forbidden:
                await interaction.response.send_message("권한이 부족해서 역할을 부여하지 못했어요. (manage_roles 필요)", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 비밀번호가 올바르지 않아요. 다시 시도해주세요.", ephemeral=True)

# ---------------- Slash Commands ----------------
@bot.tree.command(name="보안", description="보안 비밀번호를 입력해 인증합니다.")
async def slash_security(interaction: discord.Interaction):
    modal = SecurityPasswordModal(member=interaction.user)
    await interaction.response.send_modal(modal)

# ---------------- Commands ----------------
@bot.command(name="역할")
async def cmd_roles(ctx: commands.Context):
    await ctx.send("원하시는 역할을 선택해주세요:", view=RoleView())

@bot.command(name="국가")
async def cmd_country(ctx: commands.Context):
    await ctx.send("국가를 선택해주세요:", view=CountryView())

@bot.command(name="명령어")
async def cmd_help(ctx: commands.Context):
    await ctx.send(
        "사용 가능한 명령어:\n"
        "• `!역할`  역할 선택 버튼 표시\n"
        "• `!국가`  언어 역할 버튼 표시\n"
        "• `!보안`  (또는 `/보안`) 📥보안채널📥에서 비밀번호 인증 후 역할 부여\n"
        "• `!회의`  R4 역할 멘션으로 회의 소집\n"
        "• `!리폿`  신고 접수 및 ⚠서버-관리실⚠ 채널에 알림\n"
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

# ----- 추가 기능: 보안 인증 (접두사) -----
@bot.command(name="보안", aliases=["security","sec"])
async def cmd_security(ctx: commands.Context):
    if SECURITY_CHANNEL_ID and ctx.channel.id != SECURITY_CHANNEL_ID:
        target = bot.get_channel(SECURITY_CHANNEL_ID)
        if target:
            await ctx.reply(f"이 명령어는 {target.mention} 에서만 사용할 수 있어요.")
        else:
            await ctx.reply("이 명령어는 지정된 보안채널에서만 사용할 수 있어요.")
        return

    await ctx.send("비밀번호가 뭔가요? (60초 내 입력)")

    def check(m: discord.Message):
        return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

    try:
        msg: discord.Message = await bot.wait_for("message", timeout=60.0, check=check)
        pw = msg.content.strip()
        try:
            await msg.delete()
        except Exception:
            pass

        if pw == SECURITY_PASSWORD:
            role = ctx.guild.get_role(ROLE_SECURITY_CERT_ID)
            if not role:
                await ctx.send("서버에서 '보안인증서' 역할을 찾을 수 없어요. 관리자에게 문의해주세요.")
                return
            try:
                await ctx.author.add_roles(role, reason="보안 비밀번호 인증")
                await ctx.send(f"✅ 인증 성공! {ctx.author.mention} 님께 {role.mention} 역할을 부여했어요.")
            except discord.Forbidden:
                await ctx.send("권한이 부족해서 역할을 부여하지 못했어요. (manage_roles 필요)")
        else:
            await ctx.send("❌ 비밀번호가 올바르지 않아요. 다시 시도해주세요.")

    except Exception as e:
        await ctx.send("시간 초과 또는 오류가 발생했어요. 다시 `!보안`을 입력해주세요.")
        print(f"[WARN] 보안 비번 처리 실패: {e}")

# ----- 추가 기능: 회의 소집 -----
@bot.command(name="회의")
async def cmd_meeting(ctx: commands.Context):
    if ROLE_R4_ID:
        role = ctx.guild.get_role(ROLE_R4_ID)
        mention_txt = role.mention if role else f"<@&{ROLE_R4_ID}>"
    else:
        mention_txt = "R4"
    await ctx.send(f"{mention_txt} 회의 참여부탁드립니다~")

# ----- 추가 기능: 신고 접수 -----
@bot.command(name="리폿")
async def cmd_report(ctx: commands.Context):
    await ctx.reply("신고가접수되었습니다.")
    admin_ch = bot.get_channel(SERVER_ADMIN_CHANNEL_ID) if SERVER_ADMIN_CHANNEL_ID else None
    if admin_ch:
        try:
            await admin_ch.send(f"{ctx.author.mention} 님의 신고가 접수되었습니다.")
        except Exception as e:
            print(f"[WARN] 관리자 채널 알림 실패: {e}")
    else:
        print("[WARN] SERVER_ADMIN_CHANNEL_ID 채널을 찾지 못했습니다.")

# ---------------- Schedulers ----------------
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
        if ch:\n            try:\n                await ch.send(\"다들 주말동안 잘 쉬었어? 내일은 일하러 가야하니까 다들 일찍 자 고생해!!\")\n            except Exception as e:\n                print(f\"[WARN] sunday_11pm 전송 실패: {e}\")\n\n# ---------------- Keep Alive & Run ----------------\nkeep_alive()\nbot.run(DISCORD_BOT_TOKEN)\n