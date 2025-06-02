# app.py
import os
import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_login import login_required, current_user, LoginManager
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from engine.server import bp as engine_bp
from engine.server import init_game
from db import User, Session  # импортируем модель и сессию из вашего db.py


# === Настройка ===
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'engine', 'bots')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'py'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'секретка'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# === Модели ===
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    mmr           = db.Column(db.Integer, default=1000)
    created       = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Bot(db.Model):
    __tablename__ = 'bots'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename    = db.Column(db.String(256), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    user = db.relationship('User', backref=db.backref('bots', lazy='dynamic'))

class Match(db.Model):
    __tablename__ = 'matches'
    id          = db.Column(db.Integer, primary_key=True)
    player1_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player2_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    winner_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp   = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# создаём таблицы при старте
with app.app_context():
    db.create_all()

# === Хелперы ===
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# === Маршруты ===

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        name = request.form['username']
        pwd  = request.form['password']
        user = User.query.filter_by(username=name).first()
        if user:
            if not check_password_hash(user.password_hash, pwd):
                flash('Неверный пароль', 'danger')
                return redirect(url_for('login'))
        else:
            # регистрируем нового
            user = User(username=name,
                        password_hash=generate_password_hash(pwd))
            db.session.add(user)
            db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('profile'))

    # GET: подтягиваем топ-10 по MMR
    top_users = User.query \
                    .order_by(User.mmr.desc()) \
                    .limit(10) \
                    .all()
    return render_template('login.html', users=top_users)


@app.route('/profile')
def profile():
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('login'))
    user = User.query.get(uid)
    matches = []
    bots = Bot.query.filter_by(user_id=uid).order_by(Bot.uploaded_at.desc()).all()
    # Статистика матчей
    total = Match.query.filter(
        (Match.player1_id==uid) | (Match.player2_id==uid)
    ).count()
    wins  = Match.query.filter_by(winner_id=uid).count()
    winrate = f"{wins/total*100:.1f}%" if total>0 else "—"

    # История игр
    history = Match.query.filter(
        (Match.player1_id==uid) | (Match.player2_id==uid)
    ).order_by(Match.timestamp.desc()).all()

    return render_template('profile.html',
                           user=user,
                           total_matches=total,
                           winrate=winrate,
                           history=history,
                           bots = bots)


# ----------------------------------------------------------------------
#  LEADERBOARD  –  /leaderboard?page=N   (default page-size = 25)
# ----------------------------------------------------------------------
@app.route('/leaderboard')
def leaderboard():
    page      = request.args.get('page', default=1, type=int)
    per_page  = 25
    # paginate() is built-in to Flask-SQLAlchemy
    pagination = User.query.order_by(User.mmr.desc()) \
                           .paginate(page=page, per_page=per_page, error_out=False)
    return render_template(
        'leaderboard.html',
        users      = pagination.items,
        pagination = pagination
    )

@app.route('/battle', methods=['POST'])
def battle():
    # сбрасываем игровое состояние
    init_game()
    # перенаправляем на страницу визуализации с параметром autostart
    return redirect(url_for('game') + '?autostart=1')


@app.route('/game')
def game():
    return render_template('game.html')


@app.route('/upload_bot', methods=['POST'])
def upload_bot():
    if 'botfile' not in request.files:
        flash('Файл не выбран', 'warning')
        return redirect(url_for('profile'))

    file = request.files['botfile']
    if file.filename == '':
        flash('Файл не выбран', 'warning')
        return redirect(url_for('profile'))

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)
        new_bot = Bot(user_id=session['user_id'], filename=filename)
        db.session.add(new_bot)
        db.session.commit()
        flash(f'Bot "{filename}" uploaded successfully.', 'success')
    else:
        flash('Разрешены только .py файлы', 'danger')

    return redirect(url_for('profile'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

print(">> Registering test_battle route")
@app.route('/test_battle')
def test_battle():
    """
    Простой тест: запускаем битву между green_bot и red_bot.
    """
    # Загружаем оба бота в движок
    reload_bots([
        {"name": "green_bot", "path": "engine/bots/green_bot.py"},
        {"name": "red_bot",   "path": "engine/bots/red_bot.py"},
    ])
    # Сбрасываем состояние игры
    reset_game()
    # Переходим на страницу визуализации
    return redirect(url_for('game'))

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    return session.query(User).get(int(user_id))

app.register_blueprint(engine_bp, url_prefix='/api')


if __name__ == '__main__':
    app.run(debug=True)
