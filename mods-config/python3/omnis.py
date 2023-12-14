#! /usr/bin/python3
import datetime
import mysql.connector
import sys, string, random, radiusd


def post_auth(p):
    """
    créer un utilisateur et ajouter dans le fichier user de freeradius,
    """
    print("***Post_Authentication***")
    db = get_db()
    with db.cursor() as c:
        # vérifier d'abord si l'utilisateur créer ne se trouve pas dansa base de donn�e
        user = generate_random_string(6)
        query = "SELECT * FROM number_auth WHERE code=%s"
        c.execute(query, (user,))
        result = c.fetchall()
        while(result):
            user = generate_random_string(6)
            result = c.execute(query, user).fetchall()
            
        # ajouter l'utilisateur dans la table number_auth
        query = "INSERT INTO number_auth (code, expiration) VALUES (%s, %s)"
        
        # la date d'expiration de cette compte est après 15min
        now = datetime.datetime.now()
        plus_15_min = now + datetime.timedelta(minutes=15)
        #plus_15_min = plus_15_min.strftime("%B %d %Y %H:%M:%S")
        
        params = (
            user, plus_15_min 
        )
        c.execute(query, params)
        db.commit()
        update_dict = {
            'reply': (("Reply-Message", ":=", f"http://192.168.11.150:8080/auth/number/{user}"),)
        }
    
    return radiusd.RLM_MODULE_UPDATED, update_dict

def get_db():
    connection_params = {
        'host': '192.168.11.251',
        'user': 'raduser',
        'password': 'radpass',
        'database': 'raddb'
    }
    try:
        db = mysql.connector.connect(**connection_params)
        return db
    #except (Exception, mysql.connector.Error) as e:
    except mysql.connector.Error as e:
        print(f"Vérifier la connexion à la base de donnée {e}")
        sys.exit(1)


def convert_tuple_to_dict(tuple_of_tuples):
    """
        Converts a tuple of tuples to a dictionary
        Args:
            tuple_of_tuples: A tuple of tuples, where each tuple contain a tuple
        Returns:
            A dictionary containing the key-value pairs from the tuple of tuples
    """
    dictionary = {}
    for key, value in tuple_of_tuples:
        dictionary[key] = value

    return dictionary


def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters_and_digits) for i in range(length))
    return random_string

