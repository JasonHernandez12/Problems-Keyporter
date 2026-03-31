<<<<<<< HEAD
from flask import Flask
from database import problems

app = Flask(__name__)

@app.route('/test')
def test():
    return 'I hate niggers'

if __name__ == '__main__':
    app.run(debug=True, port=6000)
=======
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    # Ahora Flask busca el archivo dentro de la carpeta 'templates'
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
>>>>>>> 8efaf9b (Mi primer commit)
