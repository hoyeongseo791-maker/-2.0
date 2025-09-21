# Discord Bot (Render + GitHub 배포)

## 🚀 실행 방법

1. GitHub에 이 코드 업로드
2. Render에서 새 Web Service 생성
3. Environment Variables 등록
   - DISCORD_BOT_TOKEN = (디스코드 봇 토큰)
   - OWNER_ID = (본인 디스코드 ID)
   - GUILD_ID, WELCOME_CHANNEL_ID, CHAT_CHANNEL_ID 등 서버 ID와 채널 ID 입력
4. Start Command:
   ```bash
   python3 main.py
   ```

## 📌 주요 기능
- 역할 버튼 (!역할 / !class)
- 국가 선택 버튼 (!국가 / !country)
- 랜덤 메시지 (!영이)
- 청소 기능 (!청소)
- 간단한 통계 (!통계)
- 신규 유저 환영 메시지
- 주말/일요일 정기 메시지
