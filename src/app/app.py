from flask import Flask, render_template, g, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db, connect_db
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
classActive = 'active'
classActives = {'classActivehome': classActive, 'classActivelogin': classActive,
               'classActiveregister': classActive, 'classActiveask': classActive,
               'classActiveanswer': classActive, 'classActiveunan': classActive,
               'classActiveuser': classActive}


def get_current_user():
    user_result = None

    if 'user' in session:
        db = get_db()
        user = session['user']
        db.execute('select * from users where name= %s', (user, ))
        user_result = db.fetchone()

    return user_result


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()
    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()


@app.route('/')
@app.route('/home')
def index():
    user = get_current_user()
    db = get_db()
    db.execute(
        'select questions.id, questions.question_text, askers.name as asker, experts.name as expert '
        'from questions join users as askers on questions.asked_by_id=askers.id '
        'join users as experts on questions.expert_id = experts.id '
        'where questions.answer_text is not null')
    questions = db.fetchall()

    return render_template('home.html', classActive=classActives, user=user, questions=questions)


@app.route('/login', methods=['POST', 'GET'])
def login():
    current_user = get_current_user()
    errors = {'error_password': 'None', 'error_email': 'None'}
    if request.method == 'POST':
        email = request.form['useremail']
        password = request.form['userpassword']
        db = get_db()
        db.execute('select * from users where email = %s', (email, ))
        user = db.fetchone()

        if user:
            if check_password_hash(user['password'], password):
                session['user'] = user['name']
                return redirect(url_for('index'))
            else:
                errors['error_password'] = 'password do not match'
        else:
            errors['error_email'] = 'Email dont exist'

    return render_template('login.html', errors=errors, classActive=classActives, user=current_user)


@app.route('/register', methods=['POST', 'GET'])
def register():
    current_user = get_current_user()
    user_created = None
    error = {'name': 'None', 'email': 'None'}
    if request.method == 'POST':
        db = get_db()
        db.execute('select name, email from users where name = %s or email= %s group by name,email', (request.form['username'], request.form['useremail'], ))
        user = db.fetchone()

        if user:
            if user['name'] == request.form['username']:
                error['name'] = 'this name already exist'
                user_created = False
            elif user['email'] == request.form['useremail']:
                error['email'] = 'this email already exist'
                user_created = False
        else:
            hashed_password = generate_password_hash(request.form['userpassword'], method='sha256')
            db.execute('insert into users (name,email,password,expert,admin) values (%s,%s,%s,%s,%s)',
                       (request.form['username'], request.form['useremail'], hashed_password, False, False, ))
            user_created = True
            session['user'] = request.form['username']
            return redirect(url_for('index'))

    return render_template('register.html', error=error, user_created=user_created,
                           classActive=classActives, user=current_user)


@app.route('/askquestion', methods=['POST', 'GET'])
def ask():
    current_user = get_current_user()
    db = get_db()

    if not current_user:
        return redirect(url_for('login'))
    if current_user['expert'] or current_user['admin']:
        return redirect(url_for('index'))
    if request.method == 'POST':
        db.execute('insert into questions (question_text, asked_by_id,expert_id) values (%s,%s,%s)',
                   (request.form['question'], current_user['id'], request.form['expert'], ))
        return redirect(url_for('index'))

    db.execute('select * from users where expert = True')
    expert_result = db.fetchall()

    return render_template('ask.html', classActive=classActives, user=current_user, experts=expert_result)


@app.route('/answers/<question_id>', methods=['POST', 'GET'])
def answers(question_id):
    db = get_db()
    current_user = get_current_user()

    if not current_user:
        return redirect(url_for('login'))

    if not current_user['expert']:
        return redirect(url_for('index'))

    db.execute('select * from questions where id = %s', (question_id, ))
    questions_results = db.fetchone()
    if request.method == 'POST':
        db.execute('UPDATE questions set answer_text= %s where id= %s', (request.form['answer'], question_id, ))
        return redirect(url_for('unanswered'))

    return render_template('answer.html', classActive=classActives, user=current_user, question=questions_results)


@app.route('/unanswered')
def unanswered():
    db = get_db()
    current_user = get_current_user()

    if not current_user:
        return redirect(url_for('login'))

    if not current_user['expert']:
        return redirect(url_for('index'))

    db.execute('select questions.id, questions.question_text, users.name '
                              'from questions join users on questions.asked_by_id = users.id '
                              'where questions.expert_id = %s and questions.answer_text is null',
               (current_user['id'], ))
    questions = db.fetchall()

    return render_template('unanswered.html', questions=questions, user=current_user, classActive=classActives)


@app.route('/questions/<question_id>')
def questions(question_id):
    current_user = get_current_user()
    db = get_db()

    if not current_user:
        return redirect(url_for('login'))

    db.execute(
        'select questions.id, questions.question_text, questions.answer_text, '
        'askers.name as asker, experts.name as expert '
        'from questions join users as askers on questions.asked_by_id=askers.id '
        'join users as experts on questions.expert_id = experts.id '
        'where questions.id = %s', (question_id, ))
    question = db.fetchone()
    return render_template('question.html', question=question, user=current_user)


@app.route('/users')
def users_control():
    current_user = get_current_user()

    if not current_user:
        return redirect(url_for('login'))

    if not current_user['admin']:
        return redirect(url_for('index'))

    db = get_db()
    db.execute('select * from users')
    users_list = db.fetchall()

    return render_template('users.html', classActive=classActives, user=current_user, users=users_list)


@app.route('/promote/<user_id>')
def promote(user_id):
    db = get_db()
    current_user = get_current_user()

    if not current_user:
        return redirect(url_for('login'))
    if not current_user['admin']:
        redirect(url_for('index'))

    db.execute('update users set expert = True where id = %s', (user_id, ))

    return redirect(url_for('users_control'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))
