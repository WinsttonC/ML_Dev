### Инструкция по установке

1. Установите все необходимые зависимости:

```bash
pip install -r requirements.txt
```

2. Запустите два терминала. Один для FastAPI, другой для Streamlit:

Для FastAPI:

```bash
uvicorn main:app --reload
```

Для Streamlit:

```bash
streamlit run app.py
```
Готово!

*Для предсказания можно использовать небольшую подвыборку из данных `train_data.csv`*