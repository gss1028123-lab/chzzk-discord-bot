import requests
import os
import discord
import asyncio

# 설정 로드
TOKEN = os.environ.get('DISCORD_TOKEN')
CHANNEL_ID_RAW = os.environ.get('CHANNEL_ID')
CHZZK_ID = os.environ.get('CHZZK_ID', '').strip()
STATUS_FILE = "last_status.txt"

CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else 0

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

async def run_check():
    intents = discord.Intents.all()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"✅ 로그인 성공: {client.user}")
        # 보안을 위해 ID 앞뒤 3글자만 노출해서 확인용으로 찍습니다.
        print(f"📡 체크 대상 ID: {CHZZK_ID[:3]}...{CHZZK_ID[-3:]}")
        
        try:
            # 현재 치지직에서 가장 안정적인 오픈 API 엔드포인트입니다.
            url = f'https://api.chzzk.naver.com/open/v1/channels/{CHZZK_ID}/live-status'
            
            r = requests.get(url, headers=headers, timeout=10)
            print(f"🌐 API 응답 코드: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                content = data.get('content')
                
                if not content:
                    print("🚨 content 데이터가 비어있습니다.")
                    await client.close()
                    return

                current_status = content.get('status', 'CLOSE')
                last_status = get_last_status()

                print(f"📊 상태: {current_status} (이전: {last_status})")

                if current_status != last_status:
                    channel = client.get_channel(CHANNEL_ID)
                    if channel:
                        if current_status == 'OPEN':
                            title = content.get('liveTitle', '제목 없음')
                            await channel.send(f"🔔 **방송 시작!**\n제목: {title}\nhttps://chzzk.naver.com/live/{CHZZK_ID}")
                        else:
                            await channel.send("📴 **방송 종료!**")
                    save_status(current_status)
            else:
                print(f"🚨 API 호출 실패: {r.text[:100]}")
            
            await asyncio.sleep(2)
            await client.close()
            
        except Exception as e:
            print(f"🚨 에러 발생: {e}")
            await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    if TOKEN and CHANNEL_ID and CHZZK_ID:
        asyncio.run(run_check())
    else:
        print("🚨 설정값(Secrets) 로드 실패")
