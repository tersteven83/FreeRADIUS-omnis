#! usr/bin/env python3
from datetime import datetime
import mysql.connector
import sys
import radiusd


def authorize(p):
    print("***Authorize***")
    # Récupérer la date d'aujourd'hui
    ajd = datetime.now().date()
    #print(p)

    # Récupérer la date du vouche
    db = get_db()
    with db.cursor() as c:
        # get the username key
        request = convert_tuple_to_dict(p["request"])
        # config = convert_tuple_to_dict(p["config"])
        # request = convert_tuple_to_dict(p)
        username = request["User-Name"]
        mac_address = request.get("Calling-Station-Id")
        params = (username, )
        # préparer la requête
        query = "SELECT * FROM voucher WHERE voucher_code = %s"
        # (id, voucher_code, is_active, telephone_number, date, mac_address)
        
        c.execute(query, params)
        result = c.fetchone()
       # print("Adresse MAC: " + mac_address + " " +  result[5])

        if result is not None:
            # Vérification de l'adresse mac
            if result[5] is not None:
                # si l'adresse mac dans la BD ne correspond pas au mac request, on n'autorise pas l'authentification
                if mac_address is not None and mac_address != result[5]:
                    update_dict = {"config": (("Auth-Type", "Reject"),),
                                   "reply": (("Reply-Message", ":=",
                                              "Le code que vous avez entré est déjà utilisé"),)
                                   }
                    return radiusd.RLM_MODULE_REJECT, update_dict
                
            # si la date récupérée par notre requete est n'est pas aujourd'hui,
            # on rejete l'authentification de l'utilisateur
            if result[4] is not None:
                if result[4].date() != ajd:
                    print(result[4].date())
                    update_dict = {"config": (("Auth-Type", "Reject"),),
                                   "reply": (("Reply-Message", ":=",
                                              "Le code que vous avez entré est déjà utilisé"),)
                                   }
                    # print(update_dict)
                    return radiusd.RLM_MODULE_REJECT, update_dict
            else:
                return radiusd.RLM_MODULE_OK
        
        
        


def post_auth(p):
    print("***Post_Authentication***")
    print(p)


def get_db():
    connection_params = {
        'host': 'localhost',
        'user': 'raduser',
        'password': 'radpass',
        'database': 'raddb'
    }
    try:
        db = mysql.connector.connect(**connection_params)
        return db
    except (Exception, mysql.connector.Error) as e:
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
