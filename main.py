# 영이봇 2.0 - Render + GitHub + keep_alive (KR/EN security split)
# 기능:
# - 신규 유저 환영 (한/영 안내 + 명령어 요약)
# - !역할 / !국가 / !Role / !Country 버튼
# - 보안(KR): 📥보안채널📥 에서 !보안 → 비밀번호 확인(0920) 후 "보안인증서" 역할 부여 (Korean 역할 보유자만)
# - 보안(EN): Security Channel 에서 !Security → 비밀번호 확인(0920) 후 "Security Certificate" 역할 부여 (English 역할 보유자만)
#             성공 시 Secondary Security Channel 에 신청 알림 + 2차 인증 양식 안내 (수동 처리)
# - !회의 (R4 멘션), !리폿 (관리실 알림), !청소, !명령어, !영이, 스케줄 안내
# - 루프 중복 방지, 환경변수 체크

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

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

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

DISCORD_BOT_TOKEN = _get_token("DISCORD_BOT_TOKEN")

# ----- 채널 ID -----
WELCOME_CHANNEL_ID              = _get_id("WELCOME_CHANNEL_ID")
CHAT_CHANNEL_ID                 = _get_id("CHAT_CHANNEL_ID")
ROLE_REQUEST_CHANNEL_ID         = _get_id("ROLE_REQUEST_CHANNEL_ID")
SECURITY_CHANNEL_ID             = _get_id("SECURITY_CHANNEL_ID")            # 📥보안채널📥 (KR)
SECURITY_CHANNEL_EN_ID          = _get_id("SECURITY_CHANNEL_EN_ID")         # Security Channel (EN)
SECONDARY_SECURITY_CHANNEL_EN_ID= _get_id("SECONDARY_SECURITY_CHANNEL_EN_ID")# Secondary Security Channel (EN step2)
SERVER_ADMIN_CHANNEL_ID         = _get_id("SERVER_ADMIN_CHANNEL_ID")         # ⚠서버-관리실⚠

# ----- 역할 ID -----
ROLE_R4_ID               = _get_id("ROLE_R4_ID")
ROLE_ADMIN_ID            = _get_id("ROLE_ADMIN_ID")
ROLE_R3_1_ID             = _get_id("ROLE_R3_1_ID")
ROLE_KR_ID               = _get_id("ROLE_KOREAN_ID")         # Korean
ROLE_EN_ID               = _get_id("ROLE_ENGLISH_ID")        # English
ROLE_SECURITY_CERT_ID    = _get_id("ROLE_SECURITY_CERT_ID")   # 보안인증서 (KR)
ROLE_SECURITY_CERT_EN_ID = _get_id("ROLE_SECURITY_CERT_EN_ID")# Security Certificate (EN)

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
    print(f"✅ Logged in as {bot.user} ({bot.user.id}) | v2.0")
    bot.add_view(RoleView())
    bot.add_view(CountryView())

    ch = bot.get_channel(CHAT_CHANNEL_ID)
    if ch:
        await ch.send("영이봇 v2.0 준비완료!")

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

    # 한국어 환영
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
        "8. 규칙 채널에 가서 디스코드 이용에 대한 규칙을 읽어주세요. 감사합니다."
    )

    # 영어 환영 (새 번역)
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

    await ch.send(f"{member.mention}\n{text_kr}")
    await ch.send(text_en)
    await ch.send(cmds)

# ---------------- 이하 나머지 (Interactions, Commands, Security KR/EN, Scheduler 등) ----------------
# (캔버스 최신본 그대로 이어붙이시면 됩니다)
