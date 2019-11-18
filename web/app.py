"""
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.BankAPI
users = db["users"]

def UserExist(username):
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True

def verifyPw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username" : username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def cashWithUser(username):
    cash = users.find({"Username": username})[0]["Own"]
    return cash

def debtWithUser(username):
    debt = users.find({"Username" : username})[0]["Debt"]
    return debt

def generateReturnDictionary(status, msg):
    retJson= {
        "status": status,
        "msg": msg
    }
    return retJson

def verifyCredentials(username, password):
    if not UserExist(username):
        return generateReturnDictionary(301, "User doesn't exist, Please Register First"), True

    correct_pw = verifyPw(username, password)

    if not correct_pw:
        return generateReturnDictionary(302, "Incorrect Password"), True

    return None, False

def updateAccount(username, balance):
    users.update({
        "Username": username
    },{
        "$set":{
            "Own": balance
        }
    })

def updateDebt(username, balance):
    users.update({
        "Username" : username
    },{
        "$set" : {
            "Debt": balance
        }
    })

@app.route("/signup", methods = ["GET", "POST"])
class Register(Resource):

    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "This User allready exist"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Own" : 0,
            "Debt" : 0
        })

        retJson = {
            "status" : 200,
            "msg" : "You Successfully Signed up for the API"
        }
        return jsonify(retJson)


class Add(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        if money <= 0:
            return jsonify(generateReturnDictionary(304, "The amount entered must be > 0"))

        cash = cashWithUser(username)
        money -= 1
        bank_cash = cashWithUser("BANK")
        updateAccount("BANK", bank_cash+ 1)
        updateAccount(username, cash+money)

        return jsonify(generateReturnDictionary(200, "Amount added successfully to account"))

class Transfer(Resource):
    def post(self):
        postedData= request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        to = postedData["to"]
        money = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        cash = cashWithUser(username)
        if int(cash) <= 0 or money > int(cash):
            return jsonify(generateReturnDictionary(304, "You are out of money please add or take a loan"))

        if not UserExist(to):
            return jsonify(generateReturnDictionary(301, "Receiver Username is Invalid"))

        cash_from = cashWithUser(username)
        cash_to = cashWithUser(to)
        bank_cash = cashWithUser("BANK")

        updateAccount("BANK", bank_cash+1)
        updateAccount(to, cash_to + money - 1)
        updateAccount(username, cash_from-money)

        return jsonify(generateReturnDictionary(200, "Amount Transfered successfully"))

class Balance(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        retJson = users.find({
            "Username": username
        }, {
            "Password": 0,
            "_id": 0
        })[0]

        return jsonify(retJson)

class TakeLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        if int(money) <= 0:
            return jsonify(generateReturnDictionary(200, "Sorry you can not enter negative amount"))

        cash = cashWithUser(username)
        debt = debtWithUser(username)
        updateAccount(username, cash+money)
        updateDebt(username, debt+money)

        return jsonify(generateReturnDictionary(200, "Loan added to your account"))

class PayLoan(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        money = postedData["amount"]

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        if int(money) <= 0:
            return jsonify(generateReturnDictionary(200, "Sorry you can not enter negative amount"))

        cash = cashWithUser(username)

        if cash < money:
            return jsonify(generateReturnDictionary(303, "Not enough cash in your Account"))

        debt = debtWithUser(username)
        updateAccount(username, cash - money)
        updateDebt(username, debt - money)

        return jsonify(generateReturnDictionary(200, "You've successfully paid your loan"))

api.add_resource(Register, "/register")
api.add_resource(Add, "/add")
api.add_resource(Transfer, "/transfer")
api.add_resource(Balance, "/balance")
api.add_resource(TakeLoan, "/takeloan")
api.add_resource(PayLoan, "/payloan")

if __name__=="__main__":
    app.run(host="0.0.0.0")

"""
from flask import Flask, jsonify, request, render_template
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.BankAPI
users = db["users"]

def UserExist(username):
    if users.find({"Username": username}).count() == 0:
        return False
    else:
        return True

def verifyPw(username, password):
    if not UserExist(username):
        return False

    hashed_pw = users.find({
        "Username" : username
    })[0]["Password"]

    if bcrypt.hashpw(password.encode("utf8"), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def cashWithUser(username):
    cash = users.find({"Username": username})[0]["Own"]
    return cash

def debtWithUser(username):
    debt = users.find({"Username" : username})[0]["Debt"]
    return debt

def generateReturnDictionary(status, msg):
    retJson= {
        "status": status,
        "msg": msg
    }
    return retJson

def verifyCredentials(username, password):
    if not UserExist(username):
        return generateReturnDictionary(301, "User doesn't exist, Please Register First"), True

    correct_pw = verifyPw(username, password)

    if not correct_pw:
        return generateReturnDictionary(302, "Incorrect Password"), True

    return None, False

def updateAccount(username, balance):
    users.update({
        "Username": username
    },{
        "$set":{
            "Own": balance
        }
    })

def updateDebt(username, balance):
    users.update({
        "Username" : username
    },{
        "$set" : {
            "Debt": balance
        }
    })


@app.route("/signup", methods = ["GET", "POST"])
def Register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "This User allready exist"
            }
            return jsonify(retJson)

        hashed_pw = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())

        users.insert({
            "Username": username,
            "Password": hashed_pw,
            "Own" : 0,
            "Debt" : 0
        })

        retJson = {
            "status" : 200,
            "msg" : "You Successfully Signed up for the API"
        }
        return jsonify(retJson)
    return render_template("signup.html")

@app.route("/add", methods = ["GET", "POST"])
def Add():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        money = request.form["amount"]
        money = int(money)
        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        if int(money) <= 0:
            return jsonify(geusernamenerateReturnDictionary(304, "The amount entered must be > 0"))

        cash = cashWithUser(username)
        money -= 1
        bank_cash = cashWithUser("BANK")
        updateAccount("BANK", bank_cash+ 1)
        updateAccount(username, cash+money)

        return jsonify(generateReturnDictionary(200, "Amount added successfully to Account"))
    return render_template("Add.html")

@app.route("/transfer", methods = ["GET", "POST"])
def Transfer():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        to = request.form["to"]
        money = request.form["amount"]
        money = int(money)

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        cash = cashWithUser(username)
        if int(cash) <= 0 or int(money) > int(cash):
            return jsonify(generateReturnDictionary(304, "You are out of money please add or take a loan"))

        if not UserExist(to):
            return jsonify(generateReturnDictionary(301, "Receiver Username is Invalid"))

        cash_from = cashWithUser(username)
        cash_to = cashWithUser(to)
        bank_cash = cashWithUser("BANK")

        updateAccount("BANK", bank_cash+1)
        updateAccount(to, cash_to + money - 1)
        updateAccount(username, cash_from-money)

        return jsonify(generateReturnDictionary(200, "Amount Transfered successfully"))
    return render_template("Transfer.html")

@app.route("/balance", methods = ["GET", "POST"])
def Balance():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        retJson = users.find({
            "Username": username
        }, {
            "Password": 0,
            "_id": 0
        })[0]

        return jsonify(retJson)
    return render_template("Balance.html")

@app.route("/takeloan", methods = ["GET", "POST"])
def TakeLoan():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        money = request.form["amount"]
        money = int(money)

        retJson, error = verifyCredentials(username, password)
        if error:
            return jsonify(retJson)

        if int(money) <= 0:
            return jsonify(generateReturnDictionary(200, "Sorry you can not enter negative amount"))

        cash = cashWithUser(username)
        debt = debtWithUser(username)
        updateAccount(username, cash+money)
        updateDebt(username, debt+money)

        return jsonify(generateReturnDictionary(200, "Loan added to your account"))
    return render_template("takeloan.html")

@app.route("/payloan", methods = ["GET", "POST"])
def PayLoan():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        money = request.form["amount"]
        money = int(money)

        retJson, error = verifyCredentials(username, password)

        if error:
            return jsonify(retJson)

        if int(money) <= 0:
            return jsonify(generateReturnDictionary(200, "Sorry you can not enter negative amount"))

        cash = cashWithUser(username)

        if cash < money:
            return jsonify(generateReturnDictionary(303, "Not enough cash in your Account"))

        debt = debtWithUser(username)

        if money > debt:
            return jsonify(generateReturnDictionary(303, "Sorry! you are paying more than your debt sheikh Sahb"))

        updateAccount(username, cash - money)
        updateDebt(username, debt - money)

        return jsonify(generateReturnDictionary(200, "You've successfully paid your loan"))
    return render_template("payloan.html")

if __name__=="__main__":
    app.run(debug = "True", host="0.0.0.0")
