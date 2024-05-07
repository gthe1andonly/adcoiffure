from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/listings')
def listings():
    return render_template('listings.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/appointments')
def appointments():
    return render_template('appointments.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)
