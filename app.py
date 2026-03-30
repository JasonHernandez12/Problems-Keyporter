from flask import Flask
from database import problems

app = Flask(__name__)

@app.route('/test')
def ping():
    return 'I hate niggers'

if __name__ == '__main__':
    app.run(debug=True, port=6000)