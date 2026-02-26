import requests
import asyncio
import os
import discord
import time

# 깃허브 금고(Secrets)에서 데이터 가져오기
# 로컬에서 테스트할 때를 대비해 기본값도 설정 가능합니다.
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_STR = os.getenv('CHANNEL_ID')
CHZZK_ID = os.getenv('CHZZK_ID')

# ID가 숫자인지 확인 후 변환
CHANNEL_ID = int(CHANNEL_ID_STR) if CHANNEL_ID_STR else 0

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://chzzk.naver.com/'
}
url = f'https://api.chzzk.naver.com/service/v1/channels/{CHZZK_ID}/live-status'

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def set_chat_lock(lock: bool):
    """채널 채팅 잠금 또는 해제"""
    try:
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            # @everyone 권한 가져오기
            overwrite = channel.overwrites_for(channel.guild.default_role)
            # lock이 True면 전송 불가, False면 전송 가능
            overwrite.send_messages = False if lock else True
            await channel.set_permissions(channel.guild.default_role, overwrite=overwrite)
            print(f"📢 디스코드 권한 변경 완료 (잠금: {lock})")
    except Exception as e:
        print(f"🚨 권한 변경 실패: {e}")

async def checking():
    await client.wait_until_ready()
    last_check = None # 초기값
    
    print(f"📡 감시 시작: {CHZZK_ID}")
    
    while not client.is_closed():
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                data = r.json()
                current_status = data['content']['status']
                
                # 상태가 변했을 때만 실행
                if current_status != last_check:
                    channel = client.get_channel(CHANNEL_ID)
                    if current_status == 'OPEN':
                        title = data['content'].get('liveTitle', '제목 없음')
                        await channel.send(f"🔔 **방송 ON!**\n채팅창을 잠급니다.\n제목: {title}")
                        await set_chat_lock(True)
                    else:
                        await channel.send("📴 **방송 OFF**\n채팅창 잠금을 해제합니다.")
                        await set_chat_lock(False)
                    last_check = current_status
            
            print(".", end="", flush=True)
        except Exception as e:
            print(f"🚨 에러: {e}")
            
        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(checking())

if __name__ == "__main__":
    if not TOKEN:
        print("🚨 에러: DISCORD_TOKEN을 찾을 수 없습니다. 환경 변수를 확인하세요.")
    else:
        client.run(TOKEN)
