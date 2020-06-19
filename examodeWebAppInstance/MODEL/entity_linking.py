import math
import itertools 
import warnings
import json

import utils

from copy import deepcopy
from spacy.tokens import Span

from bionlp import BioNLP 
from ontology_processing import OntologyProc 
from report_processing import ReportProc 
from rdf_processing import RDFProc
from examodeWebAppInstance import bio_proc_init


warnings.filterwarnings('ignore')

# NOTE: private data are replaced with asterisks ***


class EL(object):
	"""build class to perform Entity Linking through REST API"""

	def __init__(self, use_case='colon'):

		# store use_case
		self.use_case = use_case
		# set required class instances
		self.exa_onto = OntologyProc(ontology_path='***/MODEL/ontology/examode.owl', hiearchies_path='***/MODEL/hierarchy_relations.txt')
		self.report_proc = ReportProc()
		self.bio_proc = bio_proc_init
		self.rdf_proc = RDFProc()

		# restrict ontology to the considered use-case
		self.exa_usecase = self.exa_onto.restrict2use_case(self.use_case)
		# pre-process concept labels for the considered use-case
		self.labels = self.bio_proc.process_ontology_concepts(labels=[label.lower() for label in self.exa_usecase['label'].tolist()])
		# restrict hand-crafted rules and dysplasia mappings based on considered use-case
		self.bio_proc.restrict2use_case(self.use_case)

	def perform_linking_and_serialization(self, report, output='stream', rdf_format='turtle'):
		"""
        Perform entity linking over target report and return serialized graph

        Params:
          report (dict): target report {'diagnosis': <string>, 'materials': <string>, 'codes': <list>, 'age': <string>, 'gender': <string>}
          output (str): output path of the serialized graph - if output == 'stream' --> return streamed output
          rdf_format (str): rdf serialization format

        Returns: the serialized rdf graph
        """

		# perform entity linking over target report
		concepts = self.bio_proc.online_entity_linking(report, self.exa_onto, self.labels, self.use_case,
													   self.exa_usecase)
		# convert report data and concepts into rdf and serialize into rdf_format
		graph = self.rdf_proc.create_graph(report, concepts, self.exa_onto, self.use_case)
		# serialize graph into rdf using specified format
		if output == 'stream':  # stream concepts and created graph
			return concepts, self.rdf_proc.searialize_report_graphs([graph], output, rdf_format)
		else:  # store created graph within output file
			with open(output + '_concepts.json', 'w') as out:
				json.dump(concepts, out)
			self.rdf_proc.searialize_report_graphs([graph], output + '_graph.' + rdf_format, rdf_format)
			return True
