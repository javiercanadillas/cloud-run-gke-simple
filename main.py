import os, socket, platform, subprocess

from flask import Flask, request, make_response, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

app = Flask(__name__)
# This is necessary for Flask-WTF package
# Using python-dotevn to extract it from the environment
#app.config['SECRET_KEY'] = 'dont-ever-do-this'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
bootstrap = Bootstrap(app)
moment = Moment(app)

# Include POST method for form handling
@app.route('/', methods=['GET', 'POST'])
def index():
    name = None
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
    hostname = socket.gethostname()
    host_info = {
        'hostname': socket.gethostname(),
        'system': platform.platform(),
        'release': platform.release(),
        'version': platform.version(),
        #'uptime': subprocess.check_output(['cat', '/proc/uptime']).decode('utf-8').split()[0]
    }
    user_agent = request.headers.get('User-Agent')
    current_time = datetime.utcnow()
    print(current_time)
    return render_template('index.html', 
                            form=form,
                            user_agent=user_agent,
                            name=name,
                            host_info=host_info,
                            current_time=current_time)

@app.route('/cookie')
def set_cookie():
    response = make_response('<h1>This document carries a cookie!</h1>')
    response.set_cookie('answer', '42')
    return response

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))