from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from db_users import get_db_users, User
from db_operations import get_db_operations, UserOperations
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from joblib import load
from jose import jwt, JWTError
import pandas as pd

SECRET_KEY = "dftg11yhujikog34567jik8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

app = FastAPI()
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str):#Depends(oauth2_scheme)):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return username

def get_user(db, user_name: str):
    return db.query(User).filter(User.username == user_name).first()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функция для проверки пароля
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_user(db, user: dict):
    hashed_password = pwd_context.hash(user['password'])
    
    db_user = User(
        username=user['username'],
        hashed_password=hashed_password,
        money=0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def add_operation(db, operation_info: dict):
    db_operation = UserOperations(
        username=operation_info['username'],
        message=operation_info['message'],
        date=operation_info['date']
    )
    db.add(db_operation)
    db.commit()
    db.refresh(db_operation)
    return db_operation

@app.post("/register")
def register_user(user:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_users)):
    
    db_user = get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    else:
        user_dict = {'username': user.username, 'password': user.password}
        create_user(db, user_dict)
    
    return True

@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(use_cache=True), 
                            #form_data: UserLogin,
                            db: Session = Depends(get_db_users)):
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"username": user.username}, expires_delta=access_token_expires
    )
    print(access_token)
    return Token(access_token=access_token, token_type="bearer")

# Функция для добавления денег на счет пользователя
def add_money(amount, current_user: str, db, db_op):
    user = get_user(db, current_user)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if amount <= 0:
        raise HTTPException(status_code=400, detail="Deposit amount must be positive")

    user.money += amount
    db.commit()
    db.refresh(user)
    operation_info = {
        'username': user.username,
        'message' : f'Пополнение счета на {amount} кредитов.',
        'date' : datetime.now()
    }
    add_operation(db_op, operation_info)
    return {"message": f"Successfully added {amount} to your account.", 
            'money' :f'{user.money}'}

@app.post("/add-money/{amount}")
def add_money_to_account(amount: float, 
                         token,
                         db: Session = Depends(get_db_users),
                         db_op: Session = Depends(get_db_operations)):
    current_user = get_current_user(token)
    
    return add_money(amount, current_user, db, db_op)

available_models = {
    "LogisticRegression" : 6.0, 
    "KNeighborsClassifier" : 4.0, 
    "GradientBoostingClassifier" : 9.0
}

def check_balance(user, db):
    db_user = get_user(db, user.username)


@app.post("/user_info")
def models_list(token, db: Session = Depends(get_db_users)):
    current_user = get_current_user(token)
    user = get_user(db, current_user)
    return {"username": user.username, "money": user.money}

@app.post("/choose_model")
def models_list(token, model_name: str = None,  db: Session = Depends(get_db_users)):
    current_user = get_current_user(token)
    user = get_user(db, current_user)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.money < available_models[model_name]:
        raise HTTPException(status_code=404, detail="Недостаточно средств")
    else:
        return f"Выбрана модель {model_name}"

class Prediction(BaseModel):
    token: str
    model_name: str
    file_path: str

@app.post("/prediction")
def prediction(#token,
               #model_name: str, 
               #file_path: str,
               input_data: Prediction,
               db: Session = Depends(get_db_users),
               db_op: Session = Depends(get_db_operations)):
    token = input_data.token
    model_name = input_data.model_name
    file_path = input_data.file_path

    current_user = get_current_user(token)
    user = get_user(db, current_user)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        model = load(f"models/{model_name}.joblib")
        data = pd.read_csv(file_path)
        prediction = model.predict(data) 
        prediction = f'Результат предсказания: {str(list(prediction))}'
        user.money -= available_models[model_name]
        db.commit()
        db.refresh(user)

        operation_info_1 = {
            'username': user.username,
            'message' : f'Со счета списано {available_models[model_name]} кредитов.',
            'date' : datetime.now()
        }
        add_operation(db_op, operation_info_1)
        operation_info_2 = {
            'username': user.username,
            'message' : f'Выполнено предсказание с использованием {model_name}.',
            'date' : datetime.now()
        }
        add_operation(db_op, operation_info_2)

        return prediction
    except Exception as e:
        return f'Неудачная попытка выполнения предсказания. Попробуйте еще раз ({e})'