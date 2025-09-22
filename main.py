# 영이봇 2.0 - Render + GitHub + keep_alive (KR/EN security split)
# ... (기타 부분 동일) ...

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

# ... (나머지 코드 동일) ...
