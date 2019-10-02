from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, session, flash, Response
import re
from mysqlconnection import connectToMySQL 
from flask_bcrypt import Bcrypt  
from flask import jsonify
import json
import sqlite3
from bs4 import BeautifulSoup

app = Flask(__name__)
app.static_folder = 'static'

app.config['SECRET_KEY'] = '09e938dd0f6d856e9031dc067facb52f'
bcrypt = Bcrypt(app)  


@app.route("/", methods=['GET', 'POST'])
@app.route("/home")
def home():
        if 'useremail' in session:
            return render_template("index.html", logged_in=True)
        else:
            return render_template('index.html', logged_in=False)

        


@app.route("/major/<major_id>")
def major(major_id):
    id = major_id
    mysql = connectToMySQL("majorrater")
    query = "SELECT content, user_id, id from reviews where reviews.major_id = %(id)s"
    data = {
        "id": id
    }
    reviews = mysql.query_db(query, data)
    if 'useremail' in session:
        mysql = connectToMySQL("majorrater")
        dataOne = {
                "email": session['useremail']
            }
        queryOne = "SELECT id FROM users where email = %(email)s"
        user_id = mysql.query_db(queryOne, dataOne)
        user_id = user_id[0]["id"]
        logged_in=True
    else:
        user_id = None
        logged_in=False 
    return render_template('major.html', major_id=major_id, reviews=reviews, logged_in=logged_in, user_id=user_id)

@app.route("/add-review", methods=['POST'])
def add_review():

    
    if 'useremail' in session:
        dataOne = {
            "email": session['useremail']
        }
        mysql = connectToMySQL("majorrater")
        queryOne = "SELECT id FROM users where email = %(email)s"
        user_id = mysql.query_db(queryOne, dataOne)
        user_id = user_id[0]["id"]
        dataTwo = {
            "user_id": user_id,
            "major_id": request.form["majorId"],
            "content": request.form["content"]

        }
        mysql = connectToMySQL("majorrater")
        queryTwo = "INSERT INTO reviews (content, user_id, major_id) VALUES (%(content)s, %(user_id)s, %(major_id)s);"
        new_review = mysql.query_db(queryTwo, dataTwo)
        
    
    else:
        dataThree = {
             "major_id": request.form["majorId"],
            "content": request.form["content"]
        }
        mysql = connectToMySQL("majorrater")
        queryThree = "INSERT INTO reviews (content, major_id) VALUES (%(content)s, %(major_id)s);"
        new_review = mysql.query_db(queryThree, dataThree)


    return redirect("/")


@app.route("/register")
def register_page():
    return render_template('register.html')

@app.route('/create_user', methods=['POST'])
def create_user():
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$') 
    is_valid = True
    if not EMAIL_REGEX.match(request.form['email']):    # test whether a field matches the pattern
        is_valid = False
        flash("Invalid email address")
    if len(request.form['username']) < 1:
    	is_valid = False
    	flash("Please enter a username")
    if len(request.form['password']) < 2:
    	is_valid = False
    	flash("Please enter password")
    
    if not is_valid:
        return redirect("/register")

    else:
        session['useremail'] = request.form['email']
        pw_hash = bcrypt.generate_password_hash(request.form['password']) 
        mysql = connectToMySQL("majorrater")

        query = "INSERT INTO users (username, password, email) VALUES (%(un)s, %(pw)s, %(em)s);"
        data = {
            "un": request.form["username"],
            "pw": pw_hash,
            "em": request.form["email"]
        }
        new_user = mysql.query_db(query, data)
        return redirect("/")



@app.route("/show_login")
def show_login():
    return render_template('login.html')

@app.route("/login_user", methods=['POST'])
def login_user():
    # see if the username provided exists in the database
    mysql = connectToMySQL("majorrater")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form["email"] }
    result = mysql.query_db(query, data)
    if len(result) > 0:
        # assuming we only have one user with this username, the user would be first in the list we get back
        # of course, we should have some logic to prevent duplicates of usernames when we create users
        # use bcrypt's check_password_hash method, passing the hash from our database and the password from the form
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            # if we get True after checking the password, we may put the user id in sessioncopy
            session['useremail'] = result[0]['email']
            # never render on a post, always redirect!
            return redirect('/')
    # if we didn't find anything in the database by searching by username or if the passwords don't match,
    # flash an error message and redirect back to a safe route
    flash("You could not be logged in")
    return redirect("/show_login")



# @app.route("/autocomplete", methods=['GET'])
# def search():
#     mysql = connectToMySQL("majorrater")
#     query = "SELECT * FROM majors WHERE name LIKE %(name)s;"
#     data = {
#         "name" : request.args.get('autocomplete')
#     }
#     results = mysql.query_db(query, data)
#     return render_template("partials/possiblemajors.html", majors = results) # render a template which uses the results




@app.route("/search", methods=['POST', 'GET'])
def search():
    output = ''
    mysql = connectToMySQL("majorrater")
    
    data_received = json.loads(request.data)
    data = data_received['query']
    
    var_data = '%' + data + '%'

    mysqlQuery = "SELECT name, id FROM majors WHERE majors.name LIKE '%s' LIMIT 10;" %var_data

   
    majors =  mysql.query_db(mysqlQuery)


    output += '<ul class="list-unstyled">'

    # if len(result) > 0:
    #     for major in result:
    #         output += '<li>' + major["name"] + '</li>' 

    # else:
    #     output += '<li>Major Not Found</li>'
    
    output += '</ul>'
    
    
    
    return render_template("partials/majorOutput.html", majors=majors)
    

@app.route("/logout")
def destroy_session():
    session.clear()
    return redirect('/')

@app.route("/delete/<id>")
def delete_review(id):
    mysql = connectToMySQL("majorrater")
    data = {
        "id": id
    }
    query = "DELETE FROM reviews where id = %(id)s"
    mysql.query_db(query, data)
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)