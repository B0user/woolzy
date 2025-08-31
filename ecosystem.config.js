module.exports = {
    apps: [
      {
        name: "tg-bot",
        script: "main.py",
        interpreter: "python3",
        env: {
          BOT_TOKEN: "твой_токен"
        }
      }
    ]
  }
  