import requests
import os
import discord
import asyncio

# 설정 로드
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID')) if os.getenv('CHANNEL_ID') else 0
CHZZK_ID = os.getenv('CHZZK_ID')
STATUS_FILE = "last_status.txt"

# 네이버 차단 방지를 위한 정밀 헤더 설정
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': f'https://chzzk.naver.com/live/{CHZZK_ID}',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
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
            print(f"📢 채팅창 {'잠금' if lock else '해제'} 완료")
    except Exception as e:
        print(f"🚨 권한 변경 실패: {e}")

async def run_check():
    # 모든 권한(Intents) 활성화
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✅ 로그인 성공: {client.user}")
        try:
            # 현재 가장 안정적인 v1 live-status 주소입니다.
            url = f'https://api.chzzk.naver.com/service/v1/channels/{CHZZK_ID}/live-status'
            
            # 요청 시 타임아웃(10초)을 설정하여 무한 대기를 방지합니다.
            r = requests.get(url, headers=headers, timeout=10)
            
            if r.status_code != 200:
                print(f"❌ API 요청 실패 (상태코드: {r.status_code})")
                await client.close()
                return

            # JSON 파싱 전 예외 처리
            try:
                data = r.json()
            except Exception as json_e:
                print(f"❌ JSON 해석 실패: {json_e}")
                print(f"받은 데이터 내용: {r.text[:200]}") # 에러 분석용
                await client.close()
                return

            content = data.get('content')
            if not content:
                print("❌ 'content' 데이터를 찾을 수 없습니다.")
                await client.close()
                return

            current_status = content.get('status', 'CLOSE') # 'OPEN' 또는 'CLOSE'
            last_status = get_last_status()

            print(f"📡 상태 체크 완료 - 현재: {current_status} | 이전: {last_status}")

            if current_status != last_status:
                channel = client.get_channel(CHANNEL_ID)
                if channel:
                    if current_status == 'OPEN':
                        title = content.get('liveTitle', '제목 없음')
                        await channel.send(f"🔔 **방송 시작!**\n제목: {title}\n링크: https://chzzk.naver.com/live/{CHZZK_ID}")
                        await set_chat_lock(client, True)
                    else:
                        await channel.send("📴 **방송 종료!**")
                        await set_chat_lock(client, False)
                
                save_status(current_status)
            
            await asyncio.sleep(1)
            await client.close()
            
        except Exception as e:
            print(f"🚨 런타임 에러: {e}")
            await client.close()

    try:
        await client.start(TOKEN)
    except Exception as e:
        print(f"🚨 디스코드 시작 실패: {e}")

if __name__ == "__main__":
    if TOKEN and CHANNEL_ID and CHZZK_ID:
        # 이벤트 루프 실행
        asyncio.run(run_check())
    else:
        print("🚨 설정값(Secrets)이 비어있습니다. 확인해 주세요.")
