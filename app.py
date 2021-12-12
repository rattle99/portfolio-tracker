from flask import Flask, render_template, flash, request, redirect
import os
from flask.helpers import url_for
from werkzeug.utils import secure_filename

from user.charting import util
from user.scanner import finalParser

app = Flask(__name__)
app.secret_key = "super secret key"

ALLOWED_EXTENSIONS = {'pdf', 'PDF'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'GET':
        return render_template('upload.html')

    if request.method == 'POST':
        if request.files:
            pdf = request.files['inputGroupFile']

            if pdf.filename == '':
                flash('No selected file')
                print('No file')
                return redirect(request.url)

            if not allowed_file(pdf.filename):
                flash('Wrong filetype')
                print('Wrong filetype')
                return redirect(request.url)

            else:
                filename = secure_filename(pdf.filename)
                pdf.save(os.path.join('./temp/', filename))
                password = request.form['password']
                return redirect(url_for('result', filename=os.path.join('./temp/', filename), password=password))


@app.route("/result", methods=['GET', 'POST'])
def result():
    filename = request.args.get('filename')
    password = request.args.get('password')
    userData, name, statementPeriod, summary = finalParser(filename, password)
    bokeh_script_code, chart_codes = util(
        filename=filename, password=password, userData=userData)
    return render_template('result.html', userData=userData, summary=summary, name=name, bokeh_script_code=bokeh_script_code,
                           chart_inv=chart_codes[0], pie_chart=chart_codes[1], statementPeriod=statementPeriod)


if __name__ == "__main__":
    app.run(debug=True)
