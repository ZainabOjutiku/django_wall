from flask import Flask, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "love"

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')


@app.route('/users')
def first_page():
    mysql = connectToMySQL('favorite_book')
    return render_template('login.html')


@app.route('/users/create', methods=['POST'])
def register():
    print(request.form)
    is_valid = True
    if len(request.form['first_name']) < 2:
        is_valid = False
        flash("First name must contain at least two letters and contain only letters", 'first_name')
    if len(request.form['last_name']) < 2:
        is_valid = False
        flash("Last name must contain at least two letters and contain only letters", 'last_name')
    if not EMAIL_REGEX.match(request.form['email']):
        flash("invalid email address", 'email')
        redirect('/users')
    if len(request.form['password']) < 8:
        is_valid = False
        flash("password must contain a number,capital letter,and be between 8-15 characters", 'password')
    if request.form['con_password'] != request.form['password']:
        is_valid = False
        flash("passwords must match", 'con_password')

    if is_valid:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        print(pw_hash)
        mysql = connectToMySQL('favorite_book')
        query = "INSERT INTO users (first_name,last_name,email,password,created_at, updated_at) VALUES (%(fname)s,%(lname)s,%(em)s,%(p_w)s, NOW(), NOW());"
        data = {
            'fname': request.form['first_name'],
            'lname': request.form['last_name'],
            'em': request.form['email'],
            'p_w': pw_hash
        }
        id = mysql.query_db(query, data)
        print('***********', id)
        flash("You have successfully registered!")
        return redirect('/users')
    return redirect('/users')

@app.route('/users/login', methods=["POST"])
def login():
    is_valid = True
    if not EMAIL_REGEX.match(request.form['login_email']):
        flash("invalid email address")
        return redirect('/users')

    if is_valid:
        mysql = connectToMySQL('favorite_book')
        query = "SELECT * FROM users WHERE email = %(email)s"#select from users where email added is same as the email put in which was registered
        data = {'email': request.form['login_email']}  # user information
        user_info = mysql.query_db(query, data)
        print(user_info)
        if len(user_info) == 0:
            flash("You must be a registered user")
            return redirect('/users')

        if bcrypt.check_password_hash(user_info[0]['password'], request.form['login_password']):
            flash("Login Successful")
            session['user_info'] = user_info
            return redirect("/users/show")
        else:
            flash("Login Unsuccessful")
            return redirect('/users')

@app.route('/users/show')
def show_user():
    if 'user_info' in session:
        print('*'*50,  session['user_info'] )
        mysql = connectToMySQL('favorite_book')
        query = "SELECT * FROM users where id = %(id)s"
        data = {'id': session['user_info'][0]['id']}
        users = mysql.query_db(query, data)
        print('*'*10, users)

        #show all the books
        mysql = connectToMySQL('favorite_book')
        query = "SELECT users.id,users.first_name, users.last_name,books.id, books.user_id, books.title, books.description, books.created_at, books.updated_at FROM books join users on books.user_id = users.id"
        session['all_books'] = mysql.query_db(query)
        print ('*'*100, session['all_books'])

        #show fav
        mysql = connectToMySQL('favorite_book')
        query = "SELECT * from fav_books where user_id = %(id)s"
        data = {'id': session['user_info'][0]['id']}
        favo_books = mysql.query_db(query,data)
        print ('^'*40, favo_books)
        return render_template('success.html', users = users, all_books = session['all_books'],favo_books = favo_books)


@app.route('/users/add_book', methods= ['POST'])
def add_book():
    is_valid = True
    if len(request.form['title'])< 1:
        is_valid = False
        flash('Title is required', 'title') 
    if len(request.form['description']) < 4:
        is_valid = False
        flash('description must be atleast 5 characters', "description")

    if is_valid:
        #add_book
        if 'user_info' in session:
            mysql = connectToMySQL('favorite_book')
            query = 'INSERT INTO books (user_id,title, description,created_at,updated_at) VALUES (%(id)s, %(title)s,%(description)s, NOW(), NOW());'
            data = { 'id':session['user_info'][0]['id'],
                    'title': request.form['title'],
                    'description':request.form['description']}
            session['books']= mysql.query_db(query, data)
            # print('*'*50, session['books'])

            #add _favoritebook
            mysql = connectToMySQL('favorite_book')
            query = "INSERT INTO fav_books (user_id, book_id, created_at, updated_at) VALUES (%(user_id)s,%(book_id)s,NOW(),NOW());"
            data = { 'user_id': session['user_info'][0]['id'],
                    'book_id' : session['books']
                    }
            print ("-"*50,session['user_info'][0]['id'])
            print ("-"*50,session['books'])
            fav_books = mysql.query_db(query, data)
            print ('-'*20, fav_books)
            return redirect ('/users/show')
        else:
            return redirect('/users/show')



@app.route('/users/<id>/edit')
def edit(id):
    if 'user_info' in session:
        mysql = connectToMySQL('favorite_book')
        query = "SELECT * FROM users where id = %(id)s"
        data = {'id': session['user_info'][0]['id']}
        users = mysql.query_db(query, data)
        print('*'*10, users)
        #show books
        # if session['user_info'][0]['id'] == session['books']:
        mysql = connectToMySQL('favorite_book')
        query = "SELECT books.id,users.first_name,users.last_name,books.user_id,books.title,books.description,books.created_at,books.updated_at from books join users on books.user_id = users.id where books.id = %(id)s;"
        data = {"id":id}
        session['edit_books'] = mysql.query_db(query, data)
        # print('$'*50, edit_books)


        return render_template('edit.html', users=users, edit_books=session['edit_books'])
@app.route('/users/<id>/view')
def show_page(id):
     if 'user_info' in session:
        print('*'*50,  session['user_info'] )
        mysql = connectToMySQL('favorite_book')
        query = "SELECT * FROM users where id = %(id)s"
        data = {'id': session['user_info'][0]['id']}
        users = mysql.query_db(query, data)
        print('*'*10, users)

        #show view page
        mysql = connectToMySQL('favorite_book')
        query = "SELECT books.id,users.first_name,users.last_name,books.user_id,books.title,books.description,books.created_at,books.updated_at from books join users on books.user_id = users.id where books.id = %(id)s;"
        data = {"id":id}
        view_books = mysql.query_db(query, data)
        print (';'*60, view_books)

        return render_template('view.html',users = users,view_books = view_books)


@app.route('/users/<id>/update', methods=["POST"])
def update(id):
        # print(session['user_info'][0]['id'])
        # print('~'*20,session['edit_books'])
        # print('~'*20,session['edit_books'][0]['user_id'])

    # if session['user_info'][0]['id'] == session['edit_books'][0]['user_id']:
        print(request.form)
        mysql = connectToMySQL('favorite_book')
        query = 'UPDATE books SET title = %(title)s, description = %(description)s, updated_at = NOW() where id = %(id)s;'
        data = {'title': request.form['new_title'],
                'description': request.form['new_dcp'],
                'id': id}
        update=mysql.query_db(query, data)
        print ('@'*40, update)
        return redirect ('/users/show')
    # else:
    #     flash("this is not your book.")

@app.route('/users/<id>/del', methods= ["POST"])
def delete_book(id):
    
    mysql = connectToMySQL('favorite_book')
    query = "DELETE FROM books WHERE id = %(id)s"
    data = {'id': id}
    delete = mysql.query_db(query, data)
    print('%'*40, delete)
    return redirect ('/users/show')

@app.route('/users/destroy', methods=["POST"])
def log_out():
    mysql = connectToMySQL('favorite_book')
    if 'user_info' in session:
        session.clear()
        return redirect('/users')
    
    
if __name__ == '__main__':
    app.run(debug=True)