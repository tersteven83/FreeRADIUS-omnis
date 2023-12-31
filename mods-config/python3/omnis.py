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
            'reply': (("WISPr-Redirection-URL", ":=", f"http://192.168.11.150:8080/auth/number/{user}"),)
        }
    
    return radiusd.RLM_MODULE_UPDATED, update_dict

def authorize(p):
    """
    charger tous les AVP du group envoyé aux parametres dans le paquets config
    """
    config = convert_tuple_to_dict(p["config"])
    if "Group" in config:
        groups = config["Group"]
        
        # les requetes SQL au BD
        group_check_query = "\
            SELECT attribute, op, \
            CASE \
                    WHEN Attribute = 'Expiration' THEN DATE_FORMAT(STR_TO_DATE(Value, '%Y-%m-%d'), '%e %b %Y') \
                    ELSE Value \
            END AS Value \
            FROM radgroupcheck \
            WHERE groupname = %s \
            ORDER BY id"
        group_reply_query = "\
            SELECT attribute,op, value \
            FROM radgroupreply \
            WHERE groupname = %s \
            ORDER BY id"
        avp = {
            "reply": [],
            "config": []    
        }
        db = get_db()
        with db.cursor() as c:
            for i in range(len(groups)):
                c.execute(group_check_query, (groups[i],))
                group_chk = c.fetchall()
                for j in range(len(group_chk)):
                    avp['config'].append(group_chk[j])
                
                c.execute(group_reply_query, (groups[i],))
                group_repl = c.fetchall()
                for j in range(len(group_repl)):
                    avp['reply'].append(group_repl[j])
            # convertir les keys de avp en tuple
            avp['config'] = tuple(avp['config'])
            avp['reply'] = tuple(avp['reply'])  
            
            return radiusd.RLM_MODULE_UPDATED, avp
        
        
    

def get_db():
    connection_params = {
        'host': '127.0.0.1',
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
        if key in dictionary:
            if type(dictionary[key]) == str:
                dictionary[key] = [dictionary[key]]
            dictionary[key].append(value)
            continue
        dictionary[key] = value

    return dictionary


def generate_random_string(length):
    letters_and_digits = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(letters_and_digits) for i in range(length))
    return random_string

