import random
import time
from datetime import datetime, timedelta
import uuid
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# =========================================================================
# 1. CONFIGURATION ET CONNEXION
# =========================================================================
# Puisque tu as activé la sécurité avec PasswordAuthenticator :
auth_provider = PlainTextAuthProvider(username='cassandra', password='cassandra')

# '127.0.0.1' fonctionne si le port 9042 de ton Docker est mappé sur ta machine
cluster = Cluster(['cassandra-europe'], port=9042)
session = cluster.connect('logitrack')

print("🔌 Connecté avec succès à Cassandra !")

# =========================================================================
# 2. GÉNÉRATEUR DE DONNÉES ALÉATOIRES BORNÉES
# =========================================================================
# Liste de 5 camions fictifs (UUID fixes pour pouvoir les requêter facilement après)
TRUCKS = [uuid.UUID(f"00000000-0000-0000-0000-00000000000{i}") for i in range(1, 6)]

# Préparation de la requête pour de meilleures performances (Prepared Statement)
query = """
    INSERT INTO telemetry_by_truck (truck_id, day_date, event_time, latitude, longitude, speed, engine_temp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
"""
prepared = session.prepare(query)

print("\n🚀 Démarrage de l'injection (Ctrl+C pour arrêter)...")

try:
    nb_insertions = 0
    while True:
        # Sélection d'un camion au hasard parmi les 5
        truck_id = random.choice(TRUCKS)
        
        # Gestion du temps actuel
        now = datetime.now()
        day_date = now.date()
        
        # ---- VALEURS ALÉATOIRES BORNÉES ----
        # Coordonnées géographiques centrées autour de la France
        latitude = round(random.uniform(43.0, 50.0), 5)
        longitude = round(random.uniform(-1.0, 6.0), 5)
        
        # Vitesse bornée entre 0 et 130 km/h (avec 5% de chance de faire un excès de vitesse pour tester l'index !)
        if random.random() < 0.05:
            speed = round(random.uniform(111.0, 140.0), 1)  # Excès de vitesse !
        else:
            speed = round(random.uniform(0.0, 90.0), 1)     # Vitesse normale camion
            
        # Température du moteur bornée entre 75°C (normal) et 115°C (surchauffe)
        engine_temp = random.randint(75, 115)
        # ------------------------------------

        # Exécution de l'insertion
        session.execute(prepared, (truck_id, day_date, now, latitude, longitude, speed, engine_temp))
        
        nb_insertions += 1
        print(f"[{nb_insertions}] Camion {truck_id.hex[-1]} -> Vitesse: {speed} km/h | Temp: {engine_temp}°C | Lat: {latitude}", end="\r")
        
        # Pause de 0.5 seconde entre chaque envoi pour simuler le flux continu
        # time.sleep(0.5)

except KeyboardInterrupt:
    print(f"\n\n🛑 Injection stoppée par l'utilisateur. Total inséré : {nb_insertions} lignes.")
finally:
    cluster.shutdown()
    print("🔌 Connexion Cassandra fermée proprement.")