from flask import request, redirect, Flask, render_template, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import secrets
from flask_migrate import Migrate
import requests
import json
from sqlalchemy.exc import IntegrityError

from datetime import datetime, timedelta


ph = PasswordHasher()

app = Flask(__name__)

app.secret_key = secrets.token_hex(32)




app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = False

app.config['SQLALCHEMY_BINDS'] = {
        'tasks_db': 'sqlite:///tasks.db'
    }

db = SQLAlchemy(app)

migrate = Migrate(app,db)





class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    Hashed_password = db.Column(db.String(300), nullable=False)
    
   

class Tasks(db.Model):

    __tablename__ = 'tasks'

    __bind_key__ = 'tasks_db'
    
    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(250), nullable=False)
 
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, nullable=False)


   

# when url is accessed, redirects user to home page 
@app.route('/')
def goHome():
    return redirect(url_for('NewAccount'))

# returns page for creating a new account
@app.route('/NewAccount')
def NewAccount ():
    return render_template('Register.html')

#stores users info into database on submit and redirects user to a login page
@app.route('/submit', methods=['GET','POST'])
def submit():
    username = None
    if request.method == 'POST':
        try:
            username= request.form['username']
            Hashed_password= ph.hash(request.form['password'])

            new_user = User(username=username, Hashed_password=Hashed_password)
            db.session.add(new_user)
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            flash("Username already exists, please try again", category="error")
            return redirect(url_for('NewAccount'))

   
    return redirect(url_for('login'))


# sends user to login page 
@app .route('/login')
def login():
    return render_template('Login.html')

# on POST checks users details and compares them with database, redirects user to welcome page to create a new task

@app.route('/auth', methods=['GET', 'POST'])
def authenticate():
    username1 = None
    password1 = None
    if request.method=='POST':
        username1=request.form['input1']
        password1=request.form['input2']

    returning_user = User.query.filter_by(username=username1).first()
    
    
    if returning_user:
        try:
            ph.verify(returning_user.Hashed_password, password1)
            
        except VerifyMismatchError:

            return redirect(url_for('login'))
        session['username'] = returning_user.username
        session['id'] = returning_user.id
        return redirect(url_for('welcome'))

    else:
        return redirect(url_for('login'))
    

@app.route('/welcome')
def welcome():
    
    



    if 'username' in session:
        username = session['username']
        return render_template('tasks.html', username=username)
    else:
        return "Welcome"



# on submit stores users task into database and returns a page of the list of tasks  
@app.route('/Create', methods = ['POST', 'GET'])
def Create():
    current_username = session['username']
    current_user = User.query.filter_by(username=current_username).first()

    if 'username' in session:
        if request.method == 'POST':
            task_name = request.form['task_name']
           
            due_date = (request.form['due-date'])
            userid = current_user.id
            #session['id'] = userid
            session['task'] = task_name
            print(f"the current users id is {userid}")
            
            if due_date:
                due_date = datetime.fromisoformat(due_date)
                session['due_date'] = due_date
            else:
                due_date = None

                
            

            new_task = Tasks(task_name=task_name, due_date=due_date, user_id=userid)
            db.session.add(new_task)
            db.session.commit()

    return redirect(url_for('welcome'))

def isCurrent_OrNextDay(date):
    current_day = datetime.now()
    string_currentday = current_day.strftime("%B %d, %Y")
    next_day = current_day + timedelta(days=1)
    string_nextday = next_day.strftime("%B %d, %Y")
    if date == string_currentday:
        formatted_duedate = "TODAY"
    elif date == string_nextday:
        formatted_duedate = "TOMORROW"
    else:
        formatted_duedate = date 
    return formatted_duedate
        



#presents user with active tasks

@app.route('/TaskList')

def Task_list():
   
    #print(current_id)
    #current_day = datetime.now()
    #next_day = current_day + timedelta(days=1)
    #formated_nextday = next_day.strftime("%B %d, %Y")
    

    
    task_dict = {}
    taskname = None
    new_date = None
    date = None

    
    
    if 'username' in session:
        current_id = session['id']
        print(current_id)
        current_day = datetime.now()
        day = current_day.strftime("%B %d, %Y")
       
        next_day = current_day + timedelta(days=1)
        
    
        
        tasks = Tasks.query.filter_by(user_id=current_id).all()

        
       
        for task in tasks:
            

            id = task.id
            
            taskname = task.task_name
            date = task.due_date.strftime("%B %d, %Y")
            if is_PastDue(task.due_date) == True:
                db.session.delete(task)
                db.session.commit()
                

            
            
            
            time_duedate = task.due_date.strftime("%I:%M %p")
            formated_duedate = task.due_date.strftime("%B %d, %Y at %I:%M %p")
            new_date = f"{isCurrent_OrNextDay(date)} at {time_duedate}"
           

            

            task_dict[id] = {'taskname': taskname, 'due_date': new_date}

                

            

          
                
    return render_template("tasks_list.html", task_dict=task_dict, tasklist = tasks, task_name=taskname, current_date=day)
@app.route('/completed', methods=['GET', 'POST'])
def completed():
    task_id = request.form['taskid']

    user_tasks = Tasks.query.filter_by(id=task_id).first()
    
    if user_tasks:
        user_tasks.completed = 1
        
        db.session.delete(user_tasks)
        db.session.commit()
        return redirect(url_for('Task_list'))
    
def is_PastDue(date):
    current_day = datetime.now()
    string_currentday = current_day.strftime("%B %d, %Y")
    if date < current_day:
        return True
    else:
        return False
    


    




    


        
    



        


    






if (__name__) == '__main__':
    app.run(debug=True, port=5001)



