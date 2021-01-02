from flask import render_template, url_for, flash, redirect, request, jsonify, make_response, abort
from web_main import app, db, bcrypt, mail
from web_main.forms import RegistrationForm, LoginForm, UpdateAccountForm, InnateForm, ResetPasswordForm, RequestResetForm
from web_main.models import User, Item, Innate
from flask_login import login_user, current_user, logout_user, login_required
import jwt
import os
import secrets
from PIL import Image
import datetime
from functools import wraps
from flask_mail import Message



@app.route("/")
@app.route("/base")
def base():
    page = request.args.get('page', type=int)
    innates = Innate.query.paginate(page=page, per_page=2)
    
    return render_template('base.html', innates=innates)

@app.route("/about")
def about():
    return render_template('about.html', title='About')   

@app.route("/register", methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('base'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user =User(username=form.username.data, email= form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Your Account has been Created for {form.username.data}, you can now Login!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)  


@app.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('base'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user= User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember= form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('base'))
        else:
            flash('Login Unsuccessful. Check credentials!', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('base'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125,125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn



@app.route("/account",methods=['GET','POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your Account has been Updated!','success')
        redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file= url_for('static', filename='profile_pics/'+ current_user.image_file)
    return render_template('account.html', title='account', image_file=image_file, form=form)

@app.route("/my_innate/new",methods=['GET','POST'])
@login_required
def create_innate():
    form = InnateForm()
    if form.validate_on_submit():
        innate = Innate(title=form.title.data, innated=form.innate.data, innate_owner_id=current_user)
        db.session.add(innate)
        db.session.commit()
        flash('innate Saved!', 'success')
        return render_template('my_innate.html', title='innate')
    return render_template('create_innate.html', title='New innate', form=form, legend= 'New Innate')

@app.route("/innate/<int:innate_id>")
def innate(innate_id):
    innate = Innate.query.get_or_404(innate_id)
    return render_template('innate.html', title=innate.title, innate=innate)

@app.route("/innate/<int:innate_id>/update", methods=['GET','POST'])
@login_required
def update_innate(innate_id):
    innate = Innate.query.get_or_404(innate_id)
    if innate.innate_owner_id != current_user:
        abort(403)
    form = InnateForm()
    if form.validate_on_submit():
        innate.title = form.title.data
        innate.innated = form.innate.data
        db.session.commit()
        flash('Updated Innate!', 'success')
        return redirect(url_for('innate', innate_id=innate.id))
    elif request.method == 'GET':
        form.title.data = innate.title
        form.innate.data = innate.innated
    return render_template('create_innate.html', title='Update innate', form=form, legend= 'Update Innate')

@app.route("/innate/<int:innate_id>/delete", methods=['POST'])
@login_required
def delete_innate(innate_id):
    innate = Innate.query.get_or_404(innate_id)
    if innate.innate_owner_id != current_user:
        abort(403)
    db.session.delete(innate)
    db.session.commit()
    flash('Innate Deleted!', 'success')
    return redirect(url_for('base'))

@app.route("/user/<string:username>")
def user_innates(username):
    page = request.args.get('page', type=int)
    user = User.query.filter_by(username=username).first_or_404()
    innates = Innate.query.filter_by(innate_owner_id=user).paginate(page=page, per_page=2)
    return render_template('user_innate.html', innates=innates, user=user)

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(' Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f''' to Rest the password please visit the below link:
{url_for('reset_password', token=token, _external= True)}

If you did not make this request then please ignore this message
'''
    mail.send(msg)

@app.route("/reset_password",methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('base'))
    form= RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An E-mail has been sent with password reset. Please check your E-mail', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password Request', form=form)

@app.route("/reset_password/<token>",methods=['GET','POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('base'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That token is invalid or expired')
        return redirect(url_for('reset_request'))
    form= ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_pw
        db.session.commit()
        flash(f'Your Password has been Updated!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset Password', form=form)
    
