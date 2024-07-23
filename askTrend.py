import requests
import os
from pathlib import Path
from bs4 import BeautifulSoup

# credentials.py が存在する場合、それを実行して環境変数を設定
credentials_path = Path(__file__).parent / "credentials.py"
if credentials_path.exists():
    exec(open(credentials_path).read())

# Slack Webhook URL
SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']

# ChatGPT API設定
CHATGPT_URL = "https://api.openai.com/v1/chat/completions"
CHATGPT_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
}

def get_explanation_from_chatgpt(word):
    payload = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{word}はTwitterのトレンドワードです。この単語について日本語で簡潔に説明しXの検索状態のURL( https://x.com/search?q=<ここに対象キーワードを入れる> )も一緒に返答をください。"}
        ]
    }
    
    try:
        response = requests.post(CHATGPT_URL, json=payload, headers=CHATGPT_HEADERS)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.RequestException as e:
        print(f"Error fetching explanation from ChatGPT: {e}")
        return None

def post_to_slack(message):
    payload = {"text": message}
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Message posted to Slack successfully\n{message}")
    except requests.RequestException as e:
        print(f"Error posting message to Slack: {e}")

def get_trending_hashtags_from_web():
    url = "https://trends24.in/"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print(f"Response status code: {response.status_code}")
        print(f"Response content preview: {response.text[:500]}...")

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # トレンドアイテムを取得する新しいセレクタ
        trend_items = soup.select('li.trend-card__item')
        
        hashtags = []
        for item in trend_items:
            trend_text = item.get_text(strip=True)
            if trend_text.startswith('#'):
                hashtags.append(trend_text)
        
        print(f"Found hashtags: {hashtags}")
        return hashtags[:10]  # 上位10件を返す
    except requests.RequestException as e:
        print(f"Error fetching trending hashtags: {e}")
        return []

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

def main():
    ranked_trending_topics = get_trending_topics_from_web()
    print(f"Ranked trending topics: {ranked_trending_topics}")
    if not ranked_trending_topics:
        post_to_slack("トレンドトピックを取得できませんでした。")
        return

    for rank, topic in ranked_trending_topics:
        explanation = get_explanation_from_chatgpt(topic)
        if explanation:
            message = f"第{rank}位「{topic}」の説明:\n{explanation}"
            post_to_slack(message)
        else:
            post_to_slack(f"第{rank}位「{topic}」の説明を取得できませんでした。")

if __name__ == "__main__":
    main()