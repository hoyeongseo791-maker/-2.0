# Create deploy-ready files for Render: main.py, keep_alive.py, requirements.txt, runtime.txt, .env example
from textwrap import dedent

main_py = r'''# main.py — YOUNGI Bot 2.0 (KR/EN/CN/VI security split) for Render + GitHub
# --------------------------------------------------------------------
# Features (updated per request)
# - Welcome flow: on member join -> country buttons first (Korean/English/China/Vietnam)
# - Country picker buttons also shown by commands (!국가 / !Country / !国家 / !QuốcGia ...)
# - Language roles: Korean, English, China(中文), Vietnam(Tiếng Việt)
# - Per-language security:
#     KR  : 📥보안채널📥 -> !보안 -> password(0920) -> role "보안인증서"
#     EN  : Security Channel -> !Security -> password(0920) -> role "Security Certificate" -> tag in secondary-security-channel (manual step)
#     CN  : 安全通道 -> !安全 -> password(0920) -> role "安全证书" -> tag in 二级安全通道 (manual step)
#     VI  : kênh an ninh -> !BaoMat / !BảoMật -> password(0920) -> role "Giấy chứng nhận bảo mật" -> tag in Kênh an ninh thứ cấp (manual step)
# - Meeting/Report/Cleanup, daily 09:00 & Sun 23:00 (Asia/Seoul)
# - All commands have multi-language aliases (KR/EN/CN/VI)
# - Render tips: Start Command -> `python3 main.py`
# --------------------------------------------------------------------

import os, random
from datetime import datetime
import pytz
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button

# -------- keep_alive (optional tiny web server) --------
try:
    from keep_alive import keep_alive
except Exception:
    def keep_alive():
        pass

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
WELCOME_CHANNEL_ID                 = _get_id("WELCOME_CHANNEL_ID")
CHAT_CHANNEL_ID                    = _get_id("CHAT_CHANNEL_ID")
ROLE_REQUEST_CHANNEL_ID            = _get_id("ROLE_REQUEST_CHANNEL_ID")

SECURITY_CHANNEL_KR_ID             = _get_id("SECURITY_CHANNEL_KR_ID")              # 📥보안채널📥
SECURITY_CHANNEL_EN_ID             = _get_id("SECURITY_CHANNEL_EN_ID")              # Security Channel
SECURITY_CHANNEL_CN_ID             = _get_id("SECURITY_CHANNEL_CN_ID")              # 安全通道
SECURITY_CHANNEL_VI_ID             = _get_id("SECURITY_CHANNEL_VI_ID")              # kênh an ninh

SECONDARY_SECURITY_CHANNEL_EN_ID   = _get_id("SECONDARY_SECURITY_CHANNEL_EN_ID")    # secondary-security-channel
SECONDARY_SECURITY_CHANNEL_CN_ID   = _get_id("SECONDARY_SECURITY_CHANNEL_CN_ID")    # 二级安全通道
SECONDARY_SECURITY_CHANNEL_VI_ID   = _get_id("SECONDARY_SECURITY_CHANNEL_VI_ID")    # Kênh an ninh thứ cấp

SERVER_ADMIN_CHANNEL_ID            = _get_id("SERVER_ADMIN_CHANNEL_ID")             # ⚠서버-관리실⚠

# ----- Role IDs -----
ROLE_LANG_KR_ID         = _get_id("ROLE_LANG_KR_ID")                 # Korean
ROLE_LANG_EN_ID         = _get_id("ROLE_LANG_EN_ID")                 # English
ROLE_LANG_CN_ID         = _get_id("ROLE_LANG_CN_ID")                 # China(中文)
ROLE_LANG_VI_ID         = _get_id("ROLE_LANG_VI_ID")                 # Vietnam(Tiếng Việt)

ROLE_SECURITY_CERT_KR   = _get_id("ROLE_SECURITY_CERT_KR")           # 보안인증서
ROLE_SECURITY_CERT_EN   = _get_id("ROLE_SECURITY_CERT_EN")           # Security Certificate
ROLE_SECURITY_CERT_CN   = _get_id("ROLE_SECURITY_CERT_CN")           # 安全证书
ROLE_SECURITY_CERT_VI   = _get_id("ROLE_SECURITY_CERT_VI")           # Giấy chứng nhận bảo mật

ROLE_R4_ID              = _get_id("ROLE_R4_ID")
ROLE_ADMIN_ID           = _get_id("ROLE_ADMIN_ID")
ROLE_R3_1_ID            = _get_id("ROLE_R3_1_ID")

# ----- Misc -----
SECURITY_PASSWORD = os.getenv("SECURITY_PASSWORD", "0920").strip()
SEOUL = pytz.timezone("Asia/Seoul")
loops_started = False
ready_once = False

# ---------------- Intents & Bot ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

# ---------------- Views (buttons) ----------------
class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Role picker (server-specific roles)
        self.add_item(Button(label="R4",     style=discord.ButtonStyle.primary, custom_id="role_r4"))
        self.add_item(Button(label="관리자",  style=discord.ButtonStyle.danger,  custom_id="role_admin"))
        self.add_item(Button(label="R3~1",   style=discord.ButtonStyle.success, custom_id="role_r3_1"))

class CountryView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # 4 choices as requested
        self.add_item(Button(label="Korean",  style=discord.ButtonStyle.primary, custom_id="country_kr"))
        self.add_item(Button(label="English", style=discord.ButtonStyle.primary, custom_id="country_en"))
        self.add_item(Button(label="China",   style=discord.ButtonStyle.primary, custom_id="country_cn"))
        self.add_item(Button(label="Vietnam", style=discord.ButtonStyle.primary, custom_id="country_vi"))

# ---------------- Events ----------------
@bot.event
async def on_ready():
    global loops_started, ready_once
    if ready_once:
        return
    ready_once = True

    print(f"✅ Logged in as {bot.user} ({bot.user.id}) | YOUNGI v2.0 (KR/EN/CN/VI)")

    # Persistent views
    bot.add_view(RoleView())
    bot.add_view(CountryView())

    ch = bot.get_channel(CHAT_CHANNEL_ID)
    if ch:
        try:
            await ch.send("영이봇 v2.0 온라인! (KR/EN/CN/VI)")
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
    try:
        # Show country buttons first
        await ch.send(f"{member.mention}\n국가/언어를 먼저 선택해주세요.\nPlease choose your language first.\n请先选择语言。\nVui lòng chọn ngôn ngữ trước.", view=CountryView())
    except Exception as e:
        print(f"[WARN] Failed to send country picker on join: {e}")

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

        # ---- Roles ----
        if cid == "role_r3_1" and ROLE_R3_1_ID:
            role = guild.get_role(ROLE_R3_1_ID)
            if role:
                await member.add_roles(role)
                await inter.followup.send("R3~1 역할을 부여했어요! / Granted R3~1 role.", ephemeral=True)
                return

        if cid == "role_r4":
            req = bot.get_channel(ROLE_REQUEST_CHANNEL_ID)
            if req:
                await req.send(f"{member.mention} 님이 **R4 역할**을 신청했습니다. 심사 진행합니다.")
            await inter.followup.send("R4 역할은 역할신청방에 양식대로 올려주세요! / Please apply for R4 in the role-request channel.", ephemeral=True)
            return

        if cid == "role_admin":
            req = bot.get_channel(ROLE_REQUEST_CHANNEL_ID)
            if req:
                await req.send(f"{member.mention} 님이 **관리자 역할**을 신청했습니다. 심사 진행합니다.")
            await inter.followup.send("관리자 역할은 역할신청방에 양식대로 올려주세요! / Please apply for Admin in the role-request channel.", ephemeral=True)
            return

        # ---- Countries (language roles + route to security channel) ----
        async def _add_role_and_route(lang_role_id: int, security_channel_id: int, tag_text: str, cmd_hint: str):
            # Assign language role (add; do not remove others automatically)
            if lang_role_id:
                r = guild.get_role(lang_role_id)
                if r and r not in member.roles:
                    await member.add_roles(r, reason="Selected language")
            # Route user to the proper security channel and tag with hint
            ch = bot.get_channel(security_channel_id) if security_channel_id else None
            if ch:
                await ch.send(f"{member.mention} {tag_text}\n{cmd_hint}")
            await inter.followup.send("언어 역할 부여 및 보안 채널 안내가 완료되었습니다. / Language role set & security channel notified.", ephemeral=True)

        if cid == "country_kr":
            await _add_role_and_route(
                ROLE_LANG_KR_ID,
                SECURITY_CHANNEL_KR_ID,
                "보안 인증을 진행해주세요.",
                "여기서 `!보안` 을 입력하면 됩니다. (비밀번호: 0920)"
            )
            return

        if cid == "country_en":
            await _add_role_and_route(
                ROLE_LANG_EN_ID,
                SECURITY_CHANNEL_EN_ID,
                "Please proceed with security verification.",
                "Type `!Security` here. (Password: 0920)"
            )
            return

        if cid == "country_cn":
            await _add_role_and_route(
                ROLE_LANG_CN_ID,
                SECURITY_CHANNEL_CN_ID,
                "请进行安全验证。",
                "在此处输入 `!安全`。（密码：0920）"
            )
            return

        if cid == "country_vi":
            await _add_role_and_route(
                ROLE_LANG_VI_ID,
                SECURITY_CHANNEL_VI_ID,
                "Vui lòng tiến hành xác minh bảo mật.",
                "Nhập `!BảoMật` tại đây. (Mật khẩu: 0920)"
            )
            return

        await inter.followup.send("처리할 수 없는 버튼입니다. 관리자에게 문의해주세요.", ephemeral=True)

    except Exception as e:
        print(f"[ERROR] on_interaction 실패: {e}")

# ---------------- Commands (multi-language aliases) ----------------

# Country picker
@bot.command(name="국가", aliases=["Country", "国家", "QuocGia", "QuốcGia"])
async def cmd_country(ctx: commands.Context):
    await ctx.send("언어/국가를 선택하세요.\nChoose your language.\n请选择语言。\nHãy chọn ngôn ngữ:", view=CountryView())

# Role picker
@bot.command(name="역할", aliases=["Role", "角色", "VaiTro", "VaiTrò"])
async def cmd_roles(ctx: commands.Context):
    await ctx.send("역할을 선택하세요 / Choose a role:", view=RoleView())

# Help
@bot.command(name="명령어", aliases=["help", "도움말", "帮助", "TroGiup", "TrợGiúp"])
async def cmd_help(ctx: commands.Context):
    await ctx.send(
        "사용 가능한 명령어 / Available / 可用命令 / Lệnh khả dụng:\n"
        "• `!국가` / `!Country` / `!国家` / `!QuốcGia`  — 언어 역할 버튼\n"
        "• `!역할` / `!Role` / `!角色` / `!VaiTrò`       — 서버 역할 버튼\n"
        "• `!보안` (KR) / `!Security` (EN) / `!安全` (CN) / `!BảoMật` (VI)\n"
        "• `!회의` / `!Meeting` / `!会议` / `!CuộcHọp`   — R4 멘션 소집\n"
        "• `!리폿` / `!Report` / `!举报` / `!BáoCáo`     — 신고 접수\n"
        "• `!청소 [n]` / `!Clean [n]` / `!清理 [n]` / `!Dọn [n]` — 메시지 삭제"
    )

# Fun
@bot.command(name="영이", aliases=["YOUNGI", "영이봇", "Youngi"])
async def cmd_youngi(ctx: commands.Context):
    msgs = [
        "안냥! 영이 왔어 🐾", "오늘도 파이팅 ✨", "영이봇 2.0 준비 완료!", "명령어는 `!명령어`",
        "Hello! YOUNGI here 👋", "欢迎～一起玩吧！", "Xin chào! Cùng vui nào!"
    ]
    await ctx.send(random.choice(msgs))

# Cleanup
@bot.command(name="청소", aliases=["Clean", "清理", "Dọn"])
@commands.has_permissions(manage_messages=True)
async def cmd_clean(ctx: commands.Context, amount: int = 5):
    amount = max(1, min(50, amount))
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{max(0, len(deleted)-1)}개의 메시지를 삭제했어요. / Deleted. / 已删除. / Đã xóa.", delete_after=3)

@cmd_clean.error
async def _clean_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("권한이 없어요 (manage_messages). / Missing permission. / 权限不足. / Thiếu quyền.")

# Meeting
@bot.command(name="회의", aliases=["Meeting", "会议", "CuộcHọp"])
async def cmd_meeting(ctx: commands.Context):
    role = ctx.guild.get_role(ROLE_R4_ID) if ROLE_R4_ID else None
    mention = role.mention if role else (f"<@&{ROLE_R4_ID}>" if ROLE_R4_ID else "R4")
    await ctx.send(f"{mention} 회의 참여 부탁드립니다. / Meeting please. / 请参加会议. / Mời tham dự họp.")

# Report
@bot.command(name="리폿", aliases=["Report", "举报", "BáoCáo"])
async def cmd_report(ctx: commands.Context):
    await ctx.reply("신고가 접수되었습니다. / Report received. / 已接收举报. / Đã nhận báo cáo.")
    admin_ch = bot.get_channel(SERVER_ADMIN_CHANNEL_ID)
    if admin_ch:
        await admin_ch.send(f"{ctx.author.mention} 신고/Report/举报/Báo cáo 접수.")

# ---------------- Security Commands ----------------

KR_ONLY_NAMES = ["보안", "보안인증", "보안확인"]
EN_ONLY_NAMES = ["Security"]
CN_ONLY_NAMES = ["安全", "安全验证"]
VI_ONLY_NAMES = ["BaoMat", "BảoMật", "BảoMat", "BaoMật"]

def _pw_prompt(lang: str):
    return {
        "KR": "비밀번호가 뭔가요? (60초 내 입력)",
        "EN": "What is the password? (enter within 60 seconds)",
        "CN": "密码是什么？（请在60秒内输入）",
        "VI": "Mật khẩu là gì? (nhập trong 60 giây)",
    }[lang]

def _pw_wrong(lang: str):
    return {
        "KR": "❌ 비밀번호가 올바르지 않아요. 다시 시도해주세요.",
        "EN": "❌ Wrong password. Please try again.",
        "CN": "❌ 密码错误。请重试。",
        "VI": "❌ Sai mật khẩu. Vui lòng thử lại.",
    }[lang]

def _timeout_err(lang: str):
    return {
        "KR": "시간 초과 또는 오류가 발생했어요. 다시 시도해주세요.",
        "EN": "Timed out or an error occurred. Please try again.",
        "CN": "超时或发生错误。请重试。",
        "VI": "Hết thời gian hoặc có lỗi xảy ra. Vui lòng thử lại.",
    }[lang]

async def _security_flow(ctx: commands.Context, lang: str, need_lang_role_id: int, cert_role_id: int, allowed_channel_id: int, secondary_channel_id: int = 0):
    # Guard: channel & language role (if configured)
    if allowed_channel_id and ctx.channel.id != allowed_channel_id:
        target = bot.get_channel(allowed_channel_id)
        if lang == "KR":
            await ctx.reply(f"이 명령어는 {target.mention if target else '지정된 보안채널'} 에서만 사용 가능합니다.")
        elif lang == "EN":
            await ctx.reply(f"This command can be used only in {target.mention if target else 'the Security Channel'}.")
        elif lang == "CN":
            await ctx.reply(f"此指令仅可在 {target.mention if target else '安全通道'} 使用。")
        else:
            await ctx.reply(f"Lệnh này chỉ sử dụng tại {target.mention if target else 'kênh an ninh'}.")
        return

    if need_lang_role_id:
        need_role = ctx.guild.get_role(need_lang_role_id)
        if need_role and need_role not in ctx.author.roles:
            if lang == "KR":
                await ctx.reply("Korean 역할이 있어야 인증할 수 있어요. 먼저 `!국가`로 Korean을 선택하세요.")
            elif lang == "EN":
                await ctx.reply("You must have the English role. Run `!Country` and choose English first.")
            elif lang == "CN":
                await ctx.reply("需要拥有中文角色。请先运行 `!国家` 选择 China。")
            else:
                await ctx.reply("Bạn cần có vai trò Tiếng Việt. Vào `!QuốcGia` chọn Vietnam trước.")
            return

    await ctx.send(_pw_prompt(lang))

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
            role = ctx.guild.get_role(cert_role_id) if cert_role_id else None
            if not role:
                await ctx.send("❌ 인증서 역할 ID가 설정되지 않았어요. 관리자에게 문의해주세요.")
                return
            try:
                await ctx.author.add_roles(role, reason=f"Security password verification ({lang})")
                if lang == "KR":
                    await ctx.send(f"✅ 인증 성공! {ctx.author.mention} 님께 {role.mention} 역할을 부여했어요.")
                elif lang == "EN":
                    await ctx.send(f"✅ Success! {ctx.author.mention} has been granted {role.mention}.")
                elif lang == "CN":
                    await ctx.send(f"✅ 成功！已为 {ctx.author.mention} 赋予 {role.mention}。")
                else:
                    await ctx.send(f"✅ Thành công! {ctx.author.mention} đã được cấp {role.mention}.")
            except discord.Forbidden:
                await ctx.send("권한이 부족해 역할을 부여하지 못했습니다. (manage_roles 필요)")
                return

            # Post to secondary channel (EN/CN/VI only as requested)
            if lang in ("EN", "CN", "VI") and secondary_channel_id:
                sec2 = bot.get_channel(secondary_channel_id)
                if sec2:
                    try:
                        msg_text = {
                            "EN": "Hello, this is the final verification. Please attach a screenshot where your in-game ID is visible.",
                            "CN": "您好，最后一步验证，请附上能看见您游戏ID的截图。",
                            "VI": "Xin chào, đây là bước xác minh cuối. Vui lòng đính kèm ảnh chụp cho thấy ID trong game của bạn."
                        }[lang]
                        await sec2.send(f"{ctx.author.mention}\n{msg_text}")
                    except Exception as e:
                        print(f"[WARN] Secondary notice failed ({lang}): {e}")
        else:
            await ctx.send(_pw_wrong(lang))

    except Exception as e:
        await ctx.send(_timeout_err(lang))
        print(f"[WARN] Security flow failed ({lang}): {e}")

# --- KR Security ---
@bot.command(name="보안", aliases=["보안인증", "보안확인"])
async def cmd_security_kr(ctx: commands.Context):
    await _security_flow(ctx, "KR", ROLE_LANG_KR_ID, ROLE_SECURITY_CERT_KR, SECURITY_CHANNEL_KR_ID, 0)

# --- EN Security ---
@bot.command(name="Security", aliases=[])
async def cmd_security_en(ctx: commands.Context):
    await _security_flow(ctx, "EN", ROLE_LANG_EN_ID, ROLE_SECURITY_CERT_EN, SECURITY_CHANNEL_EN_ID, SECONDARY_SECURITY_CHANNEL_EN_ID)

# --- CN Security ---
@bot.command(name="安全", aliases=["安全验证"])
async def cmd_security_cn(ctx: commands.Context):
    await _security_flow(ctx, "CN", ROLE_LANG_CN_ID, ROLE_SECURITY_CERT_CN, SECURITY_CHANNEL_CN_ID, SECONDARY_SECURITY_CHANNEL_CN_ID)

# --- VI Security ---
@bot.command(name="BảoMật", aliases=["BaoMat", "BảoMat", "BaoMật"])
async def cmd_security_vi(ctx: commands.Context):
    await _security_flow(ctx, "VI", ROLE_LANG_VI_ID, ROLE_SECURITY_CERT_VI, SECURITY_CHANNEL_VI_ID, SECONDARY_SECURITY_CHANNEL_VI_ID)

# ---------------- Schedulers ----------------
@tasks.loop(minutes=1)
async def every_morning():
    now = datetime.now(SEOUL)
    if now.hour == 9 and now.minute == 0:
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            try:
                await ch.send("좋은아침! 라오킹 접속해서 일일보상 챙기세요! / Good morning! / 早上好！/ Chào buổi sáng!")
            except Exception as e:
                print(f"[WARN] every_morning send failed: {e}")

@tasks.loop(minutes=1)
async def sunday_11pm():
    now = datetime.now(SEOUL)
    if now.weekday() == 6 and now.hour == 23 and now.minute == 0:
        ch = bot.get_channel(CHAT_CHANNEL_ID)
        if ch:
            try:
                await ch.send("주간 공지: 내일 출근/등교 준비! / Weekly notice. / 每周提醒。/ Thông báo hàng tuần.")
            except Exception as e:
                print(f"[WARN] sunday_11pm send failed: {e}")

# ---------------- Run ----------------
if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        raise SystemExit("Env DISCORD_BOT_TOKEN is empty. Set it in Render.")
    keep_alive()
    bot.run(DISCORD_BOT_TOKEN)
'''

keep_alive_py = dedent('''\
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.get("/")
def home():
    return "ok"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run, daemon=True)
    t.start()
''')

requirements = dedent('''\
discord.py>=2.3.2
pytz>=2024.1
Flask>=3.0.0
# If using Python 3.13 on Render, uncomment the next line:
# audioop-lts>=0.2.1
''')

runtime = 'python-3.12.4\n'

env_template = dedent('''\
# ---- REQUIRED ----
DISCORD_BOT_TOKEN=

# ---- CHANNELS ----
WELCOME_CHANNEL_ID=
CHAT_CHANNEL_ID=
ROLE_REQUEST_CHANNEL_ID=

SECURITY_CHANNEL_KR_ID=
SECURITY_CHANNEL_EN_ID=
SECURITY_CHANNEL_CN_ID=
SECURITY_CHANNEL_VI_ID=

SECONDARY_SECURITY_CHANNEL_EN_ID=
SECONDARY_SECURITY_CHANNEL_CN_ID=
SECONDARY_SECURITY_CHANNEL_VI_ID=

SERVER_ADMIN_CHANNEL_ID=

# ---- ROLES ----
ROLE_LANG_KR_ID=
ROLE_LANG_EN_ID=
ROLE_LANG_CN_ID=
ROLE_LANG_VI_ID=

ROLE_SECURITY_CERT_KR=
ROLE_SECURITY_CERT_EN=
ROLE_SECURITY_CERT_CN=
ROLE_SECURITY_CERT_VI=

ROLE_R4_ID=
ROLE_ADMIN_ID=
ROLE_R3_1_ID=

# ---- SECURITY ----
SECURITY_PASSWORD=0920
''')

paths = {
    "/mnt/data/main.py": main_py,
    "/mnt/data/keep_alive.py": keep_alive_py,
    "/mnt/data/requirements.txt": requirements,
    "/mnt/data/runtime.txt": runtime,
    "/mnt/data/.env.youngi.example": env_template,
}

for p, content in paths.items():
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

list(paths.keys())
