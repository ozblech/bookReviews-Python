import os
import csv
from flask import Flask
from models import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)



def main():
	db.create_all()
	f = open("books.csv")
	reader = csv.reader(f)
	next(reader, None)
	for isbn, title, author, year in reader:
		book = Book(isbn=isbn,title=title,author=author,year=year)
		db.session.add(book)
	db.session.commit()

if __name__ == "__main__":
	with app.app_context():
		main()