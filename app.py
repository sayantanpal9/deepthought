from flask import Flask,render_template,request,redirect,url_for
import requests

app = Flask(__name__)

@app.route('/home',methods=['POST','GET'])
def home():
    if request.method=='POST':
        print(request.form['transcript'])
        return redirect(url_for('resp',data = request.form))
    return render_template('home.html')



@app.route('/resp',methods=['GET'])
def resp():
    data = request.args.get('data')


    # response = requests.post('http://localhost:11434/api/generate', json={
    #     'model': 'llama3.2:1b',
    #     'prompt': prompt,
    #     'stream': False
    # })
    print(response.json()['response']) 
    return render_template('res.html',data=data)




if __name__=='__main__':
    app.run(debug=True)