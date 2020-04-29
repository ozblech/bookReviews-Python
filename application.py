import os
from models import *
from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

API_KEY = 'BgL5W1j6rFhyjLFAr3PLPA'
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
	session["user"] = []
	return render_template("index.html")

@app.route("/api/<string:isbn>", methods=["GET"])
def book_api(isbn):
	# book = Book.query.get(isbn)
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	if book is None:
		return jsonify({"error":"Invalid ISBN"}),404

	#Fetch the reviews statistics
	# review_count = Review.query.filter_by(isbn=isbn).count()
	# reviews = book.reviews
	# sum = 0
	# for review in reviews:
	# 	sum+=review.rate
	# average_score = sum/review_count
	review_count = db.execute("SELECT COUNT(isbn) FROM reviews WHERE isbn = :isbn", { "isbn": isbn }).fetchone()
	average_score = db.execute("SELECT AVG(rate) FROM reviews WHERE isbn = :isbn", { "isbn": isbn }).fetchone()
	
	return jsonify({
		"title": book.title,
		"author":book.author,
		"isbn":isbn,
		"year":book.year,
		"review_count":review_count[0],
		"average_score":average_score[0]
		})

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/registerUser", methods=["POST"])
def registerUser():
	email=request.form.get("email")
	password = request.form.get("password")
	name = request.form.get("name")

	# Make sure all field are not empty
	if ((not email) or (not password) or (not name)): 
		return render_template("error.html", message="Please make sure you enter name, email and password.")
	
	# Checking if user already exists
	# user = User.query.filter_by(email=email).all()
	user = db.execute("SELECT * FROM users WHERE email= :email", {"email": email}).fetchone()
	db.commit()
	if (user):
		return render_template("error.html", message="A user with the same email already exists.")

	# Inserting new user
	user = User(email=email,password=password,name=name)
	# db.add(user)
	# db.commit()
	db.execute("INSERT INTO users (email, password, name) VALUES (:email, :password, :name)"
		,{"email": email, "password": password, "name": name})
	user = db.execute("SELECT * FROM users WHERE email= :email", {"email": email}).fetchone()
	db.commit()
	if (user):
		session["user"] = user
	return render_template("search.html")

@app.route("/loginUser", methods=["POST"])
def loginUser():
	email=request.form.get("email")
	password = request.form.get("password")

	# Make sure all field are not empty
	if ((not email) or (not password)): 
		return render_template("error.html", message="Please make sure you enter email and password.")
	
	# Checking if user already exists
	# user = User.query.filter_by(email=email).first()
	user = db.execute("SELECT * FROM users WHERE email= :email", {"email": email}).fetchone()
	db.commit()
	if (not user or user.password != password):
		return render_template("error.html", message="Wrong Email and Password combination.")


	session["user"] = user
	return render_template("user.html")

@app.route("/search", methods=["GET"])
def search():	
	if session["user"] == []:
		return render_template("error.html", message="Please login.")
	return render_template("search.html")

@app.route("/searchBy/<string:id>", methods=["POST", "GET"])
def searchBy(id):
	if request.method == "GET":
		return render_template("error.html", message="OOps, Something went wrong.")
	if session["user"] == []:
		return render_template("error.html", message="Please login.")
	searchText = request.form.get("searchText")
	# Make sure all field are not empty
	if (not searchText): 
		return render_template("error.html", message="Please enter search text.")
	
	if id == 'isbn':
		searchTextSrc = '%' + searchText + '%'
		# books = Book.query.filter(Book.isbn.like(searchTextSrc)).all()
		books = db.execute("SELECT * FROM books WHERE isbn LIKE :searchText", {"searchText": searchTextSrc}).fetchall()
		db.commit()
	elif id == 'title':
		searchTextSrc = '%' + searchText.capitalize() + '%'
		# books = Book.query.filter(Book.title.like(searchTextSrc)).all()
		books = db.execute("SELECT * FROM books WHERE title LIKE :searchText", {"searchText": searchTextSrc}).fetchall()
		db.commit()
	elif id == 'author':
		searchTextSrc = '%' + searchText.capitalize() + '%'
		# books = Book.query.filter(Book.author.like(searchTextSrc)).all()
		books = db.execute("SELECT * FROM books WHERE author LIKE :searchText", {"searchText": searchTextSrc}).fetchall()
		db.commit()
	else:
		return render_template("error.html", message="Oops, Something in not correct.")
	print(books)
	return render_template("search.html",books= books)


@app.route("/books/<string:book_isbn>")
def book(book_isbn):
	#Fetch the book
	# book = Book.query.get(book_isbn)
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", { "isbn": book_isbn }).fetchone()
	if book is None:
		return render_template("error.html", message="No such book")
	#Fetch the reviews
	# reviews = book.reviews
	reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", { "isbn": book_isbn }).fetchall()

	session["book"] = book
	session["reviews"] = reviews

	#Fetch Review data from goodreads api
	import requests
	res = requests.get("https://www.goodreads.com/book/review_counts.json", 
		params={"key": API_KEY, "isbns": book_isbn})
	if res.status_code != 200:
		raise Exception("Error: ApI request unsuccessful.")
	goodReadsData = res.json()

	return render_template("book.html", book = book, reviews = reviews, goodReadsData = goodReadsData)

@app.route("/reviewPost", methods=["POST"])
def reviewPost():
	isbn = session["book"].isbn
	comment = request.form.get("review")
	rate = request.form.get("inlineRadioOptions")
	# Make sure all field are not empty
	if ((not comment) or (not rate)): 
		return render_template("error.html", message="Please make sure you enter comment and rating.")
	
	for review in session["reviews"]:
		if review.user_id == session["user"].id:
			return render_template("error.html",message = "Can not post multiple reviews on the same book")
	# session["user"].add_review(isbn,rate,comment)
	db.execute("INSERT INTO reviews (isbn, user_id, rate, comment, username) VALUES (:isbn, :user_id, :rate, :comment, :username)",
			{"isbn": isbn, "user_id": session["user"].id, "rate": rate, "comment": comment, "username": session["user"].name})
	db.commit()
	return render_template("search.html",books= [])

