from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float, desc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests


class Base(DeclarativeBase):
    pass


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

URL = "https://api.themoviedb.org/3/search/movie"
HEADERS = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjNTE0Nzg0M2ExOTI5MjUyYzMwZDFhYjZhM2VhZWViNSIsInN1YiI6IjY1YzMyNzA2OGMwYTQ4MDE4NDg1ZjRlYiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.FvUVzDbUH_5_7gYhXcg9gA-MP8iGVdQPE0m7ElTUMB8"
}


class RateMovieForm(FlaskForm):
    rating = FloatField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField('Done')


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField('Add Movie')


# CREATE DB
db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movie-ranking.db"
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[str] = mapped_column(String(70), nullable=False)
    ranking: Mapped[str] = mapped_column(String(70), nullable=False)
    review: Mapped[str] = mapped_column(String(70), nullable=False)
    img_url: Mapped[str] = mapped_column(String(70), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()

    return render_template("index.html", all_movies=all_movies)


@app.route("/imaginary")
def add_movie():
    api_movie_id = request.args.get('id')
    the_url = f"https://api.themoviedb.org/3/movie/{api_movie_id}"
    response = requests.get(the_url, headers=HEADERS)
    data = response.json()
    new_movie = Movie(
        title=data['original_title'],
        year=data['release_date'][:4],
        description=data['overview'],
        rating="None",
        ranking="None",
        review="None",
        img_url=f"https://image.tmdb.org/t/p/w500/{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()

    sql_movie_id = new_movie.id
    return redirect(url_for('edit', id=sql_movie_id))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get('id')
    if form.validate_on_submit():
        movie_to_update = db.get_or_404(Movie, movie_id)
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    movie_selected = db.get_or_404(Movie, movie_id)
    return render_template("edit.html", movie=movie_selected, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        params = {
            "query": movie_title
        }
        response = requests.get(URL, params=params, headers=HEADERS)
        data = response.json()
        result = data['results']
        return render_template("select.html", movies=result)

    return render_template("add.html", form=form)


if __name__ == '__main__':
    app.run(debug=True, port=5002)
