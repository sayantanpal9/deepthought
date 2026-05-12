from flask import Flask,render_template

app = Flask(__name__)

@app.route('/',methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/resp',methods=['GET'])
def resp():
    return render_template('res.html')
if __name__=='__main__':
    app.run(debug=True)