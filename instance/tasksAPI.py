from flask import Flask, jsonify, request, redirect, url_for
import sqlite3


app = Flask(__name__)





def db_connection():
    conn = None
    try:
        conn = sqlite3.connect('tasks.db')
    except sqlite3.error as e:
        print("Database not found")
    return conn

@app.route('/')
def reroute():
    return redirect(url_for('task_database'))

@app.route('/taskdatabase', methods=['GET'] )
def task_database():
    conn = db_connection()
    cursor = conn.cursor()
    userid = request.args.get('user_id')
    if userid:
        query = "SELECT task_name, due_date FROM Tasks WHERE user_id= ?"
        cursor.execute(query, (userid,))
    else:
        query = "SELECT * FROM Tasks"
        cursor.execute(query)
    
    Tasks = [
        dict(id=row[0], task_name=row[1], due_date=row[2], completed=row[3], user_id=row[4] )
        for row in cursor.fetchall()
    ]
    if Tasks:
        return jsonify(Tasks)
    else:
        return "No Task data found"

if __name__ == '__main__':
    app.run(debug=True)