import requests
import os

def check_and_run():
    # 🚨 깃허브 설정(Secrets)에서 가져올 값들입니다.
    STREAMER_ID = "ec1ea72f238ffa4d6de7f1c7f9edc050"
    DISCORD_TOKEN = os.getenv("MTQ3NjU0Nzg4MzU3NzkwMTExOQ.Gww5pF.ibjsRQc1HARQMLw0ji0Gu_1hGT9-ze-eb92nKw")
    ROLE_ID = os.getenv("1379497803214229514") # @everyone 역할 ID
    CHANNEL_IDS = os.getenv("1379497803805622374") # 여러 채널은 쉼표로 구분

    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. 치지직 상태 확인
    chzzk_url = f"https://api.chzzk.naver.com/service/v1/channels/{STREAMER_ID}/live-status"
    res = requests.get(chzzk_url, headers={"User-Agent": "Mozilla/5.0"}).json()
    status = res.get('content', {}).get('status', 'CLOSE')

    # 2. 각 채널별 권한 제어
    for channel_id in CHANNEL_IDS:
        channel_id = channel_id.strip()
        channel_url = f"https://discord.com/api/v10/channels/{channel_id}"
        c_res = requests.get(channel_url, headers=headers).json()
        
        overwrites = c_res.get('permission_overwrites', [])
        is_locked = any((ow['id'] == ROLE_ID and (int(ow['deny']) & 2048) == 2048) for ow in overwrites)

        if status == 'OPEN' and not is_locked:
            payload = {"allow": "0", "deny": "2048", "type": 0}
            requests.put(f"{channel_url}/permissions/{ROLE_ID}", json=payload, headers=headers)
            print(f"🔒 {channel_id} 잠금 완료")
        elif status == 'CLOSE' and is_locked:
            requests.delete(f"{channel_url}/permissions/{ROLE_ID}", headers=headers)
            print(f"🔓 {channel_id} 잠금 해제 완료")

if __name__ == "__main__":
    check_and_run()
