from datetime import datetime

from flask import render_template, flash, redirect, request, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db, logging
from app.models import User, Enterprise, Value
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EnterpriseForm, EditEnterpriseForm


@app.before_request
def before_request():
    """Función que actualiza periodicamente el valor de última conexión del usuario"""
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    """Función que maneja la lógica de la inserción de empresas tanto en 'enterprises'
        como en 'values'enterprises', así como el despliegue de páginas y la paginación de las mismas

    :return: Redireccionamiento a página principal
    :rtype: None
    """
    
    return render_template(
        "index.html",
        title="Home",
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Función que direcciona a formulario que valida identidad del usuario

    :return: Redireccionamiento a página principal
    :rtype: None
    """
    if current_user.is_authenticated:
        return redirect(url_for("main", user=current_user))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Usuario y/o contraseña invàlidos")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main", user=user)
        return redirect(next_page)
    return render_template("login.html", title="Ingresar", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Función que permite direccionar a la página de registro de usuarios y
        manejar la lógica de las peticiones

    :return: redireccionamiento a página de registro
    :rtype: None
    """
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Felicitaciones. Te has registrado con èxito")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/user/<username>")
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user.html", user=user)


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    """Función que permite redireccionar a página de edición de perfiles de usuarios
        y manejar la lógica de las peticiones

    :return: redireccionamiento a página de edición de perfiles
    :rtype: None
    """
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Tus cambios han sido guardados")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Editar Perfil", form=form)


@app.route("/main", methods=["GET", "POST"])
@login_required
def main():
    return render_template("main.html", title="Página Principal")
