# opendata-finess
Analyse des donnees Finess 
==========================

Analyse des donnnées Finess, disponible sur le site 
[www.data.gouv.fr](www.data.gouv.fr), sur 3 points :

1. conformité par rapport à la définition donnée dans le fichier de description des données ;
2. calcul du taux de données vides ;
3. répartition des mises à jour des données.

Le projet est composé de :

* un script python analysant les données et les publiant dans ElasticSearch
* un fichier docker-compose permettant de lancer ElasticSearch+Kibana pour naviguer dans les données.

Le projet sert de support au billet : [Analyse des données Finess publiées en Open Data](http://www.opikanoba.org/sante/finess_etalab)

# Telechargement du fichier Finess via l'API
Le script `down_finess.sh` permet le téléchargement du fichier de données Finess en utilisant l'[API data.gouv.fr](https://www.data.gouv.fr/fr/apidoc/).

L'interêt et le fonctionnement est expliqué dans le billet : [Interrogation data.gouv.fr via son API](http://www.opikanoba.org/sante/finess_api).
Il s'utilise simplement avec une date de référence. Cette date va être comparée avec la dernière date de mise à jour du fichier distant.
Si une version plus récente du fichier est disponible, elle est telechargée.


