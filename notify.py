import requests

def send_wechat(msg):
    # 你的 Token 填在这里
    token = "4e9d1184827941cfa070700f96af2446" 
    
    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": "UR团地房源提醒",
        "content": msg,
        "template": "html"
    }
    
    try:
        # 这就是普通的网页请求，公司防火墙不会拦截
        resp = requests.post(url, json=data)
        print("✅ 微信推送成功")
    except Exception as e:
        print(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    send_wechat("发现新房源！<br>房号: 101<br>价格: 10万")
