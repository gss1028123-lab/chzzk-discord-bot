import requests
import os

def check_and_run():
    # 주신 주소에서 확인된 스트리머 고유 ID
    STREAMER_ID = "ec1ea72f238ffa4d6de7f1c7f9edc050"
    
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    SERVER_ID = os.getenv("SERVER_ID")
    channel_raw = os.getenv("CHANNEL_IDS", "")
    CHANNEL_IDS = [cid.strip() for cid in channel_raw.split(",") if cid.strip()]

    if not DISCORD_TOKEN or not SERVER_ID or not CHANNEL_IDS:
        print("❌ 설정값이 부족합니다. GitHub Secrets를 확인하세요.")
        return

    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }

    # 치지직 접속용 헤더 (브라우저처럼 보이게 더 보강)
    chzzk_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": f"https://chzzk.naver.com/live/{STREAMER_ID}"
    }
    
    status = "CLOSE"
    
    # 404를 피하기 위해 두 가지 다른 API 주소를 순서대로 시도합니다.
    target_urls = [
        f"https://api.chzzk.naver.com/service/v2/channels/{STREAMER_ID}/live-status",
        f"https://api.chzzk.naver.com/polling/v2/channels/{STREAMER_ID}/live-status"
    ]
    
    for url in target_urls:
        try:
            print(f"🔗 접속 시도 중: {url}")
            response = requests.get(url, headers=chzzk_headers, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                status = res_data.get('content', {}).get('status', 'CLOSE')
                print(f"✅ 접속 성공! 현재 상태: {status}")
                break
            else:
                print(f"⚠️ {url} 접속 실패 (상태코드: {response.status_code})")
        except Exception as e:
            print(f"⚠️ 에러 발생: {e}")

    # --- 디스코드 제어 로직 ---
    for channel_id in CHANNEL_IDS:
        try:
            channel_url = f"https://discord.com/api/v10/channels/{channel_id}"
            c_data = requests.get(channel_url, headers=headers).json()
            overwrites = c_data.get('permission_overwrites', [])
            is_locked = any((ow['id'] == SERVER_ID and (int(ow['deny']) & 2048) == 2048) for ow in overwrites)

            if status == 'OPEN' and not is_locked:
                requests.put(f"{channel_url}/permissions/{SERVER_ID}", json={"allow": "0", "deny": "2048", "type": 0}, headers=headers)
                print(f"🔒 채널 {channel_id}: 잠금 완료")
            elif status == 'CLOSE' and is_locked:
                requests.delete(f"{channel_url}/permissions/{SERVER_ID}", headers=headers)
                print(f"🔓 채널 {channel_id}: 잠금 해제 완료")
            else:
                print(f"✅ 채널 {channel_id}: 상태 유지 중")
        except Exception as e:
            print(f"⚠️ 디스코드 제어 에러 ({channel_id}): {e}")

if __name__ == "__main__":
    check_and_run()
