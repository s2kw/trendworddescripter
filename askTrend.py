import requests
import time
import os
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


# credentials.py が存在する場合、それを実行して環境変数を設定
credentials_path = Path(__file__).parent / "credentials.py"
if credentials_path.exists():
    exec(open(credentials_path).read())

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# Slack Webhook URL
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

# ChatGPT API設定
CHATGPT_URL = "https://api.openai.com/v1/chat/completions"
CHATGPT_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

def get_explanation_from_chatgpt(word):
    encoded_word = quote_plus(word)
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{word}はTwitterのトレンドワードです。この単語について日本語で簡潔に説明し、(https://x.com/search?q={encoded_word}) と解説時に利用したソースのURLも一緒に返答をください。解説ができなかった場合はTwitterの検索URLだけは貼ってください。"}
        ]
    }
    
    retries = 3
    for _ in range(retries):
        try:
            response = requests.post(CHATGPT_URL, json=payload, headers=CHATGPT_HEADERS)
            response.raise_for_status()
            return response.json()['choices'][0]['text']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("Rate limit exceeded, waiting to retry...")
                time.sleep(10)  # Wait for 10 seconds before retrying
            else:
                raise e  # Reraise the error if it's not a rate limit error
        except requests.RequestException as e:
            print(f"Error fetching explanation from ChatGPT: {e}")
            return None

def post_to_slack(message):
    payload = {
        "attachments": [
            {
                "color": "#36a64f",  # 緑色のカラーコード
                "text": message
            }
        ]
    }
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Message posted to Slack successfully\n{message}")
    except requests.RequestException as e:
        print(f"Error posting message to Slack: {e}")

def get_trending_topics_from_web():
    url = "https://trends24.in/"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        trends = soup.select('a.trend-link')
        if trends:
            trend_texts = [trend.get_text(strip=True) for trend in trends]
            # トピックと順位（1から始まる）のペアのリストを作成
            ranked_trends = list(enumerate(trend_texts, 1))
            print(f"Found trends: {ranked_trends}")
            return ranked_trends[:10]  # 上位10件を返す
        else:
            print("No trends found")
            return []
    except requests.RequestException as e:
        print(f"Error fetching trending topics: {e}")
        return []

def replace_hash(text):
    # 文字列中の '#' を '%23' に置換
    return text.replace('#', '%23')
    

def main():
    ranked_trending_topics = get_trending_topics_from_web()
    print(f"Ranked trending topics: {ranked_trending_topics}")
    if not ranked_trending_topics:
        post_to_slack("トレンドトピックを取得できませんでした。")
        return

    for rank, topic in ranked_trending_topics:
        explanation = None #get_explanation_from_chatgpt(topic)
        if explanation:
            message = f"第{rank}位「{topic}」の説明:\n{explanation}"
            post_to_slack(message)
        else:
            encoded_topic = quote_plus(f'"{topic}"')
#             post_to_slack(f"第{rank}位「{topic}」の説明を取得できませんでした。\nhttps://x.com/search?q={ replace_hash(topic) }")
            post_to_slack(f"第{rank}位「{topic}」\nhttps://x.com/search?q={encoded_topic}")

if __name__ == "__main__":
    main()
