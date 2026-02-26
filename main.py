import requests
import os
import discord
import asyncio

# 깃허브 Secret에서 정보 가져오기
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID')) if os.getenv('CHANNEL_ID') else 0
CHZZK_ID = os.getenv('CHZZK_ID')
STATUS_FILE = "last_status.txt"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
}

def get_last_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return f.read().strip()
    return "CLOSE"

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        f.write(status)

async def set_chat_lock(client, lock: bool):
    try:
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            overwrite = channel.overwrites_for(channel.guild.default_role)
            overwrite.send_messages = False if lock else True
            await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
            print(f"채팅창 {'잠금' if lock else '해제'} 완료")
    except Exception as e:
        print(f"권한 변경 실패: {e}")

async def run_check():
    intents = discord.Intents.default()
    # 봇 권한 설정 (Intents)
    intents.guilds = True
    intents.members = True 
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"로그인 성공: {client.user}")
        try:
            # 주소를 조금 더 안정적인 '공개 API' 주소로 변경했습니다.
            url = f'https://api.chzzk.naver.com/service/v2/channels/{CHZZK_ID}/live-status'
            r = requests.get(url, headers=headers)
            res = r.json()
            
            # 데이터 구조가 바뀐 경우를 대비해 안전하게 가져오기
            content = res.get('content')
            if not content:
                print("API 응답에 content가 없습니다.")
                await client.close()
                return

            current_status = content.get('status', 'CLOSE') 
            last_status = get_last_status()

            print(f"현재 상태: {current_status} / 이전 상태: {last_status}")

            if current_status != last_status:
                channel = client.get_channel(CHANNEL_ID)
                if channel:
                    if current_status == 'OPEN':
                        title = content.get('liveTitle', '제목 없음')
                        await channel.send(f"🔔 **방송 시작!**\n제목: {title}\n채팅창을 잠급니다.")
                        await set_chat_lock(client, True)
                    else:
                        await channel.send("📴 **방송 종료!**\n채팅창 잠금을 해제합니다.")
                        await set_chat_lock(client, False)
                
                save_status(current_status)
            
            await asyncio.sleep(2) # 연결 안정성을 위해 잠시 대기
            await client.close()
            
        except Exception as e:
            print(f"에러 발생 상세: {e}")
            await client.close()

    try:
        await client.start(TOKEN)
    except Exception as e:
        print(f"디스코드 연결 실패: {e}")

if __name__ == "__main__":
    if TOKEN and CHANNEL_ID:
        # 이벤트 루프 닫힘 에러 방지를 위해 새로운 루프 사용
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_check())
    else:
        print("환경 변수 설정 오류")
