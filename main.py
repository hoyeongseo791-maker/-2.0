# main.py — YOUNGI Bot 2.0 (KR/EN security split) for Render + GitHub
# --------------------------------------------------------------------
# Features
# - Welcome messages (KR + EN) + command cheat sheet
# - Role pickers: !역할 / !Role (R4, 관리자, R3~1), !국가 / !Country (Korean/English)
# - Security (KR): 📥보안채널📥 -> !보안 -> password(0920) -> "보안인증서" role (Korean role required)
# - Security (EN): Security Channel -> !Security -> password(0920) -> "Security Certificate" role (English role required)
#     Also posts to Secondary Security Channel: application instructions for second-level certificate (manual review)
# - Meeting: !회의 (mentions R4), Report: !리폿 (ack + post to SERVER_ADMIN_CHANNEL)
# - Cleanup: !청소 [n] (default 5, max 50)
# - Daily 09:00 & Sun 23:00 scheduled messages (Asia/Seoul)
# - Environment variable sanity helpers, no voice/audio features (avoids audioop issues)
#
# Render tips:
# - Start Command: python3 main.py
# - If using Python 3.13, add "audioop-lts" to requirements OR pin python-3.12.x in runtime.txt
# --------------------------------------------------------------------

import os
import random
from datetime import datetime

import pytz
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button

# -------- keep_alive (optional small Flask server to keep the dyno alive) --------
try:
    from keep_alive import keep_alive  # your keep_alive.py should start a tiny web server on port 8080
except Exception:
    def keep_alive():
        pass

# ---------------- Intents & Bot ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# ---------------- Helpers ----------------
def _get_token(key: str) -> str:
    v = os.getenv(key, "").strip()
    if not v:
        print(f"[WARN] Env {key} is empty.")
    return v

def _get_id(key: str) -> int:
    v = os.getenv(key, "").strip()
    try:
        return int(v)
    except Exception:
        if v:
            print(f"[WARN] Env {key} should be an integer, got: {v}")
        return 0

DISCORD_BOT_TOKEN = _get_token("DISCORD_BOT_TOKEN")

# ----- Channel IDs -----
WELCOME_CHANNEL_ID               = _get_id("WELCOME_CHANNEL_ID")
CHAT_CHANNEL_ID                  = _get_id("CHAT_CHANNEL_ID")
ROLE_REQUEST_CHANNEL_ID          = _get_id("ROLE_REQUEST_CHANNEL_ID")
SECURITY_CHANNEL_ID              = _get_id("SECURITY_CHANNEL_ID")               # 📥보안채널📥 (KR)
SECURITY_CHANNEL_EN_ID           = _get_id("SECURITY_CHANNEL_EN_ID")            # Security Channel (EN)
SECONDARY_SECURITY_CHANNEL_EN_ID = _get_id("SECONDARY_SECURITY_CHANNEL_EN_ID")  # Secondary Security Channel (EN step2)
SERVER_ADMIN_CHANNEL_ID          = _get_id("SERVER_ADMIN_CHANNEL_ID")           # ⚠서버-관리실⚠

# ----- Role IDs -----
ROLE_R4_ID               = _get_id("ROLE_R4_ID")
ROLE_ADMIN_ID            = _get_id("ROLE_ADMIN_ID")
ROLE_R3_1_ID             = _get_id("ROLE_R3_1_ID")
ROLE_KR_ID               = _get_id("ROLE_KOREAN_ID")          # Korean
ROLE_EN_ID               = _get_id("ROLE_ENGLISH_ID")         # English
ROLE_SECURITY_CERT_ID    = _get_id("ROLE_SECURITY_CERT_ID")   # 보안인증서 (KR)
ROLE_SECURITY_CERT_EN_ID = _get_id("ROLE_SECURITY_CERT_EN_ID")# Security Certificate (EN)

# ----- Misc -----
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
    print(f"✅ Logged in as {bot.user} ({bot.user.id}) | YOUNGI v2.0")
    bot.add_view(RoleView())
    bot.add_view(CountryView())

    ch = bot.get_channel(CHAT_CHANNEL_ID)
    if ch:
        try:
            await ch.send("영이봇 v2.0 준비완료!")
        except Exception as e:
            print(f"[WARN] Failed to send ready message: {e}")

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

    # 한국어 환영 (요청하신 최신 버전)
    text_kr = (
        "[꼭 읽어주세요] 환영합니다!! 간단하게 서버소개 도와드릴게요!\n\n"
        "1. 채널에대한 권한을 받기위해 아래 절차대로 진행해주세요.\n"
        "2. !국가와 !역할을 디스코드 채팅에 입력해주세요\n"
        "3. 본인의 국가와 인게임 티어를 눌러주세요\n"
        "4. 역할이 부여되면 보안인증서를 위해 보안채널이 열립니다. 오른쪽으로 밀면 나와요.\n"
        "5. 보안채널에서 !보안을 입력해주세요.\n"
        "7. 초대받을때 받은 비밀번호를 입력해세요\n"
        "8. 이후 봇의 안내에따라 Secondary Security Channel 채널에서 양식에맞게 신청서를 제출하세요\n"
        "9. 디스코드 이용을 위한 모든 권한이 열립니다.\n"
        "10. 규칙 채널에 가서 디스코드 이용에 대한 규칙을 읽어주세요. 감사합니다."
    )

    # 영어 환영 (요청하신 번역본)
    text_en = (
        "[Please Read] Welcome!! I'll briefly introduce the server!\n\n"
        "1. To gain channel access permissions, please follow the steps below.\n"
        "2. Type `!Country` and `!Role` in the Discord chat.\n"
        "3. Select your country and your in-game tier.\n"
        "4. Once roles are assigned, the Security Channel will open for certificate verification. Swipe right to find it.\n"
        "5. In the Security Channel, enter `!Security`.\n"
        "7. Enter the password you received when invited.\n"
        "8. Then, following the bot’s guidance, submit the application form in the Secondary Security Channel.\n"
        "9. Full Discord permissions will then be unlocked.\n"
        "10. Please read the rules in the rules channel before using the Discord. Thank you."
    )

    # 명령어 요약 (KR+EN)
    cmds = (
        "[명령어/Commands]\n"
        "• `!역할` / `!Role` : 역할 선택 버튼 표시\n"
        "• `!국가` / `!Country` : 언어 역할 버튼 표시 (Korean / English)\n"
        "• `!보안` : 보안채널에서 비밀번호 인증 (Korean only)\n"
        "• `!Security` : Security Channel에서 비밀번호 인증 (English only)\n"
        "• `!회의` : R4 멘션으로 회의 소집\n"
        "• `!리폿` : 신고 접수 (관리실 알림)\n"
        "• `!청소 [n]` : 최근 n개 메시지 삭제 (기본 5)\n"
        "• `!영이` : 랜덤 멘트\n"
    )

    try:
        await ch.send(f"{member.mention}\n{text_kr}")
        await ch.send(text_en)
        await ch.send(cmds)
    except Exception as e:
        print(f"[WARN] Failed to send welcome messages: {e}")

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
        await inter.response.defer(ephemeral=True)

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

# ---------------- Commands ----------------
@bot.command(name="역할")
async def cmd_roles(ctx: commands.Context):
    await ctx.send("원하시는 역할을 선택해주세요:", view=RoleView())

@bot.command(name="Role")
async def cmd_roles_en(ctx: commands.Context):
    await ctx.send("Please choose your role:", view=RoleView())

@bot.command(name="국가")
async def cmd_country(ctx: commands.Context):
    await ctx.send("국가/언어 역할을 선택해주세요:", view=CountryView())

@bot.command(name="Country")
async def cmd_country_en(ctx: commands.Context):
    await ctx.send("Choose your language role:", view=CountryView())

@bot.command(name="명령어")
async def cmd_help(ctx: commands.Context):
    await ctx.send(
        "사용 가능한 명령어 / Available Commands:\n"
        "• `!역할` / `!Role`  역할 선택 버튼 표시\n"
        "• `!국가` / `!Country`  언어 역할 버튼 표시\n"
        "• `!보안` (Korean only, 보안채널)\n"
        "• `!Security` (English only, Security Channel)\n"
        "• `!회의`  R4 멘션 회의 소집\n"
        "• `!리폿`  신고 접수 및 관리실 알림\n"
        "• `!청소 [n]`  최근 n개 메시지 삭제 (기본 5)\n"
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

# ----- Cleanup -----
@bot.command(name="청소")
@commands.has_permissions(manage_messages=True)
async def cmd_clean(ctx: commands.Context, amount: int = 5):
    amount = max(1, min(50, amount))
    deleted = await ctx.channel.purge(limit=amount + 1)  # include command message
    await ctx.send(f"{max(0, len(deleted)-1)}개의 메시지를 삭제했어요.", delete_after=3)

@cmd_clean.error
async def _clean_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("이 명령어를 사용할 권한이 없어요. (manage_messages)")

# ----- Security (KR) -----
@bot.command(name="보안", aliases=["보안인증", "보안확인"])
async def cmd_security_kr(ctx: commands.Context):
    # channel + role guard
    if SECURITY_CHANNEL_ID and ctx.channel.id != SECURITY_CHANNEL_ID:
        target = bot.get_channel(SECURITY_CHANNEL_ID)
        await ctx.reply(f"이 명령어는 {target.mention} 에서만 사용할 수 있어요." if target else "이 명령어는 지정된 보안채널에서만 사용 가능합니다.")
        return
    if ROLE_KR_ID and (ctx.guild.get_role(ROLE_KR_ID) not in ctx.author.roles):
        await ctx.reply("Korean 역할이 있어야 인증할 수 있어요. 먼저 `!국가`에서 Korean을 선택해주세요.")
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
                await ctx.send("❌ '보안인증서' 역할을 찾을 수 없어요. ROLE_SECURITY_CERT_ID 확인 필요.")
                return
            try:
                await ctx.author.add_roles(role, reason="보안 비밀번호 인증(KR)")
                await ctx.send(f"✅ 인증 성공! {ctx.author.mention} 님께 {role.mention} 역할을 부여했어요.")
            except discord.Forbidden:
                await ctx.send("권한이 부족해서 역할을 부여하지 못했어요. (manage_roles 필요)")
        else:
            await ctx.send("❌ 비밀번호가 올바르지 않아요. 다시 시도해주세요.")

    except Exception as e:
        await ctx.send("시간 초과 또는 오류가 발생했어요. 다시 `!보안`을 입력해주세요.")
        print(f"[WARN] 보안(KR) 실패: {e}")

# ----- Security (EN) -----
@bot.command(name="Security")
async def cmd_security_en(ctx: commands.Context):
    # channel + role guard
    if SECURITY_CHANNEL_EN_ID and ctx.channel.id != SECURITY_CHANNEL_EN_ID:
        target = bot.get_channel(SECURITY_CHANNEL_EN_ID)
        await ctx.reply(f"This command can be used only in {target.mention}." if target else "This command can be used only in the Security Channel.")
        return
    if ROLE_EN_ID and (ctx.guild.get_role(ROLE_EN_ID) not in ctx.author.roles):
        await ctx.reply("You must have the English role. Please run `!Country` and choose English first.")
        return

    await ctx.send("What is the password? (enter within 60 seconds)")

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
            role = ctx.guild.get_role(ROLE_SECURITY_CERT_EN_ID)
            if not role:
                await ctx.send("❌ Could not find 'Security Certificate' role. Please set ROLE_SECURITY_CERT_EN_ID.")
                return
            try:
                await ctx.author.add_roles(role, reason="Security password verification (EN)")
                await ctx.send(f"✅ Success! {ctx.author.mention} has been granted {role.mention}.")
            except discord.Forbidden:
                await ctx.send("Insufficient permission to grant roles. (manage_roles required)")
                return

            # Post second-level instructions to Secondary Security Channel (manual)
            sec2 = bot.get_channel(SECONDARY_SECURITY_CHANNEL_EN_ID)
            if sec2:
                try:
                    await sec2.send(f"{ctx.author.mention} has applied for the **Second-level Security Certificate** role.")
                    await sec2.send(
                        "You must have a second-level security certificate to have all channel privileges.\n\n"
                        "**Second-level security certificate issuance form**\n\n"
                        "Game Nickname:\n"
                        "Leader ID:\n"
                        "Recommended by:\n"
                        "Kingdom number, in-game screenshot attached"
                    )
                except Exception as e:
                    print(f"[WARN] Secondary security notice failed: {e}")
        else:
            await ctx.send("❌ Wrong password. Please try again.")

    except Exception as e:
        await ctx.send("Timed out or an error occurred. Please run `!Security` again.")
        print(f"[WARN] Security(EN) failed: {e}")

# ----- Meeting & Report -----
@bot.command(name="회의")
async def cmd_meeting(ctx: commands.Context):
    role = ctx.guild.get_role(ROLE_R4_ID) if ROLE_R4_ID else None
    mention = role.mention if role else (f"<@&{ROLE_R4_ID}>" if ROLE_R4_ID else "R4")
    await ctx.send(f"{mention} 회의 참여부탁드립니다~")

@bot.command(name="리폿")
async def cmd_report(ctx: commands.Context):
    await ctx.reply("신고가접수되었습니다.")
    admin_ch = bot.get_channel(SERVER_ADMIN_CHANNEL_ID)
    if admin_ch:
        await admin_ch.send(f"{ctx.author.mention} 님의 신고가 접수되었습니다.")

# ---------------- Scheduler ----------------
@tasks.loop(minutes=1)
async def every_morning():
    now = datetime.now(SEOUL)
    if now.hour == 9 and now.minute == 0:
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            try:
                await ch.send("좋은아침이에요! 다들 라오킹접속해서 일일보상 챙겨!")
            except Exception as e:
                print(f"[WARN] every_morning send failed: {e}")

@tasks.loop(minutes=1)
async def sunday_11pm():
    now = datetime.now(SEOUL)
    if now.weekday() == 6 and now.hour == 23 and now.minute == 0:
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            try:
                await ch.send("다들 주말동안 잘 쉬었어? 내일은 일하러 가야하니까 다들 일찍 자 고생해!!")
            except Exception as e:
                print(f"[WARN] sunday_11pm send failed: {e}")

# ---------------- Run ----------------
keep_alive()
bot.run(DISCORD_BOT_TOKEN)
