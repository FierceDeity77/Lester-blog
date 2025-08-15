from flask import Blueprint, abort, render_template, redirect, url_for, flash, request
from datetime import date
from sqlalchemy import desc
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, RecoveryForm, ResetPasswordForm
from notif import Notification
from flask_login import login_user, current_user, logout_user
from models import BlogPost, User, Comment, db

views = Blueprint('views', __name__)


# Admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 4:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# Register new users into the User database
@views.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!", "danger")
            return redirect(url_for('views.login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("views.get_all_posts"))
    return render_template("register.html", form=form, current_user=current_user)


@views.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.", "danger")
            return redirect(url_for('views.login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.', "danger")
            return redirect(url_for('views.login'))
        else:
            login_user(user)
            return redirect(url_for('views.get_all_posts'))

    return render_template("login.html", form=form, current_user=current_user)


@views.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('views.get_all_posts'))


@views.route('/')
def get_all_posts():
    result = db.session.execute(db.select(BlogPost).order_by(desc(BlogPost.id)).limit(3))
    posts = result.scalars().all()
    return render_template("index.html", all_posts=posts, current_user=current_user)


@views.route('/blog-archive')
def blog_archive():
    result = db.session.execute(db.select(BlogPost).order_by(desc(BlogPost.id)))
    posts = result.scalars().all()
    return render_template("all_posts.html", all_posts=posts, current_user=current_user)


# View post
@views.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = db.get_or_404(BlogPost, post_id)
    # Add the CommentForm to the route
    comment_form = CommentForm()
    # Only allow logged-in users to comment on posts
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.", "danger")
            return redirect(url_for("views.login"))

        new_comment = Comment(
            text=comment_form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
    return render_template("post.html", post=requested_post,
                           current_user=current_user, form=comment_form)


@views.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("views.get_all_posts"))
    return render_template("make-post.html", form=form, current_user=current_user)


@views.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("views.show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True, current_user=current_user)


@views.route("/delete/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('views.get_all_posts'))


@views.route("/delete-comment/<int:comment_id>/<int:post_id>")
def delete_comment(comment_id, post_id):
    comment_to_delete = db.get_or_404(Comment, comment_id)
    db.session.delete(comment_to_delete)
    db.session.commit()
    return redirect(url_for('views.show_post', post_id=post_id))  # post id is the id of the blogpost


@views.route("/recovery", methods=["GET", "POST"])
def account_recovery():
    recovery_form = RecoveryForm()
    if recovery_form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == recovery_form.email.data))
        user = result.scalar()

        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.", "danger")
            return redirect(url_for('views.account_recovery'))
        else:
            token = user.get_reset_token()
            link = url_for('views.reset_password', token=token, _external=True)

            subject = 'Reset Your Password'
            frm = 'Hi!'
            to = user.email
            msg = (f"Thanks for checking out my blog! I really appreciate your support.  "
                   f"Hope you enjoyed what you read! \n\nclick the link to change your password {link}")

            notif = Notification(subject, frm, to, msg)
            notif.send_email()

            flash('Password reset email sent. Check your inbox.', 'success')
    return render_template("forgot.html", current_user=current_user, form=recovery_form)


@views.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset_password_form = ResetPasswordForm()
    user = User.verify_reset_token(token)

    # if request.method == 'POST':
    if reset_password_form.validate_on_submit():
        password = reset_password_form.password.data
        confirm_password = reset_password_form.confirm_password.data

        if not user:
            flash('That is an invalid or expired token.', 'danger')
            return redirect(url_for('account_recovery'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(request.url)

        # 🔐 Hash the password before saving
        hashed_pw = generate_password_hash(password)

        user.password = hashed_pw
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('views.login'))

    return render_template('reset.html', form=reset_password_form)


@views.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@views.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form  # gets data from html forms

        name = data["name"]  # data from html form assign to variables
        email = data["email"]
        phone = data["phone"]
        message = data["message"]

        send_notification = Notification(name, email, phone, message)  # creates object from Notification class
        send_notification.contact_email()
        flash('Your Message Has Been Sent Successfully!', 'success')
        return redirect(url_for('views.contact'))
    return render_template("contact.html")
