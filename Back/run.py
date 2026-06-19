from app import create_app

app = create_app()

if __name__ == "__main__":
    # Сервер для разработки. На бой так не запускают (см. деплой в README) —
    # там используют gunicorn/uvicorn за nginx.
    app.run(debug=True, host="127.0.0.1", port=5000)
