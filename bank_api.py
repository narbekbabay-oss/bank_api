from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI(title="Банковский API", version="1.0")

# ===== БАНКОВСКИЙ КЛАСС =====
class BankAccount:
    def __init__(self, owner_name, balance=0, history=None):
        self.owner = owner_name
        self.balance = balance
        self.history = history if history is not None else []

    def deposit(self, amount):
        if amount <= 0:
            return "Ошибка: сумма должна быть больше 0"
        self.balance += amount
        self.history.append(f"Пополнение: +{amount}")
        save_all_accounts()
        return f"Пополнено! Баланс: {self.balance}"

    def withdraw(self, amount):
        if amount <= 0:
            return "Ошибка: сумма должна быть больше 0"
        if amount > self.balance:
            return "Ошибка: недостаточно средств"
        self.balance -= amount
        self.history.append(f"Снятие: -{amount}")
        save_all_accounts()
        return f"Снято! Баланс: {self.balance}"

    def transfer(self, other_account, amount):
        if amount <= 0:
            return "Ошибка: сумма перевода должна быть больше 0"
        commission = max(1, int(amount * 0.01))
        total = amount + commission
        if total > self.balance:
            return f"Ошибка: нужно {total} руб. (перевод {amount} + комиссия {commission}), доступно {self.balance}"
        self.balance -= total
        other_account.balance += amount
        self.history.append(f"Перевод {other_account.owner}: -{amount} (комиссия -{commission})")
        other_account.history.append(f"Перевод от {self.owner}: +{amount}")
        save_all_accounts()
        return f"Перевод {amount} руб. от {self.owner} к {other_account.owner} выполнен! Комиссия: {commission} руб."

    def add_interest(self, rate=0.05):
        if self.balance <= 0:
            return f"Проценты не начислены: баланс {self.owner} нулевой или отрицательный"
        interest = int(self.balance * rate)
        self.balance += interest
        self.history.append(f"Начислены проценты: +{interest}")
        save_all_accounts()
        return f"Начислены проценты 5% на счёт {self.owner}: +{interest} руб. Баланс: {self.balance}"

    def to_dict(self):
        return {"owner": self.owner, "balance": self.balance, "history": self.history}

    @staticmethod
    def from_dict(data):
        return BankAccount(data["owner"], data["balance"], data["history"])

DATA_FILE = "bank_data.json"

def save_all_accounts():
    data = {name: acc.to_dict() for name, acc in accounts.items()}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_all_accounts():
    global accounts
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        accounts = {name: BankAccount.from_dict(info) for name, info in data.items()}
    else:
        accounts = {}

accounts = {}
load_all_accounts()

class TransferData(BaseModel):
    from_account: str
    to_account: str
    amount: int

@app.get("/")
def root():
    return {"message": "Банковский API работает!"}

@app.get("/accounts")
def get_all_accounts():
    return {name: acc.to_dict() for name, acc in accounts.items()}

@app.post("/account/{name}")
def create_account(name: str):
    if name in accounts:
        raise HTTPException(status_code=400, detail="Счёт уже существует")
    accounts[name] = BankAccount(name)
    save_all_accounts()
    return {"message": f"Счёт {name} создан!", "balance": 0}

@app.get("/account/{name}")
def get_account(name: str):
    if name not in accounts:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    return accounts[name].to_dict()

@app.post("/deposit/{name}/{amount}")
def deposit(name: str, amount: int):
    if name not in accounts:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    result = accounts[name].deposit(amount)
    return {"message": result}

@app.post("/withdraw/{name}/{amount}")
def withdraw(name: str, amount: int):
    if name not in accounts:
        raise HTTPException(status_code=404, detail="Счёт не найден")
    result = accounts[name].withdraw(amount)
    return {"message": result}

@app.post("/transfer")
def transfer(data: TransferData):
    if data.from_account not in accounts:
        raise HTTPException(status_code=404, detail="Счёт отправителя не найден")
    if data.to_account not in accounts:
        raise HTTPException(status_code=404, detail="Счёт получателя не найден")
    result = accounts[data.from_account].transfer(accounts[data.to_account], data.amount)
    return {"message": result}

@app.post("/interest")
def add_interest():
    results = []
    for name, acc in accounts.items():
        results.append(acc.add_interest())
    return {"results": results}
