import sys
import json
import datetime
import requests
import codecs
import logging
import os.path


def _getLogger(name):
    """
        Helper function to configure a logger
    :param name: name of the logger
    :return: instance of a logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


# http://localhost:9200/finess/_count?q=updated:2016-06-08
class Finess:
    """
        Finess data Parser

        Schema definition based on
        https://www.data.gouv.fr/s/resources/extraction-du-fichier-national-des-etablissements-sanitaires-et-sociaux-finess-par-etablissements/20151222-100753/etalab_cs1100502.pdf
    """

    def __init__(self):
        self.logger = _getLogger(self.__class__.__name__)

        self.finess_sch = [
            {"desc": "structureet", "title": "structureet", "min": 11, "max": 11, "nillable": False},
            {"desc": "Numero FINESS ET", "title": "nofinesset", "min": 9, "max": 9, "nillable": False},
            {"desc": "Numero FINESS EJ", "title": "nofinessej", "min": 9, "max": 9, "nillable": False},
            {"desc": "Raison sociale", "title": "rs", "min": 1, "max": 38, "nillable": False},
            {"desc": "Raison sociale longue", "title": "rslongue", "min": 1, "max": 60, "nillable": True},
            {"desc": "Complement de raison sociale", "title": "complrs", "min": 1, "max": 32, "nillable": True},
            {"desc": "Complement de distribution", "title": "compldistrib", "min": 1, "max": 32, "nillable": True},
            {"desc": "Numero de voie", "title": "numvoie", "min": 1, "max": 4, "nillable": True},
            {"desc": "Type de voie", "title": "typvoie", "min": 1, "max": 4, "nillable": True},
            {"desc": "Libelle de voie", "title": "voie", "min": 1, "max": 27, "nillable": True},
            {"desc": "Complement de voie", "title": "compvoie", "min": 1, "max": 1, "nillable": True},
            {"desc": "Lieu-dit / BP", "title": "lieuditbp", "min": 1, "max": 32, "nillable": True},
            {"desc": "Code Commune", "title": "commune", "min": 3, "max": 3, "nillable": True},
            {"desc": "Departement", "title": "departement", "min": 2, "max": 2, "nillable": False},
            {"desc": "Libelle departement", "title": "libdepartement", "min": 1, "max": 24, "nillable": False},
            {"desc": "Ligne d'acheminement (CodePostal+Lib commune)", "title": "ligneacheminement", "min": 1,
             "max": 26, "nillable": False},
            {"desc": "Telephone", "title": "telephone", "min": 10, "max": 10, "nillable": True},
            {"desc": "Telecopie", "title": "telecopie", "min": 10, "max": 10, "nillable": True},
            {"desc": "Categorie d'etablissement", "title": "categetab", "min": 3, "max": 3, "nillable": False},
            {"desc": "Libelle categorie d'etablissement", "title": "libcategetab", "min": 1, "max": 60, "nillable": True},
            {"desc": "Categorie d'agregat d'etablissement", "title": "categagretab", "min": 4, "max": 4, "nillable": False},
            {"desc": "Libelle categorie d'agregat d'etablissement", "title": "libcategagretab", "min": 1, "max": 60, "nillable": True},
            {"desc": "Numero de SIRET", "title": "siret", "min": 14, "max": 14, "nillable": True},
            {"desc": "Code APE", "title": "codeape", "min": 5, "max": 5, "nillable": True},
            {"desc": "Code MFT", "title": "codemft", "min": 2, "max": 2, "nillable": True},
            {"desc": "Libelle MFT", "title": "libmft", "min": 1, "max": 60, "nillable": True},
            {"desc": "Code SPH", "title": "codesph", "min": 1, "max": 1, "nillable": True},
            {"desc": "Libelle SPH", "title": "libsph", "min": 1, "max": 60, "nillable": True},
            {"desc": "Date d'ouverture", "title": "dateouv", "min": 10, "max": 10, "nillable": True},
            {"desc": "Date d'autorisation", "title": "dateautor", "min": 10, "max": 10, "nillable": True},
            {"desc": "Date de mise a jour sur la structure", "title": "datemaj", "min": 10, "max": 10, "nillable": False},
            {"desc": "Numero education nationale", "title": "numuai", "min": 8, "max": 8, "nillable": True}
        ]
        self.mapping = {'finess': (1, None),
                        'name': (3, None), 'cp': (16, self.cutzipcode), 'dept': (16, self.cutdept),
                        'city': (15, self.cutcity), 'opened': (28, None),
                        'updated': (30, None)
                        }
        self.entities = {}
        self.errors_checked = {}
        self.empty_checked = {}

        for i in range(len(self.finess_sch)):
            self.errors_checked[i] = dict(count=0, finess=[])
            self.empty_checked[i] = 0

    def cutzipcode(self, data):
        return data[:5]

    def cutdept(self, data):
        return data[:2]

    def cutcity(self, data):
        return data[6:].replace('CEDEX', '').strip()

    def convertodate(self, data):
        return datetime.datetime.strptime(data, '%Y-%m-%d')

    def checkdata(self, data):
        """
            Check data Validity, against the schema definition

        :param data: data to check
        :return: _
        """
        for i, v in enumerate(data):
            # get definition
            defsch = self.finess_sch[i]
            value = v.strip()
            if len(value) == 0:
                self.empty_checked[i] += 1
                if not defsch["nillable"]:
                    self.errors_checked[i]["count"] += 1
                    self.errors_checked[i]["finess"].append(data[1])
            else:
                if len(value)<defsch["min"] or len(value)>defsch["max"]:
                    self.errors_checked[i]["count"] += 1
                    self.errors_checked[i]["finess"].append(data[1])

    def createCard(self, data):
        """
            Create an info card based on all available data
        :param data: all data
        :return: needed data
        """
        newcard = {}
        for k, v in self.mapping.items():
            (index, func) = v
            newcard[k] = func(data[index]) if func else data[index]
        return newcard

    def load_data(self, filename):
        """
            Load data file. Parse it, and create entities

        :param filename: name of the file
        :return:
        """

        assert os.path.exists(filename), "Filename {} doesn't existst".format(filename)

        self.logger.info("Parse data file : {}".format(filename))
        with codecs.open(filename, 'r', 'latin1') as fin:
            for line in fin.readlines()[1:]:
                data = line.split(';')
                self.checkdata(data)
                card = self.createCard(data)
                if card['finess'] in self.entities:
                    self.logger.error("Finess already exists : {}".format(card['finess']))
                else:
                    self.entities[card['finess']] = card

        self.logger.info("Entites count = {}".format(len(self.entities.keys())))

    def log_errors(self):
        """
            Log all the errors checked during parsing
        :return: _
        """

        self.logger.info("Error values : ")
        total_entities = float(len(self.entities.keys()))

        for k, v in self.errors_checked.items():
            if v["count"]>0:
                self.logger.info(
                    "Col {0:2d} -> {1:13s} = {2:32s} (min={3:2d}, max={4:2d}) : {5:8d} errors = {6:02.2f}%".format(
                        k, self.finess_sch[k]["title"], self.finess_sch[k]["desc"],
                        self.finess_sch[k]["min"], self.finess_sch[k]["max"],
                        v["count"], (float(v["count"])/total_entities * 100)
                    ))
                self.logger.info("\tEx : {}".format(v["finess"][:3]))


    def log_empty_values(self):
        """
            Log informations on empty values
        :return: _
        """
        self.logger.info("Empty values : ")
        total_entities = float(len(self.entities.keys()))

        for k,v in self.empty_checked.items():
            if v > 0:
                self.logger.info(
                   "Col {0:2d} -> {1:13s} = {2:32s} : {3:8d} empty values = {4:02.2f}%".format(
                        k, self.finess_sch[k]["title"], self.finess_sch[k]["desc"],
                        v, (float(v) / total_entities * 100) ))


class FinessStore():
    """
        Store where data are pushed. ElasticSearch is used here.
        Index = finess
        Type document : et

    """

    def __init__(self):
        self.logger = _getLogger(self.__class__.__name__)

        self.es_url = "http://localhost:9200"
        self.es_index = "finess"
        self.es_typedoc = "et"
        self.es_init()

    def es_put(self, _id, doc):
        """
            Insert document in ElasticSearch

        :param _id: document ID
        :param doc: document to store
        :return: _
        """
        self.logger.debug('Document => {}'.format(doc))
        if not doc:
            self.logger.info("Publising {0}/{1}".format(self.es_url, self.es_index))
            req = requests.put("{0}/{1}".format(self.es_url, self.es_index))
            if req.status_code > 299:
                self.logger.error(
                    " Error {0}: index={1} typedoc={2}".format(req.status_code, self.es_index, self.es_typedoc))
        else:
            self.logger.debug("Publising {0}/{1}/{2}/{3}".format(self.es_url, self.es_index, self.es_typedoc, _id))
            req = requests.post("{0}/{1}/{2}/{3}".format(self.es_url, self.es_index, self.es_typedoc, _id),
                                json.dumps(doc).encode('UTF-8'))
            if req.status_code > 299:
                self.logger.error(
                    " Error {0}: index={1} typedoc={2} id={3}".format(req.status_code, self.es_index, self.es_typedoc,
                                                                      _id))
                self.logger.error(req.text)

    def es_init(self):
        """
            Init data store
        :return: _
        """
        self.logger.info("Create ElasticSearch Index : {}".format(self.es_index))
        self.es_put(None, None)

    def store(self, entities):
        """
            Store all entities in ElasticSearch

        :param entities: data entites
        :return:
        """
        count = 0
        for finess, etab in entities.items():
            self.es_put(finess, etab)
            count += 1
            if count%10000 == 0:
            	self.logger.info("\t{} documents in ElasticSearch".format(count))


if __name__ == "__main__":
    assert len(sys.argv) == 2, "data file must be provided as argument"
    fi = Finess()
    fi.load_data(sys.argv[1])
    fi.log_errors()
    fi.log_empty_values()

    fs = FinessStore()
    fs.store(fi.entities)
