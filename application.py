import os
from flask import Flask,render_template, request, flash, session
from sqlalchemy import create_engine
from flask_session import Session 
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import secure_filename

app=Flask(__name__,static_folder='static')

UPLOAD_FOLDER=r"C:\Users\NISHA\Desktop\projects\p5\static\images"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

DATABASE_URL="postgres://postgres:newPassword@localhost:5432/bookcase"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

Session(app)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
	raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route('/')
def index():
	if 'username' in session:
		cases=db.execute("SELECT * FROM book_info").fetchall()
		return render_template("home.html",cases=cases)	
	return render_template("index.html")

@app.route('/login', methods=['GET','POST'])
def login():
	if request.method=='POST':
		username = request.form.get('username')
		password = request.form.get('password')
		query=db.execute("SELECT * FROM user_info WHERE username=:username AND password=:password ", {"username":username,"password":password}).fetchall()
		if query==[]:
			return "Invalid details..!!"
		session['username'] = username
		cases=db.execute("SELECT * FROM book_info").fetchall()
		return render_template("home.html",cases=cases)	
	return "You are not logged in..!!"

@app.route('/new',methods=['GET'])
def new():
	return render_template("signup.html")

@app.route('/signup',methods=['POST'])
def signup():
	names=db.execute("SELECT username FROM user_info").fetchall()
	for name in names:
		if request.form.get('username') in name.username:
			flash("Username is taken")
			return render_template("signup.html")
	username = request.form.get('username')
	email = request.form.get('email')
	if request.form.get('password') == request.form.get('c_password'):
		password = request.form.get('password')
	else:
		flash("Password does not match")
		return render_template("signup.html")	
	db.execute("INSERT INTO user_info(username,email,password) VALUES(:username,:email,:password)", {"username": username,"email":email,"password":password})
	db.commit()
	db.close()
	return render_template("index.html")
@app.route('/logout')
def logout():	
	session.pop('username', None)
	return render_template("index.html")

@app.route('/profile')
def profile():
	return render_template("profile.html")	

@app.route('/sell')
def sell():
	return render_template("sell.html")	

@app.route('/view/<string:show_book>')
def view(show_book):
	img_name=show_book
	name=session.get('username')
	order=db.execute("SELECT * FROM profile_info WHERE profile_name=:name AND order_book=:img_name",{"name":name,"img_name":img_name}).fetchone()
	views=db.execute("SELECT * FROM book_info WHERE image=:img_name",{"img_name":img_name}).fetchone()
	return render_template("book_view.html",views=views,name=name,order=order)	

@app.route('/search')
def search():
	book_name=request.form.get('search')
	searches=db.execute("SELECT * FROM book_info WHERE book_name=:book_name",{"book_name":book_name}).fetchall()
	print(searches)
	return render_template("search.html",searches=searches)

@app.route('/back_to_home')
def back_to_home():
	cases=db.execute("SELECT * FROM book_info").fetchall()
	return render_template("home.html",cases=cases)	

@app.route('/buy/<string:book_name>/<string:owner_name>/<string:book_writer_name>/<string:book_price>/<string:book_description>/<string:book_image>')
def buy(book_name,owner_name,book_writer_name,book_price,book_description,book_image):
	profile_name=session.get('username')
	order_book=book_name
	seller_name=owner_name
	writer_name=book_writer_name
	price=book_price
	description=book_description
	image=book_image
	db.execute("INSERT INTO profile_info(profile_name,order_book,seller_name,writer_name,price,description,image) VALUES(:profile_name,:order_book,:seller_name,:writer_name,:price,:description,:image)",{"profile_name":profile_name,"order_book":order_book,"seller_name":seller_name,"writer_name":writer_name,"price":price,"description":description,"image":image})
	db.commit()
	db.close()
	message ="deliver"
	return render_template("final.html",message=message)

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

@app.route('/cased',methods=['POST'])
def cased():
	name=session.get('username')
	book_name=request.form.get('book_name')
	file = request.files['image']
	writer_name=request.form.get('writer_name')
	address=request.form.get('address')
	price=request.form.get('price')
	mobile=request.form.get('mobile')
	description=request.form.get('description')
	if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			db.execute("INSERT INTO book_info(owner_name,book_name,image,writer_name,address,price,mobile,description) VALUES(:owner_name,:book_name,:image,:writer_name,:address,:price,:mobile,:description)",{"owner_name":name,"book_name":book_name,"image":filename,"writer_name":writer_name,"address":address,"price":price,"mobile":mobile,"description":description})
			db.commit()
			db.close()
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			message="collect"
			return render_template("final.html",message=message)
	return "Invalid File Format"

@app.route('/love/<string:book>')
def love(book):
	book_name=book
	love=db.execute("SELECT * FROM book_info WHERE book_name=:book_name",{"book_name":book_name}).fetchone()
	profile_name=session.get('username')
	love_book=love.book_name
	seller_name=love.owner_name
	writer_name=love.writer_name
	price=love.price
	description=love.description
	image=love.image
	db.execute("INSERT INTO profile_info(profile_name,love_book,seller_name,writer_name,price,description,image) VALUES(:profile_name,:love_book,:seller_name,:writer_name,:price,:description,:image)",{"profile_name":profile_name,"love_book":love_book,"seller_name":seller_name,"writer_name":writer_name,"price":price,"description":description,"image":image})
	db.commit()
	db.close()

	return render_template("sellfinal.html")

@app.route('/my_books')
def my_books():
	name=session.get('username')
	loves=db.execute("SELECT * FROM profile_info WHERE profile_name=:name AND love_book IS NOT NULL",{"name":name}).fetchall()
	orders=db.execute("SELECT * FROM profile_info WHERE profile_name=:name AND order_book IS NOT NULL",{"name":name}).fetchall()
	books=db.execute("SELECT * FROM book_info WHERE owner_name=:name",{"name":name}).fetchall()
	return render_template("profile.html",books=books,orders=orders,loves=loves)

if __name__ == '__main__':
	app.run(debug=True)