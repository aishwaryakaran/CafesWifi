import random
from flask import Flask, jsonify, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import LoginForm, RegisterForm, AddCafeForm

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")

ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))

##Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    cafes = db.session.query(Cafe).all()
    return render_template("index.html", all_cafes=jsonify(cafes=[cafe.to_dict() for cafe in cafes]),
                           current_user=current_user)


@app.route("/random")
def get_random_cafe():
  cafes=db.session.query(Cafe).all()
  random_cafe=random.choice(cafes)
  return jsonify(cafe=random_cafe.to_dict())
  # return jsonify(cafe={"id" : random_cafe.id,  "name" : random_cafe.name,
  # "map_url" : random_cafe.map_url,  "img_url" : random_cafe.img_url,
  # "location" : random_cafe.location,  "seats" : random_cafe.seats,
  # "has_toilet" : random_cafe.has_toilet,  "has_wifi" : random_cafe.has_wifi,
  # "has_sockets" : random_cafe.has_sockets,  "can_take_calls": random_cafe.can_take_calls,
  # "coffee_price" : random_cafe.coffee_price})

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            print(User.query.filter_by(email=form.email.data).first())
            #User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

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
        login_user(new_user)
        return redirect(url_for("home"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/cafe/<int:cafe_id>", methods=["GET", "POST"])
def show_cafe(cafe_id):
    requested_cafe = Cafe.query.get(cafe_id)

    return render_template("cafe.html", post=requested_cafe, current_user=current_user)


# @app.route("/search")
# def search_cafe():
#     query_location = request.args.get("loc")
#     cafe = db.session.query(Cafe).filter_by(location=query_location).first()
#     print(cafe)
#     if cafe:
#         return jsonify(cafe=cafe.to_dict())
#     else:
#         return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."})


@app.route("/add", methods=["POST","GET"])
def post_new_cafe():
    form = AddCafeForm()
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )
    db.session.add(new_cafe)
    db.session.commit()
    # return jsonify(response={"success": "Successfully added the new cafe."})
    # return redirect(url_for("home"))
    return render_template("make-cafe.html", form=form, current_user=current_user)

def edit_cafe(cafe_id):
    cafe = Cafe.query.get(cafe_id)
    edit_form = AddCafeForm(
        name = cafe.name,
    map_url = cafe.map_url,
    img_url = cafe.img_url,
    location = cafe.location,
    has_sockets = cafe.has_sockets,
    has_toilet = cafe.has_toilet,
    has_wifi = cafe.has_wifi,
    can_take_calls = cafe.can_take_calls,
    seats = cafe.seats,
    coffee_price = cafe.coffee_price,
    )
    if edit_form.validate_on_submit():
        cafe.name = edit_form.name.data,
        cafe.map_url = edit_form.map_url.data,
        cafe.img_url = edit_form.img_url.data,
        cafe.location = edit_form.location.data,
        cafe.has_sockets = edit_form.has_sockets.data,
        cafe.has_toilet = edit_form.has_toilet.data,
        cafe.has_wifi = edit_form.has_wifi.data,
        cafe.can_take_calls = edit_form.can_take_calls.data,
        cafe.seats = edit_form.seats.data,
        cafe.coffee_price = edit_form.coffee_price.data,
        db.session.commit()
        return redirect(url_for("show_cafe", cafe_id=cafe.id))

    return render_template("make-cafe.html", form=edit_form, is_edit=True, current_user=current_user)

# @app.route("/update-price/<int:cafe_id>", methods=["GET","PATCH"])
# def patch_new_price(cafe_id):
#     new_price = request.args.get("new_price")
#     cafe = db.session.query(Cafe).get(cafe_id)
#     if cafe:
#         cafe.coffee_price = new_price
#         db.session.commit()
#         return jsonify(response={"success": "Successfully updated the price."}), 200
#     else:
#         return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404

@app.route("/report-closed/<int:cafe_id>", methods=["GET","DELETE"])
def delete_cafe(cafe_id):
    if current_user.is_authenticated:
        cafe = db.session.query(Cafe).get(cafe_id)
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200
        else:
            return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    else:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you are logged in."}), 403


if __name__ == '__main__':
    app.run(debug=True)
