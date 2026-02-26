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
    'Referer': 'https://chzzk.naver.com/'
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
    """디스코드 채팅 잠금/해제 함수"""
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
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        try:
            url = f'https://api.chzzk.naver.com/service/v1/channels/{CHZZK_ID}/live-status'
            r = requests.get(url, headers=headers)
            data = r.json()
            current_status = data['content']['status'] # 'OPEN' 또는 'CLOSE'
            last_status = get_last_status()

            # 상태가 변했을 때만 작동
            if current_status != last_status:
                channel = client.get_channel(CHANNEL_ID)
                if current_status == 'OPEN':
                    title = data['content'].get('liveTitle', '제목 없음')
                    await channel.send(f"🔔 **방송 시작!**\n제목: {title}\n채팅창을 잠급니다.")
                    await set_chat_lock(client, True)
                else:
                    await channel.send("📴 **방송 종료!**\n채팅창 잠금을 해제합니다.")
                    await set_chat_lock(client, False)
                
                save_status(current_status)
            
            await client.close()
        except Exception as e:
            print(f"에러 발생: {e}")
            await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    if TOKEN and CHANNEL_ID:
        asyncio.run(run_check())
    else:
        print("환경 변수(TOKEN, CHANNEL_ID)가 설정되지 않았습니다.")
