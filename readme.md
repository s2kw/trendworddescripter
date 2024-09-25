# トレンドワードをSlackに投稿する

あるトレンドワード収集サイトの内容を取得してSlackに投稿する。

## 準備
以下をまとめてコピペ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 実行
以下で実行できます

```bash
python askTrend.py
```


# 環境変数

Actionsで利用されるJobの中身で定義される環境変数は、実行環境に合わせてあらかじめ定義が必要。


`.github/workflows/auto_action.yml`

```yml
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```



