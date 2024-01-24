import streamlit as st
import requests
import pandas as pd
from models_description import description
# from streamlit_local_storage import LocalStorage

# def LocalStorageManager():
#     return LocalStorage()
# localS = LocalStorageManager()

# ===============================================================
# СТРАНИЦЫ
# 1 - Авторизация
# 2 - Регистрация
# 3 - Страница с информацией о пользователе
# 4 - Пополнение баланса
# 5 - Выбор модели
# 6 - Предсказание
# ===============================================================

def authenticate(username, password):
    response = requests.post(
        "http://127.0.0.1:8000/token",
        data={"username": username, "password": password},
    )
    return response.json().get("access_token")

def register(username, password):
    response = requests.post(
        "http://127.0.0.1:8000/register",
        data={"username": username, "password": password},
    )
    return response

st.title("FastAPI + Streamlit Integration")
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'model' not in st.session_state:
    st.session_state.model = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'money' not in st.session_state:
    st.session_state.money = None

# Авторизация
def login():
    st.header("Авторизация")
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")

    if st.button("Войти"):
        token = authenticate(username, password)
        if token:
            st.session_state.username = username
            st.session_state.token = token
            st.success(f"Вход выполнен успешно.")
            st.session_state.step = 3
            st.rerun()
        else:
            st.error("Неправильный username или пароль. Попробуйте ещё раз.")

    if st.button("Зарегистрироваться"):
        st.session_state.step = 2
        st.rerun()
if st.session_state.step == 1:
    login()

# Регистрация
elif st.session_state.step == 2:
    st.header("Регистрация")
    username = st.text_input("Имя пользователя")
    password = st.text_input("Пароль", type="password")

    if st.button("Регистрация"):
        answ = register(username, password)
        if answ:
            st.success(f"Вы успешно зарегистрированы!")
        else:
            st.error("Пользователь с таким именем уже зарегистрирован, выберите другое")

    if st.button("Авторизоваться"):
        st.session_state.step = 1
        st.rerun() 

# Страница с информацией о пользователе
elif st.session_state.step == 3:
    st.header("Личный кабинет")
    token = st.session_state.get("token")
    
    if not token:
            st.error('Failed, try to log in first')
            st.session_state.step = 1
            st.rerun()
    else:
        response = requests.post(
                f"http://127.0.0.1:8000/user_info",
                params={'token': token}
            )
        data = response.json()
        st.session_state.money = data["money"]
        st.text(f'Имя пользователя: {data["username"]}')
        st.text(f'Баланс: {data["money"]}')
        if st.session_state.model:
            st.text(f'Выбранная модель: {st.session_state.model}')
            if st.button("Предсказание"):
                st.session_state.step = 6
                st.rerun()
    col1, col2 = st.columns([1,3])

    with col1:            
        if st.button("Выбрать модель"):
            st.session_state.step = 5
            st.rerun() 
    with col2:
        if st.button("Пополнить баланс"):
            st.session_state.step = 4
            st.rerun()
    
    with st.expander("Показать историю операций"):
        cond = f"select * from user_operations where username = '{st.session_state.username}'"
        conn = st.connection(
            "user_operations",
            type="sql",
            url="sqlite:///./operations.db"
        )
        df = conn.query(cond, ttl=20)
        st.dataframe(df)


# Пополнение баланса 
elif st.session_state.step == 4:
    st.subheader("Пополнение баланса")
    amount = st.number_input("Введите количетсво денег", min_value=0.0, step=1.0)

    if st.button("Добавить"):
        token = st.session_state.get("token")
        # token = localS.getItem('token')
        if not token:
            st.error('Failed, try to log in first')
            st.session_state.step = 1
            st.rerun()
        else:
            response = requests.post(
                f"http://127.0.0.1:8000/add-money/{amount}",
                params={'token': token}
            )
            if response.status_code == 200:
                try:
                    data = response.json()
                    st.success(data["message"])
                    st.session_state.money = float(data["money"])
                    st.session_state.step = 3
                    st.rerun() 
                except Exception as e:
                    st.error(f"Error parsing JSON: {e}")
            else:
                st.error(f"Error {response.status_code}: {response.text}")

# Выбор модели
elif st.session_state.step == 5:
    st.header("Выбор модели")
    model_name = st.selectbox("Выберите модель", ["LogisticRegression", "KNeighborsClassifier", "GradientBoostingClassifier"], index=None)
    st.markdown(description)
    token = st.session_state.get("token")
    if not token:
            st.error('Failed, try to log in first')
            st.session_state.step = 1
            st.rerun()
    if model_name:
        
        response = requests.post(
            "http://localhost:8000/choose_model",
            params={"model_name": model_name, "token": token}
        )
        if response.status_code == 200:
            st.success(response.json())
            st.session_state.model = model_name
            st.session_state.step = 6
            st.rerun()
        else:  
            st.error(response.json()['detail'])
            if st.button("Пополнить баланс"):
                st.session_state.step = 4
                st.rerun()
        
# Предсказание
elif st.session_state.step == 6:
    st.header("Предсказание")
    token = st.session_state.get("token")
    if not token:
        st.error('Failed, try to log in first')
        st.session_state.step = 1
        st.rerun()
    model_name = st.session_state.model
    st.text(f'Вы выбрали модель {model_name}. \nЕсли хотите использовать другую, нажмите на кнопку ниже')
         
    if st.button("Изменить выбор модели"):
        st.session_state.step = 5
        st.rerun() 

    data2 = st.file_uploader("Загрузите файл в формате .csv", type=['csv'])
    # def fill_missing_values(data):
    #     for col in data.keys():
    #         if data[col] == None:
    #             data[col] = columns_dict_mean[col]
    
    if data2 is not None:
        try:
            data_pred = pd.read_csv(data2)
            file_path = f'files/{st.session_state.username}_data_pred.csv'
            data_pred.to_csv(file_path, index=False)
            
            
        except Exception as e:
            st.error(f'Возникла ошибка с введенными данными. {e}')

    if st.button("Выполнить предсказание"):
        try:
            
            response = requests.post(
                "http://localhost:8000/prediction",
                json={"token": token, "model_name": model_name, 'file_path': file_path},
                headers={'Content-Type': 'application/json'}
            )
            st.success(response.json())
        except Exception as e:
            st.error(e)
    


