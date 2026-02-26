import requests
import os

def check_and_run():
    # --- 설정값 불러오기 ---
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

    # 1. 치지직 상태 확인 (접속 에러 방지 로직 추가)
    chzzk_url = f"https://api.chzzk.naver.com/service/v1/channels/{STREAMER_ID}/live-status"
    # 네이버가 로봇으로 오해하지 않도록 브라우저 정보를 더 자세히 넣습니다.
    chzzk_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(chzzk_url, headers=chzzk_headers)
        # 응답이 정상인지 확인 (200 OK가 아니면 에러 발생)
        response.raise_for_status() 
        res_data = response.json()
        status = res_data.get('content', {}).get('status', 'CLOSE')
    except Exception as e:
        print(f"⚠️ 치지직 접속 중 오류 발생: {e}")
        # 접속 실패 시 안전하게 종료 (에러로 멈추지 않음)
        return 

    print(f"📡 현재 치지직 상태: {status}")

    # 2. 각 채널별 권한 제어
    for channel_id in CHANNEL_IDS:
        try:
            channel_url = f"https://discord.com/api/v10/channels/{channel_id}"
            c_data = requests.get(channel_url, headers=headers).json()
            
            overwrites = c_data.get('permission_overwrites', [])
            is_locked = any((ow['id'] == SERVER_ID and (int(ow['deny']) & 2048) == 2048) for ow in overwrites)

            if status == 'OPEN' and not is_locked:
                payload = {"allow": "0", "deny": "2048", "type": 0}
                requests.put(f"{channel_url}/permissions/{SERVER_ID}", json=payload, headers=headers)
                print(f"🔒 채널 {channel_id}: 잠금 완료")
            elif status == 'CLOSE' and is_locked:
                requests.delete(f"{channel_url}/permissions/{SERVER_ID}", headers=headers)
                print(f"🔓 채널 {channel_id}: 잠금 해제 완료")
            else:
                print(f"✅ 채널 {channel_id}: 상태 유지 중")
        except Exception as e:
            print(f"⚠️ 디스코드 채널 {channel_id} 제어 실패: {e}")

if __name__ == "__main__":
    check_and_run()
