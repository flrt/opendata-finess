# opendata-finess
Analyse des donnees Finess 
==========================

Analyse des donnnées Finess, disponible sur le site www.data.gouv.fr, sur 3 points :
1. conformité par rapport à la définition donnée dans le fichier de description des données
2. calcul du taux de données vides
3. répartition des mises à jour des données.

Le projet est composé de 
* un script python analysant les données et les publiant dans ElasticSearch
* un fichier docker-compose permettant de lancer ElasticSearch+Kibana pour naviguer dans les données.

Le projet sert de support au billet : <URL>
