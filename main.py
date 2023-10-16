from flask import Flask, render_template, request, session,redirect, url_for
from flask_session import Session
import os
import json
from hashlib import sha256
import hash_functions

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def check_json_exists(filename):
    # Vérifiez d'abord si le fichier existe
    if os.path.isfile("coffres/" + filename + ".json"):
        # Le fichier existe déjà, vous pouvez choisir de gérer cette situation ici
        print(f"Le fichier {filename}.json existe déjà.")
        return 1
    else:
        return 0
    

def generate_first_json(filename):
    coffre = filename
    sites = [
        {
            "nom": "Site Web 1",
            "login": "nom_utilisateur_site1",
            "mot_de_passe": "mot_de_passe_site1"
        },
        {
            "nom": "Site Web 2",
            "login": "nom_utilisateur_site2",
            "mot_de_passe": "mot_de_passe_site2"
        },
    ]
    donnees = {
    "utilisateur": coffre,
    "sites": sites
    }
    with open("coffres/" + filename + ".json", "w") as f:
        # Utilisez json.dump pour écrire les données dans le fichier
        json.dump(donnees, f, indent=2)  # indent=2 pour une indentation lisibl

def list_json_files():
    json_files = []

    try:
        for file in os.listdir("coffres"):
            if file.endswith(".json"):
                json_files.append(file)
    except:
        pass
    return json_files

@app.route("/")
def index():
    list_json_files()
    return render_template("index.html", json_files=list_json_files() )



@app.route('/creer', methods=['POST'])
def creer_coffre_fort():
    # Récupérez la valeur soumise pour le champ 'nom' du formulaire
    nom_du_coffre = request.form.get('nom')
    exists = check_json_exists(nom_du_coffre)
    if exists == 1:
        return render_template("alreadyexists.html")
    elif exists == 0:
        return render_template("creer.html", nom_du_coffre=nom_du_coffre)


@app.route('/finaliser', methods=['POST'])
def finaliser_CF():
    # Récupérez la valeur soumise pour le champ 'nom' du formulaire
    name = request.form.get('nom')
    password = request.form.get('password')
    print("this is name : "+name)
    print(password)

    generate_first_json(name)

    key = hash_functions.generate_key(password)
    print("key generateed : "+str(key))

    hash_functions.encrypt("coffres/" + name + ".json", key)

    return render_template("finaliser.html", name=name, password=password)

@app.route('/ouvrir/<nom_fichier>')
def ouvrir_coffre_fort(nom_fichier):
    # La variable "nom_fichier" contiendra le nom du fichier spécifié dans l'URL
    return render_template("ouvrir.html", nom_fichier=nom_fichier)

@app.route('/show/<nom_fichier>', methods=['POST'])
def show_coffre_fort(nom_fichier):

    password = request.form.get('password')

    key = hash_functions.generate_key(password, load_existing_salt=True)

    status = hash_functions.decrypt("coffres/" + nom_fichier + ".json", key)
    if status == 1:
        with open("coffres/"+ nom_fichier + ".json", 'r') as file:
            data = json.load(file)

        session['password'] = password
        session['nom_fichier'] = nom_fichier+".json"

        return render_template("show.html", data=data)
    elif status == 0:
        return render_template("wrongpass.html")

@app.route("/lock")
def lock_coffre_fort():
    
    password_session = session['password']
    file = session['nom_fichier']

    key = hash_functions.generate_key(password_session)
    hash_functions.encrypt("coffres/" + file, key)
    session.pop('password', None)
    session.pop('nom_fichier', None)

    return redirect(url_for('index'))
