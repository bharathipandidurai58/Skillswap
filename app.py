from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret"


# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Users Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
    )
    """)

    # Skills Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS skills(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    skill TEXT
    )
    """)

    # Requests Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS requests(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    sender_skill TEXT,
    receiver_skill TEXT,
    status TEXT
    )
    """)

    # Messages Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


init_db()


# ================= INDEX =================

@app.route('/')
def index():
    return render_template('index.html')


# ================= REGISTER =================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, password)
        )

        conn.commit()
        return redirect('/login')

    return render_template('register.html')


# ================= LOGIN =================

@app.route('/login', methods=['GET', 'POST'])
def login():

    error = None

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = c.fetchone()

        if user:
            session['username'] = username
            return redirect('/dashboard')
        else:
            error = "Invalid Username or Password"

    return render_template('login.html', error=error)


# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= DASHBOARD =================

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Add Skill
    if request.method == 'POST':
        skill = request.form['skill']

        c.execute(
            "INSERT INTO skills(username,skill) VALUES(?,?)",
            (session['username'], skill)
        )

        conn.commit()

    # My Skills
    c.execute(
        "SELECT * FROM skills WHERE username=?",
        (session['username'],)
    )
    my_skills = c.fetchall()

    # Available Skills
    c.execute(
        "SELECT * FROM skills WHERE username != ?",
        (session['username'],)
    )
    skills = c.fetchall()

    # Incoming Requests
    c.execute("""
    SELECT * FROM requests
    WHERE receiver=?
    """, (session['username'],))

    incoming = c.fetchall()

    # Sent Requests
    c.execute("""
    SELECT * FROM requests
    WHERE sender=?
    """, (session['username'],))

    sent = c.fetchall()

    # Accepted Connections
    c.execute("""
    SELECT * FROM requests
    WHERE (sender=? OR receiver=?)
    AND status='Accepted'
    """, (session['username'], session['username']))

    accepted = c.fetchall()

    return render_template(
        'dashboard.html',
        my_skills=my_skills,
        skills=skills,
        incoming=incoming,
        sent=sent,
        accepted=accepted
    )


# ================= DELETE SKILL =================

@app.route('/delete_skill/<int:id>')
def delete_skill(id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("DELETE FROM skills WHERE id=?", (id,))
    conn.commit()

    return redirect('/dashboard')


# ================= SEND REQUEST =================

@app.route('/request/<username>/<skill>')
def request_user(username, skill):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Sender Skill
    c.execute(
        "SELECT skill FROM skills WHERE username=?",
        (session['username'],)
    )

    sender_skill = c.fetchone()[0]

    c.execute("""
    INSERT INTO requests(sender,receiver,sender_skill,receiver_skill,status)
    VALUES(?,?,?,?,?)
    """, (
        session['username'],
        username,
        sender_skill,
        skill,
        "Pending"
    ))

    conn.commit()

    return redirect('/dashboard')


# ================= ACCEPT =================

@app.route('/accept/<int:id>')
def accept(id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "UPDATE requests SET status='Accepted' WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect('/dashboard')


# ================= REJECT =================

@app.route('/reject/<int:id>')
def reject(id):

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute(
        "UPDATE requests SET status='Rejected' WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect('/dashboard')


# ================= CHAT =================

@app.route('/chat/<username>', methods=['GET', 'POST'])
def chat(username):

    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    if request.method == 'POST':

        message = request.form['message']

        c.execute("""
        INSERT INTO messages(sender,receiver,message)
        VALUES(?,?,?)
        """, (
            session['username'],
            username,
            message
        ))

        conn.commit()

    c.execute("""
    SELECT * FROM messages
    WHERE (sender=? AND receiver=?)
    OR (sender=? AND receiver=?)
    ORDER BY timestamp
    """, (
        session['username'],
        username,
        username,
        session['username']
    ))

    messages = c.fetchall()

    return render_template(
        'chat.html',
        messages=messages,
        user=username
    )


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)