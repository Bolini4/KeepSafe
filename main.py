import hashlib
from flask import Flask, jsonify, render_template, request, session,redirect, url_for
from flask_session import Session
import requests
import os
import json
import string
import hash_functions
import glob

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

def create_json(file,data):
    with open("coffres/"+ file+".json", 'w') as f:
        json.dump(data, f, indent=2)  # indent=2 pour une indentation lisibl
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

    generate_first_json(name)

    key = hash_functions.generate_key(password)
    print("key generateed : "+str(key))

    hash_functions.encrypt("coffres/" + name + ".json", key)

    return render_template("finaliser.html", name=name, password=password)

@app.route('/ouvrir/<nom_fichier>')
def ouvrir_coffre_fort(nom_fichier):
    # La variable "nom_fichier" contiendra le nom du fichier spécifié dans l'URL
    return render_template("ouvrir.html", nom_fichier=nom_fichier)

@app.route('/show/<nom_fichier>', methods=['GET','POST'])
def show_coffre_fort(nom_fichier):
    
    if session.get('password'):
        password = session["password"]
        print("password from session : "+str(password))
    else:
        password = request.form.get('password')
        print("password from form : "+str(password))

    key = hash_functions.generate_key(password, load_existing_salt=True)

    status = hash_functions.decrypt("coffres/" + nom_fichier + ".json", key)
    if status == 1:
        with open("coffres/"+ nom_fichier + ".json", 'r') as file:
            data = json.load(file)

        with open("coffres/"+ nom_fichier + ".json", 'w') as file:
            json.dump(data, file)

        with open("coffres/"+ nom_fichier + ".json", 'r') as file:
            data = json.load(file)

        #Calculer la force du mdp pour chaque site
        for site in data["sites"]:
            site['password_length'] = len(site['mot_de_passe'])
            strength_score = evaluate_password_strength(site['mot_de_passe'])
            description = password_descriptions[strength_score]
            site['strength'] = {
                'description': description,
                'color': password_colors[description]
            }
            
            # Vérifiez si le mot de passe a été compromis en ligne
            is_leaked = check_password_leak(site['mot_de_passe'])
            site['leaked_online'] = 'OUI' if is_leaked else 'NON'

        session['password'] = password
        session['nom_fichier'] = nom_fichier+".json"

        return render_template("dashboard.html", data=data)
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


@app.route('/show/edit', methods=['GET', 'POST'])
def edit_site():
    print("coucouEdit")
    file_json = session['nom_fichier']
    password_session = session['password']
    file = file_json.split('.json')[0]
    print(file)
    # Chargez les données du fichier JSON dès le début de la fonction
    with open("coffres/"+ file+".json", 'r') as f:
        data = json.load(f)

    if request.method == 'POST':
        index = int(request.form.get('index'))
        if 0 <= index < len(data['sites']):
            nom = request.form.get('nom')
            login = request.form.get('login')
            mot_de_passe = request.form.get('mot_de_passe')
            print(nom,login,mot_de_passe,index)
            
            data['sites'][index] = {
                'nom': nom,
                'login': login,
                'mot_de_passe': mot_de_passe
                # Ajoutez d'autres champs si nécessaire
            }
            print(data['sites'][index])
            print(data)
            os.remove("coffres/"+ file+".json")
            create_json(file,data)

            key = hash_functions.generate_key(password_session)
            hash_functions.encrypt("coffres/" + file_json, key)

            return redirect(url_for('show_coffre_fort', nom_fichier=file))
        else:
            return jsonify({'Index de l\'élément à modifier non valide.'})
    else:
        index = request.args.get('index')
        site = data['sites'][int(index)]
        
        return render_template('dashboard.html', data=data, site=site, index=index)

password_descriptions = {
    1: "Très faible",
    2: "Faible",
    3: "Moyen",
    4: "Fort",
    5: "Très fort"
}

password_colors = {
    "Très faible": "red",
    "Faible": "orange",
    "Fort": "lightgreen",
    "Très fort": "green",
    "Extrêmement fort": "darkgreen"
}

def evaluate_password_strength(password):
    """
    Évalue la solidité d'un mot de passe basé sur certains critères.
    
    Retourne un score compris entre 0 et 5, où 5 indique un mot de passe très fort.
    """
    score = 0

    # Longueur du mot de passe
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1

    # Lettres majuscules et minuscules
    if any(char in string.ascii_lowercase for char in password):
        score += 1
    if any(char in string.ascii_uppercase for char in password):
        score += 1

    # Présence de chiffres
    if any(char.isdigit() for char in password):
        score += 1

    # Présence de caractères spéciaux
    special_characters = string.punctuation
    if any(char in special_characters for char in password):
        score += 1

    # Assurez-vous que le score est compris entre 0 et 5
    return min(score, 5)


def check_password_leak(password):
    # Calculer le hash SHA-1 complet du mot de passe
    sha1_full_hash = hashlib.sha1(password.encode()).hexdigest().upper()
    
    # Extraire les cinq premiers caractères du hash pour la requête
    sha1_prefix = sha1_full_hash[:6]

    # Faites une requête à l'API "Have I Been Pwned" pour vérifier si le hash existe dans les fuites
    response = requests.get(f'https://api.pwnedpasswords.com/range/{sha1_prefix}')
    
    if response.status_code == 200:
        # Analysez la réponse pour voir si le hash complet correspond à l'un des retours de l'API
        hashes = [line.split(':') for line in response.text.splitlines()]
        for h, count in hashes:
            if sha1_full_hash[6:] == h:  # Comparer seulement le suffixe du hash complet
                return True  # Le mot de passe a été compromis
    return False  # Le mot de passe n'a pas été compromis