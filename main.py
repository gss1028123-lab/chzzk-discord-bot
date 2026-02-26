import requests
import os

def check_and_run():
    # 주신 주소에서 확인된 스트리머 ID입니다.
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

    # 치지직 최신 API 주소 형식으로 변경 (v1 사용)
    # 주소 끝에 /live-status 대신 채널 정보만 가져와서 상태를 확인합니다.
    chzzk_url = f"https://api.chzzk.naver.com/service/v1/channels/{STREAMER_ID}/live-status"
    chzzk_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(chzzk_url, headers=chzzk_headers)
        
        # 만약 404가 뜨면 API 경로를 v2로 바꿔서 한 번 더 시도합니다.
        if response.status_code == 404:
            chzzk_url = f"https://api.chzzk.naver.com/service/v2/channels/{STREAMER_ID}/live-status"
            response = requests.get(chzzk_url, headers=chzzk_headers)
            
        response.raise_for_status()
        res_data = response.json()
        
        # 치지직 API 구조에 맞춰 상태 추출
        status = res_data.get('content', {}).get('status', 'CLOSE')
        print(f"📡 현재 치지직 상태: {status}")
        
    except Exception as e:
        print(f"⚠️ 치지직 접속 오류 발생: {e}")
        return

    # --- 디스코드 제어 로직 ---
    for channel_id in CHANNEL_IDS:
        try:
            channel_url = f"https://discord.com/api/v10/channels/{channel_id}"
            c_data = requests.get(channel_url, headers=headers).json()
            overwrites = c_data.get('permission_overwrites', [])
            is_locked = any((ow['id'] == SERVER_ID and (int(ow['deny']) & 2048) == 2048) for ow in overwrites)

            if status == 'OPEN' and not is_locked:
                requests.put(f"{channel_url}/permissions/{SERVER_ID}", json={"allow": "0", "deny": "2048", "type": 0}, headers=headers)
                print(f"🔒 채널 {channel_id}: 방송 시작 -> 잠금 완료")
            elif status == 'CLOSE' and is_locked:
                requests.delete(f"{channel_url}/permissions/{SERVER_ID}", headers=headers)
                print(f"🔓 채널 {channel_id}: 방송 종료 -> 잠금 해제 완료")
            else:
                print(f"✅ 채널 {channel_id}: 상태 유지 중")
        except Exception as e:
            print(f"⚠️ 디스코드 제어 에러 ({channel_id}): {e}")

if __name__ == "__main__":
    check_and_run()
