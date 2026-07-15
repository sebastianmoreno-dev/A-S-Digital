from dotenv import load_dotenv

# Carga las variables de entorno de .env antes de construir la app, para que
# `python run.py` (no solo `flask run`) tome DATABASE_URL, SECRET_KEY, etc.
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
