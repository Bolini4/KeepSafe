from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

coffre_fort = {
    "utilisateur": "bolini",
    "mot_de_passe": "coucou"
}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/passwordGen")
def passwordGen():
    return render_template("passge.html")


@app.route('/ouvrir', methods=['GET', 'POST'])
def ouvrir_coffre_fort():
    if request.method == 'POST':
        print(request.form['mot_de_passe'])
        print("coucou")
        print(coffre_fort['mot_de_passe'])
        mot_de_passe_saisi = request.form['mot_de_passe']
        mot_de_passe_coffre = coffre_fort['mot_de_passe']
        if mot_de_passe_saisi == mot_de_passe_coffre:
            # Mot de passe correct, redirigez l'utilisateur vers le coffre-fort
            return redirect(url_for('coffre_fort'))
        else:
            # Mot de passe incorrect, affichez un message d'erreur
            message_erreur = "Mot de passe incorrect. Veuillez réessayer."
            return render_template('login.html', erreur=message_erreur)
    return render_template('login.html')

@app.route('/coffre-fort')
def coffre_fort():
    # Vous pouvez ajouter ici la logique pour afficher le coffre-fort
    return "Coffre-fort ouvert !"