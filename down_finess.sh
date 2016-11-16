#!bin/bash
## Usage: sh down_finess.sh [DATE]
##
##  DATE : format YYYY-MM-DD
##         Ex : sh down_finess.sh `date -v-1d +"%Y-%m-%d"` 
##         Ex : sh down_finess.sh 2016-04-15
#
# Recherche via l'API data.gouv.fr d'un dataset
# si la date du fichier distant est posterieure a celle de reference passee en argument
# le fichier est telecharge dans WORKDIR
#
# Tests sous bash BSD - GNU bash, version 4.3.42(1)-release (x86_64-apple-darwin15.4.0
# Frederic LAURENT - Fourni AS IS - License CC-BY 3.0
# https://creativecommons.org/licenses/by/3.0/fr/

# Creation d'un repertoire temporaire de travail
WORKDIR=/tmp/finess
mkdir -p $WORKDIR

# Positionnement de la date de reference, par defaut, la date du jour
REF_DATE=`date +%Y-%m-%d`

if [ $# -eq 1 ]; 
then 
  REF_DATE=$1
fi

# Positionnement des variables pour le dataset
# DATASET = FINESS
DATASET=53699569a3a729239d2046eb
DATASET_INFOS=$WORKDIR/infos.json
# Fichier du dataset = fichier global
DATAFILE=17eb6ec3-af61-4114-9650-de836b869748
URL=https://www.data.gouv.fr/api/1/datasets/$DATASET/

# Telechargement des donnees sur le jeu de valeurs
curl -s $URL > $DATASET_INFOS

# Recuperation de l'URL du fichier
DATAFILE_URL=`cat $DATASET_INFOS | jq -r '.resources[] | .id + " " + .url' | grep $DATAFILE | cut -d' ' -f2`

# Recuperation de la date de derniere mise a jour
DATAFILE_DATE=`cat $DATASET_INFOS | jq -r '.resources[] | .id + " " + .last_modified' | grep $DATAFILE | cut -d' ' -f2 | cut -c 1-19`

# Recuperation du checksum attendu du fichier
DATAFILE_CHECKSUM=`cat $DATASET_INFOS | jq -r '.resources[] | .id + " " + .checksum.value' | grep $DATAFILE | cut -d' ' -f2`

# recupeation du vrai nom du fichier
NEWFILENAME="${DATAFILE_URL##*/}"
echo "Fichier     : "$NEWFILENAME
echo "Date de MAJ : "$DATAFILE_DATE
echo "Date de REF : "$REF_DATE

# Test si la date du fichier sur data.gouv.fr est posterieure a la date de reference
DFILE=`date -jf '%Y-%m-%dT%H:%M:%S' "$DATAFILE_DATE" "+%s"`
DREF=`date -jf '%Y-%m-%d' "$REF_DATE" "+%s"`

if [[ $DFILE > $DREF ]] ;
then
  # Telechargement du fichier
  echo "Telechargement du fichier de donnees " $NEWFILENAME " dans " $WORKDIR

  curl -s $DATAFILE_URL > $WORKDIR/$NEWFILENAME
  # Calcul du checksum du fichier telecharge
  DWN_CHECKSUM=`shasum -a 1 $WORKDIR/$NEWFILENAME | cut -d' ' -f1`
  if [ $DWN_CHECKSUM != $DATAFILE_CHECKSUM ];
    then 
      echo "/!\ Erreur de checksum sur le fichier : "$NEWFILENAME
    else 
      echo "Donnees controlees, checksum OK"
      # MAIL pour prevenir que des donnees sont disponibles 
  fi
else
  # fichier plus ancien
  echo "Fichier distant plus ancien = " $DATAFILE_DATE
fi
