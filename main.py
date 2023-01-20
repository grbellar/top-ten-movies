import flask
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, SelectField
from wtforms.validators import DataRequired, NumberRange, ValidationError
import requests

# TODO: nice-to-haves-- 1. add additional users. i.e. could choose 'Grant' or 'Sabrina' collection.


# INIT APP and DB
db = SQLAlchemy()
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-database.db"
db.init_app(app)
Bootstrap(app)


# CREATE MOVIE TABLE IN DB
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String, unique=False)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False)
    description = db.Column(db.String, unique=False)
    rating = db.Column(db.Float, unique=False)
    ranking = db.Column(db.Integer, unique=False)
    review = db.Column(db.String, unique=False)
    img_url = db.Column(db.String, unique=False)


with app.app_context():
    db.create_all()


# CREATE forms
class EditForm(FlaskForm):
    rating = FloatField(label='Your rating out of 10', validators=[DataRequired(), NumberRange(min=0, max=10)])
    review = StringField(label='Your review:', validators=[DataRequired()])
    user = SelectField(label='Your name',
                       validators=[DataRequired()],
                       choices=['Amy', 'Chris', 'Grant', 'Luke', 'Sabrina'],
                       default=2)
    submit = SubmitField(label='Done')


class AddForm(FlaskForm):
    title = StringField(label='Type your movie title', validators=[DataRequired()])
    submit = SubmitField(label='Search')


@app.route("/")
def welcome():
    all_movies = db.session.query(Movie).order_by(Movie.rating.desc())
    user_list = []
    for movie in all_movies:
        if movie.user not in user_list:  # no duplicate users
            user_list.append(movie.user)
    return render_template('welcome.html', user_list=user_list)


@app.route("/display")
def display():
    user = flask.request.args.get('user')
    all_movies = db.session.query(Movie).filter_by(user=user).order_by(Movie.rating.desc())
    count = 1
    for movie in all_movies:
        movie.ranking = count
        db.session.commit()
        count += 1
    return render_template("display.html", movies=all_movies, user=user)


@app.route("/add", methods=['POST', 'GET'])
def add():
    form_add = AddForm()
    if flask.request.method == 'POST':
        search_string = form_add.title.data
        movie_request = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key'
                                     f'=24245f31c7ac222b4c2c6326fab7e901&query={search_string}')
        response_data = movie_request.json()
        results = response_data['results']
        return render_template('select.html', all_results=results)
    return render_template("add.html", form=form_add)


@app.route('/find')
def find():
    movie_api_id = flask.request.args.get('movie_id')
    id_request = requests.get(
        f'https://api.themoviedb.org/3/movie/{movie_api_id}?api_key=24245f31c7ac222b4c2c6326fab7e901')
    results = id_request.json()
    title = results['original_title']
    year = results['release_date'].split('-')[0]  # grab the year only
    description = results['overview']
    img_url = f'https://image.tmdb.org/t/p/w500{results["poster_path"]}'
    # if movie is already in database, don't try to add another one
    exists = db.session.query(db.exists().where(Movie.title == title)).scalar()
    if exists:
        # print(exists)
        return redirect(url_for('add'))  # for some reason passing exists to add.html does not work, so right now there
        # there is no message displayed helping the user.
    else:
        new_movie = Movie(title=title, year=year, description=description, img_url=img_url)
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', database_id=new_movie.id))


@app.route("/edit", methods=['POST', 'GET'])
def edit():
    database_id = flask.request.args.get('database_id')
    form_edit = EditForm()
    if flask.request.method == 'POST':
        movie_to_update = Movie.query.get(database_id)
        movie_to_update.rating = form_edit.rating.data
        movie_to_update.review = form_edit.review.data
        movie_to_update.user = form_edit.user.data
        db.session.commit()
        return redirect(url_for('display', user=form_edit.user.data))
    return render_template("edit.html", form=form_edit)


@app.route("/delete")
def delete():
    database_id = flask.request.args.get('database_id')
    movie_to_delete = Movie.query.get(database_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('display', user=movie_to_delete.user))


if __name__ == '__main__':
    app.run(debug=True)
