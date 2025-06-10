import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SelectField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid

# PyMySQL을 MySQLdb로 사용하도록 설정
pymysql.install_as_MySQLdb()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# 데이터베이스 설정 - 환경 변수 우선 사용
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # 로컬 개발용 설정
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/urbanfarm_db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 업로드 폴더 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static/uploads/posts', exist_ok=True)
os.makedirs('static/uploads/journals', exist_ok=True)
os.makedirs('static/uploads/shares', exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 데이터베이스 모델
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', lazy=True)
    journals = db.relationship('Journal', backref='author', lazy=True)
    shares = db.relationship('Share', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(100))
    
    journals = db.relationship('Journal', backref='crop', lazy=True)
    shares = db.relationship('Share', backref='crop', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0)
    likes = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_type = db.Column(db.String(50), default='free')  # free, expert
    
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String(200))
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)

class Share(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.String(100), nullable=False)
    share_method = db.Column(db.String(100), nullable=False)  # direct, delivery
    location = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200))
    is_completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 폼 클래스
class LoginForm(FlaskForm):
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('사용자명', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('비밀번호 확인', validators=[DataRequired(), EqualTo('password')])

class PostForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('내용', validators=[DataRequired()])

class JournalForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('내용', validators=[DataRequired()])
    crop_id = SelectField('작물', coerce=int, validators=[DataRequired()])
    start_date = StringField('재배 시작일', validators=[DataRequired()])
    image = FileField('사진')
    is_public = BooleanField('공개', default=True)

class ShareForm(FlaskForm):
    title = StringField('제목', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('설명', validators=[DataRequired()])
    crop_id = SelectField('작물', coerce=int, validators=[DataRequired()])
    quantity = StringField('수량', validators=[DataRequired()])
    share_method = SelectField('나눔 방식', choices=[('direct', '직거래'), ('delivery', '택배')], validators=[DataRequired()])
    location = StringField('희망 장소', validators=[DataRequired()])
    image = FileField('사진')

# 라우트
@app.route('/')
def index():
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(3).all()
    recent_journals = Journal.query.filter_by(is_public=True).order_by(Journal.created_at.desc()).limit(3).all()
    recent_shares = Share.query.filter_by(is_completed=False).order_by(Share.created_at.desc()).limit(3).all()
    
    return render_template('index.html', 
                         recent_posts=recent_posts,
                         recent_journals=recent_journals,
                         recent_shares=recent_shares)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('이메일 또는 비밀번호가 올바르지 않습니다.')
    return render_template('auth/login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('이미 등록된 이메일입니다.')
            return render_template('auth/register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('회원가입이 완료되었습니다.')
        return redirect(url_for('login'))
    return render_template('auth/register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/community')
def community():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Post.query.filter_by(post_type='free')
    if search:
        query = query.filter(Post.title.contains(search) | Post.content.contains(search))
    
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    return render_template('community/index.html', posts=posts, search=search)

@app.route('/community/post/<int:id>')
def post_detail(id):
    post = Post.query.get_or_404(id)
    post.views += 1
    db.session.commit()
    return render_template('community/post_detail.html', post=post)

@app.route('/community/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            user_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        flash('게시글이 작성되었습니다.')
        return redirect(url_for('community'))
    return render_template('community/create_post.html', form=form)

# HTMX API 엔드포인트
@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')
    
    if not content or not content.strip():
        return '', 400
    
    comment = Comment(
        content=content.strip(),
        user_id=current_user.id,
        post_id=post_id
    )
    db.session.add(comment)
    db.session.commit()
    
    # 새 댓글 HTML 반환
    return f'''
    <div class="px-6 py-4" x-data="{{ editing: false, content: '{content.strip()}' }}">
        <div class="flex space-x-3">
            <div class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                <span class="text-gray-600 text-sm font-medium">{current_user.username[0].upper()}</span>
            </div>
            <div class="flex-1">
                <div class="flex items-center space-x-2 mb-1">
                    <span class="font-medium text-gray-900">{current_user.username}</span>
                    <span class="text-sm text-gray-500">방금 전</span>
                </div>
                <div x-show="!editing">
                    <p class="text-gray-700">{content.replace(chr(10), '<br>')}</p>
                </div>
                <div x-show="editing">
                    <form hx-put="/api/comments/{comment.id}"
                          hx-target="closest div.px-6"
                          hx-swap="outerHTML"
                          @htmx:after-request="editing = false">
                        <textarea x-model="content" 
                                name="content"
                                rows="3"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-urban-green focus:border-transparent resize-none"
                                required></textarea>
                        <div class="mt-2 flex justify-end space-x-2">
                            <button type="button" @click="editing = false"
                                    class="text-gray-500 hover:text-gray-700 px-3 py-1 text-sm">
                                취소
                            </button>
                            <button type="submit"
                                    class="bg-urban-green text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition-colors">
                                수정
                            </button>
                        </div>
                    </form>
                </div>
                <div class="mt-2 flex items-center space-x-2" x-show="!editing">
                    <button @click="editing = true" class="text-xs text-gray-500 hover:text-urban-green">수정</button>
                    <button class="text-xs text-gray-500 hover:text-red-600"
                            hx-delete="/api/comments/{comment.id}"
                            hx-confirm="정말 삭제하시겠습니까?"
                            hx-target="closest div.px-6">
                        삭제
                    </button>
                </div>
            </div>
        </div>
    </div>
    '''

@app.route('/api/comments/<int:comment_id>', methods=['PUT'])
@login_required
def update_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id:
        return '', 403
    
    content = request.form.get('content')
    if not content or not content.strip():
        return '', 400
    
    comment.content = content.strip()
    db.session.commit()
    
    # 수정된 댓글 HTML 반환
    return f'''
    <div class="px-6 py-4" x-data="{{ editing: false, content: '{content.strip()}' }}">
        <div class="flex space-x-3">
            <div class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0">
                <span class="text-gray-600 text-sm font-medium">{comment.author.username[0].upper()}</span>
            </div>
            <div class="flex-1">
                <div class="flex items-center space-x-2 mb-1">
                    <span class="font-medium text-gray-900">{comment.author.username}</span>
                    <span class="text-sm text-gray-500">{comment.created_at.strftime('%m/%d %H:%M')} (수정됨)</span>
                </div>
                <div x-show="!editing">
                    <p class="text-gray-700">{content.replace(chr(10), '<br>')}</p>
                </div>
                <div x-show="editing">
                    <form hx-put="/api/comments/{comment.id}"
                          hx-target="closest div.px-6"
                          hx-swap="outerHTML"
                          @htmx:after-request="editing = false">
                        <textarea x-model="content" 
                                name="content"
                                rows="3"
                                class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-urban-green focus:border-transparent resize-none"
                                required></textarea>
                        <div class="mt-2 flex justify-end space-x-2">
                            <button type="button" @click="editing = false"
                                    class="text-gray-500 hover:text-gray-700 px-3 py-1 text-sm">
                                취소
                            </button>
                            <button type="submit"
                                    class="bg-urban-green text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition-colors">
                                수정
                            </button>
                        </div>
                    </form>
                </div>
                <div class="mt-2 flex items-center space-x-2" x-show="!editing">
                    <button @click="editing = true" class="text-xs text-gray-500 hover:text-urban-green">수정</button>
                    <button class="text-xs text-gray-500 hover:text-red-600"
                            hx-delete="/api/comments/{comment.id}"
                            hx-confirm="정말 삭제하시겠습니까?"
                            hx-target="closest div.px-6">
                        삭제
                    </button>
                </div>
            </div>
        </div>
    </div>
    '''

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    
    if comment.user_id != current_user.id:
        return '', 403
    
    db.session.delete(comment)
    db.session.commit()
    
    return '', 200

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 간단한 좋아요 토글 (실제로는 별도 테이블로 관리하는 것이 좋음)
    post.likes += 1
    db.session.commit()
    
    return f'''
    <button class="flex items-center space-x-2 text-red-500 transition-colors"
            hx-post="/api/posts/{post_id}/like"
            hx-swap="outerHTML">
        <i class="fas fa-heart"></i>
        <span>좋아요 {post.likes}</span>
    </button>
    '''

# 재배 일지 라우트
@app.route('/journals')
def journals():
    page = request.args.get('page', 1, type=int)
    journals = Journal.query.filter_by(is_public=True).order_by(Journal.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('journals/index.html', journals=journals)

@app.route('/journals/create', methods=['GET', 'POST'])
@login_required
def create_journal():
    form = JournalForm()
    form.crop_id.choices = [(c.id, f"{c.icon} {c.name}") for c in Crop.query.all()]
    
    if form.validate_on_submit():
        journal = Journal(
            title=form.title.data,
            content=form.content.data,
            start_date=datetime.strptime(form.start_date.data, '%Y-%m-%d').date(),
            crop_id=form.crop_id.data,
            is_public=form.is_public.data,
            user_id=current_user.id
        )
        
        # 이미지 업로드 처리 (향후 구현)
        if form.image.data:
            # 파일 업로드 로직
            pass
        
        db.session.add(journal)
        db.session.commit()
        flash('재배 일지가 작성되었습니다.')
        return redirect(url_for('journals'))
    
    return render_template('journals/create.html', form=form)

# 나눔 장터 라우트
@app.route('/shares')
def shares():
    page = request.args.get('page', 1, type=int)
    shares = Share.query.filter_by(is_completed=False).order_by(Share.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False)
    return render_template('shares/index.html', shares=shares)

@app.route('/shares/create', methods=['GET', 'POST'])
@login_required
def create_share():
    form = ShareForm()
    form.crop_id.choices = [(c.id, f"{c.icon} {c.name}") for c in Crop.query.all()]
    
    if form.validate_on_submit():
        share = Share(
            title=form.title.data,
            description=form.description.data,
            crop_id=form.crop_id.data,
            quantity=form.quantity.data,
            share_method=form.share_method.data,
            location=form.location.data,
            user_id=current_user.id
        )
        
        # 이미지 업로드 처리 (향후 구현)
        if form.image.data:
            # 파일 업로드 로직
            pass
        
        db.session.add(share)
        db.session.commit()
        flash('나눔 물품이 등록되었습니다.')
        return redirect(url_for('shares'))
    
    return render_template('shares/create.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # 기본 작물 데이터 추가
        if not Crop.query.first():
            crops = [
                Crop(name='토마토', icon='🍅'),
                Crop(name='상추', icon='🥬'),
                Crop(name='고추', icon='🌶️'),
                Crop(name='오이', icon='🥒'),
                Crop(name='당근', icon='🥕'),
                Crop(name='무', icon='🥬'),
                Crop(name='배추', icon='🥬'),
                Crop(name='파', icon='🧅')
            ]
            for crop in crops:
                db.session.add(crop)
            db.session.commit()
    
    # 프로덕션 환경에서는 host와 port 설정
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug) 