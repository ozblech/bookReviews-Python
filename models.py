from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Book(db.Model):
	__tablename__ = "books"
	isbn = db.Column(db.String, primary_key=True)
	title = db.Column(db.String, nullable=False)
	author = db.Column(db.String, nullable=False)
	year = db.Column(db.Integer, nullable=False)
	reviews = db.relationship("Review", backref="book", lazy=True)

class User(db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String, nullable=False)
	password = db.Column(db.String, nullable=False)
	name = db.Column(db.String, nullable=False)

	def add_review(self,isbn,rate,comment):
		review = Review(isbn=isbn,rate=rate,comment=comment,user_id=self.id,username=self.name)
		db.session.add(review)
		db.session.commit() 

class Review(db.Model):
	__tablename__ = "reviews"
	id = db.Column(db.Integer, primary_key=True)
	isbn = db.Column(db.String, db.ForeignKey("books.isbn"), nullable=False)
	rate = db.Column(db.Integer, nullable=False)
	comment = db.Column(db.String, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
	username = db.Column(db.String, nullable=False)

