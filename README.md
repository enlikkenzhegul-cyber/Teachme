# Teach Me

Оқу мәтінінен үйренуге арналған карточкалар жасайтын шағын Django жобасы.

## Мақсаты

Пайдаланушы тақырып пен оқу мәтінін енгізеді, жүйе одан карточкалар (сұрақ, жауап, дәйексөз) жасайды. Әр карточканың дәйексөзі мәтінде дәл бар болуы тексеріледі. Сақталған конспектілер кейін қарау үшін дерекқорда қалады.

## Технологиялар

- Python 3
- Django (нақты нұсқасы `requirements.txt`-те)
- Сыртқы HTTP кітапханасыз — `urllib` (LIVE режимі үшін)
- Дерекқор: Django әдепкі (SQLite)

## Жылдам бастау

### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000