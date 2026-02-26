import requests
import os
import discord
import asyncio

# 설정 로드
TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_RAW = os.environ.get('CHANNEL_ID')
CHZZK_ID = os.environ.get('CHZZK_ID', '').strip() # 공백 제거
STATUS_FILE = "last_status.txt"

CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else 0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': f'https://chzzk.naver.com/live/{CHZZK_ID}',
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
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✅ 로그인 성공: {client.user}")
        try:
            # v1과 v2 두 주소를 모두 테스트합니다.
            urls = [
                f'https://api.chzzk.naver.com/service/v2/channels/{CHZZK_ID}/live-status',
                f'https://api.chzzk.naver.com/service/v1/channels/{CHZZK_ID}/live-status'
            ]
            
            data = None
            for url in urls:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    print(f"📡 API 연결 성공: {url}")
                    break
            
            if not data:
                print(f"🚨 모든 API 주소 실패 (ID: {CHZZK_ID} 확인 필요)")
                await client.close()
                return

            content = data.get('content')
            current_status = content.get('status', 'CLOSE') if content else 'CLOSE'
            last_status = get_last_status()

            print(f"📊 상태: {current_status} (이전: {last_status})")

            if current_status != last_status:
                channel = client.get_channel(CHANNEL_ID)
                if channel:
                    if current_status == 'OPEN':
                        title = content.get('liveTitle', '제목 없음')
                        await channel.send(f"🔔 **방송 시작!**\n제목: {title}\nhttps://chzzk.naver.com/live/{CHZZK_ID}")
                        await set_chat_lock(client, True)
                    else:
                        await channel.send("📴 **방송 종료!**")
                        await set_chat_lock(client, False)
                save_status(current_status)
            
            await asyncio.sleep(2)
            await client.close()
            
        except Exception as e:
            print(f"🚨 에러: {e}")
            await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    if TOKEN and CHANNEL_ID and CHZZK_ID:
        asyncio.run(run_check())
    else:
        print(f"🚨 설정 오류: TOKEN={bool(TOKEN)}, ID={bool(CHANNEL_ID)}, CHZZK={bool(CHZZK_ID)}")
