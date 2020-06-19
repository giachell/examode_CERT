import hashlib

from rdflib import URIRef, Literal, Graph


class RDFProc(object):

	def __init__(self):  # @smarchesin TODO: add Test outcome to predicate2literal list
		"""
		Set namespaces and properties w/ Literals as objects

		Params:
		
		Returns: None
		"""

		# set namespaces
		self.namespace = {'exa': 'https://w3id.org/examode/', 'dc': 'http://purl.org/dc/elements/1.1/'}
		self.gender = {'M': 'http://purl.obolibrary.org/obo/NCIT_C46109', 'F': 'http://purl.obolibrary.org/obo/NCIT_C46110'}
		self.predicate2literal = [self.namespace['dc'] + 'identifier', self.namespace['exa'] + 'ontology#hasDiagnosis', self.namespace['exa'] + 'ontology#hasAge', self.namespace['exa'] + 'ontology#hasGender']

	
	### COMMON FUNCTIONS ###


	def associate_polyp2dysplasia(self, outcomes, mask_outcomes):  # @smarchesin TODO: this function will be part of a dict of functions that are disease dependants
		"""
		Associate polyp-type outcomes w/ dysplasia mentions (colon-related function)
		
		Params:
			outcomes (list(pair(str))): the list of report outcomes
			mask_outcomes (list(int)): the list of masked outcomes - 0 for dysplasia and 1 for Outcome subclasses
		
		Returns: a list of associated polyp-dysplasia pairs, when possible, or single polyp mentions
		"""
		
		pairs = list()
		if len(mask_outcomes) == 1:  # there is one outcome only 
			if mask_outcomes[0] == 1:  # the outcome is subclass of Outcome class
				pairs.append([outcomes[0][0]])
				return pairs
			else:  # @smarchesin TODO: the outcome is a dysplasia mention - append it w/ the general 'Polyp of Colon' concept? 
				print('unexpected dysplasia mention')
				pairs.append(['http://purl.obolibrary.org/obo/MONDO_0021400', outcomes[0][0]])
				return pairs
			
		for ix, i in enumerate(mask_outcomes):  # there are multiple outcomes
			if ix == 0:  # first outcome
				if i == 0:  # first outcome is a dysplasia mention
					if mask_outcomes[ix+1] == 1:  # second outcome is sublcass of Outcome class - store the pair
						pairs.append([outcomes[ix+1][0], outcomes[ix][0]])
					else:  # @smarchesin TODO: the outcome is a dysplasia mention - append it w/ the general 'Polyp of Colon' concept?
						print('unexpected dysplasia mention')
						pairs.append(['http://purl.obolibrary.org/obo/MONDO_0021400', outcomes[ix][0]])
				if i == 1:  # first outcome is subclass of Outcome class
					if mask_outcomes[ix+1] == 0:  # the second outcome is a dysplasia mention
						pairs.append([outcomes[ix][0], outcomes[ix+1][0]])
					else:  # the second outcome is another subclass of Outcome class
						pairs.append([outcomes[ix][0]])
			else:
				# get list of outcomes previously stored
				previous = [concept for pair in pairs for concept in pair]
				if outcomes[ix][0] in previous:  # the outcome has been already associated
					continue
				if i == 0:  # the outcome is a dysplasia mention
					if outcomes[ix-1][0] in previous:  # look for subsequent outcomes
						if ix+1 == len(mask_outcomes):  # @smarchesin TODO: the outcome is a dysplasia mention - append it w/ the general 'Polyp of Colon' concept?
							print('unexpected dysplasia mention')
							pairs.append(['http://purl.obolibrary.org/obo/MONDO_0021400', outcomes[ix][0]])
						elif mask_outcomes[ix+1] == 1:
							pairs.append([outcomes[ix+1][0], outcomes[ix][0]])
						else:
							print('unexpected dysplasia mention')
					else:  # look for previous outcomes
						if mask_outcomes[ix-1] == 1:
							pairs.append([outcomes[ix-1][0], outcomes[ix][0]])
						else:  # @smarchesin TODO: the outcome is a dysplasia mention - append it w/ the general 'Polyp of Colon' concept?
							print('unexpected dysplasia mention')
							pairs.append(['http://purl.obolibrary.org/obo/MONDO_0021400', outcomes[ix][0]])
				if i == 1:  # the outcome is subclass of Outcome class
					if outcomes[ix-1][0] in previous:  # look for subsequent outcomes
						if ix+1 == len(mask_outcomes): 
							pairs.append([outcomes[ix][0]])
						elif mask_outcomes[ix+1] == 0:
							pairs.append([outcomes[ix][0], outcomes[ix+1][0]])
						else:
							pairs.append([outcomes[ix][0]])
					else:  # look for previous outcomes
						if mask_outcomes[ix-1] == 0:
							pairs.append([outcomes[ix][0], outcomes[ix-1][0]])
						else:
							pairs.append([outcomes[ix][0]])
		return pairs

	def searialize_report_graphs(self, graphs, output='stream', rdf_format='turtle'):
		"""
		Serialize report graphs into rdf w/ specified format

		Params:
			graphs (list(list(tuple))/list(tuple)): report graphs to be serialized
			output (str): output path of the serialized graph - if output == 'stream' --> return streamed output
			rdf_format (str): rdf serialization format

		Returns: the serialized rdf graph
		"""

		g = Graph()
		# bind namespaces to given prefix
		for px, ns in self.namespace.items():
			g.bind(px, ns, override=True)
		# loop over graphs and convert them into rdflib classes
		for graph in graphs:
			for triple in graph:
				s = URIRef(triple[0])
				p = URIRef(triple[1])
				if triple[1] in self.predicate2literal:
					o = Literal(triple[2])
				else:
					o = URIRef(triple[2])
				g.add((s, p, o))
		if output == 'stream':  # stream rdf graph to output 
			# serialize graphs into predefined rdf format
			return g.serialize(format=rdf_format)
		else:  # store rdf graph to file
			# serialize graphs into predefined rdf format
			g.serialize(destination=output, format=rdf_format)
			print('rdf graph serialized to {} with {} format'.format(output, rdf_format))
			return True

	def create_graph(self, report_data, report_concepts, onto_proc, use_case):
		"""
		Create rdf report graph out of extracted concepts
		
		Params:
			rid (str): the report id
			report_data (dict): the target report data
			report_concepts (dict): the concepts extracted from the target report
			onto_proc (OntologyProc): instance of OntologyProc class
			use_case (str): the use_case considered - i.e. colon, lung, cervix, or celiac
		
		Returns: a list of (s, p, o) triples representing report data in rdf
		"""
		
		graph = list()

		# sanity check 
		if not report_data['diagnosis']:  # textual diagnosis is not present within report data
			print('you must fill the diagnosis field.')
			return False
		
		# generate report id hashing 'diagnosis' field
		rid = hashlib.md5(report_data['diagnosis'].encode()).hexdigest()

		## create report data-related triples

		# build the IRI for the resource
		resource = self.namespace['exa'] + 'resource/'
		# build the IRI for the given report
		report = resource + 'report/' + rid.replace('/', '_')
		# generate report data-related triples
		graph.append((report, 'a', self.namespace['exa'] + 'ontology#' + use_case.capitalize() + 'ClinicalCaseReport'))
		graph.append((report, self.namespace['dc'] + 'identifier', report))  # @smarchesin: we set report , dc:identifier, report - isn't is a little bit redundant?
		graph.append((report, self.namespace['exa'] + 'ontology#hasDiagnosis', report_data['diagnosis']))
		if report_data['age']:  # age data is present within report_data
			graph.append((report, self.namespace['exa'] + 'ontology#hasAge', report_data['age']))
		if report_data['gender']:  # gender data is present within report_data
			if report_data['gender'].lower() == 'm' or 'male':
				graph.append((report, self.namespace['exa'] + 'ontology#hasGender', self.gender['M']))
			elif report_data['gender'].lower() == 'f' or 'female':
				graph.append((report, self.namespace['exa'] + 'ontology#hasGender', self.gender['F']))
			else:
				print('mispelled gender: put M/F or MALE/FEMALE.')

		## create report concept-related triples

		# set ontology 'Outcome' IRI to identify its descendants within the 'Diagnosis' section
		ontology_outcome = 'http://purl.obolibrary.org/obo/NCIT_C20200'
		# set ontology 'Polyp' IRI to identify its descendants within the 'Diagnosis' section
		ontology_polyp = 'http://purl.obolibrary.org/obo/MONDO_0021400'

		# identify report procedures
		report_procedures = [procedure[0] for procedure in report_concepts['Procedure']]
		# identify report anatomical locations
		report_locations = [location[0] for location in report_concepts['Anatomical Location']]
		if not report_locations:  # add 'Colon, NOS' IRI as default
			report_locations += ['http://purl.obolibrary.org/obo/UBERON_0001155']
		# identify report tests
		report_tests = [test[0] for test in report_concepts['Test']]
		# identify report outcomes
		report_outcomes = [(diagnosis[0], onto_proc.get_higher_concept(iri1=diagnosis[0], iri2=ontology_outcome)) for diagnosis in report_concepts['Diagnosis']]
		# identify report polyps
		report_polyps = [(diagnosis[0], onto_proc.get_higher_concept(iri1=diagnosis[0], iri2=ontology_polyp, include_self=True)) for diagnosis in report_concepts['Diagnosis']]
		# restrict report_outcomes to those polyp-related and mask concepts that are sublcass of Polyp w/ 1 and 0 otherwise (dysplasia-related concepts)
		for ix, (outcome, polyp) in enumerate(zip(report_outcomes, report_polyps)):
			if (outcome[1] is not None) and (polyp[1] is None):  # non-polyp outcome
				report_polyps.pop(ix)
			elif (outcome[1] is not None) and (polyp[1] is not None):  # polyp outcome
				report_outcomes.pop(ix)
			else:  # dysplasia outcome
				report_outcomes.pop(ix)
		# mask report_polyps w/ 1 for concepts that are subclass of Polyp and 0 for other 
		masked_outcomes = [0 if report_outcome[1] is None else 1 for report_outcome in report_polyps]
		# associate polyp-related mentions w/ dysplasia ones - restricted to colon disease only
		paired_outcomes = self.associate_polyp2dysplasia(report_polyps, masked_outcomes)
		# concatenate the non-polyp outcomes to paired_outcomes
		paired_outcomes += [[outcome[0]] for outcome in report_outcomes]
		# set the counter for outcomes identified from report
		report_outcome_n = 0
		# loop over outcomes and build 'Outcome'-related triples
		for pair in paired_outcomes:
			# increase outcomes counter
			report_outcome_n += 1

			## 'Diagnosis'-related triples

			# build the IRI for the identified outcome
			resource_outcome = resource + rid.replace('/', '_') + '/' + str(report_outcome_n)
			# attach outcome instance to graph
			graph.append((report, self.namespace['exa'] + 'ontology#hasOutcome', resource_outcome))
			# specify what the resource_outcome is
			graph.append((resource_outcome, 'a', pair[0]))
			if len(pair) == 2:  # target outcome has associated dysplasia
				# specify the associated dysplasia
				graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasDysplasia', pair[1]))

			## 'Anatomical'-related triples

			# specificy the anatomical location associated to target outcome
			for location in report_locations:  # @smarchesin TODO: is it correct? in this way we can associate multiple locations to the same outcome
				graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasLocation', location))

			## 'Procedure'-related triples

			# loop over procedures and build 'Procedure'-related triples
			for ix, procedure in enumerate(report_procedures):  # @smarchesin TODO: is it correct? in this way we can associate the same procedure to multiple outcomes
				# build the IRI for the identified procedure
				resource_procedure = resource + 'procedure/'+ rid.replace('/', '_') + '/' + str(report_outcome_n) + '.' + str(ix+1)
				# attach procedure instance to graph
				graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasIntervention', resource_procedure))
				# specify what the resource_procedure is
				graph.append((resource_procedure, 'a', procedure))
				# specify the anatomical location associated to target procedure
				for location in report_locations:  # @smarchesin TODO: is it correct? in this way we can associate multiple locations to the same procedure
					graph.append((resource_procedure, self.namespace['exa'] + 'ontology#hasTopography', location))

			## 'Test'-related triples - @smarchesin TODO: decide how to handle tests in colon

		# return report rdf graph
		return graph


	### AOEC SPECIFIC FUNCTIONS ###


	def aoec_create_graph(self, rid, report_data, report_concepts, onto_proc, use_case):
		"""
		Create the AOEC rdf report graph out of extracted concepts
		
		Params:
			rid (str): the report id
			report_data (dict): the target report data
			report_concepts (dict): the concepts extracted from the target report
			onto_proc (OntologyProc): instance of OntologyProc class
			use_case (str): the use_case considered - i.e. colon, lung, cervix, or celiac
		
		Returns: a list of (s, p, o) triples representing report data in rdf
		"""
		
		graph = list()
		
		## create report data-related triples

		# build the IRI for the resource
		resource = self.namespace['exa'] + 'resource/'
		# build the IRI for the given report
		report = resource + 'report/' + rid.replace('/', '_')
		# generate report data-related triples
		graph.append((report, 'a', self.namespace['exa'] + 'ontology#' + use_case.capitalize() + 'ClinicalCaseReport'))
		graph.append((report, self.namespace['dc'] + 'identifier', rid))
		if report_data['diagnosis_nlp']:  # textual diagnosis is present within report data
			graph.append((report, self.namespace['exa'] + 'ontology#hasDiagnosis', report_data['diagnosis_nlp']))
		if report_data['age']:  # age data is present within report_data
			graph.append((report, self.namespace['exa'] + 'ontology#hasAge', report_data['age']))
		if report_data['gender']:  # gender data is present within report_data
			graph.append((report, self.namespace['exa'] + 'ontology#hasGender', self.gender[report_data['gender']]))

		## create report concept-related triples

		# set ontology 'Outcome' IRI to identify its descendants within the 'Diagnosis' section
		ontology_outcome = 'http://purl.obolibrary.org/obo/NCIT_C20200'
		# set ontology 'Polyp' IRI to identify its descendants within the 'Diagnosis' section
		ontology_polyp = 'http://purl.obolibrary.org/obo/MONDO_0021400'

		# identify report procedures
		report_procedures = [procedure[0] for procedure in report_concepts['Procedure']]
		# identify report anatomical locations
		report_locations = [location[0] for location in report_concepts['Anatomical Location']]
		if not report_locations:  # add 'Colon, NOS' IRI as default
			report_locations += ['http://purl.obolibrary.org/obo/UBERON_0001155']
		# identify report tests
		report_tests = [test[0] for test in report_concepts['Test']]
		# identify report outcomes
		report_outcomes = [(diagnosis[0], onto_proc.get_higher_concept(iri1=diagnosis[0], iri2=ontology_outcome)) for diagnosis in report_concepts['Diagnosis']]
		# identify report polyps
		report_polyps = [(diagnosis[0], onto_proc.get_higher_concept(iri1=diagnosis[0], iri2=ontology_polyp, include_self=True)) for diagnosis in report_concepts['Diagnosis']]
		# restrict report_outcomes to those polyp-related and mask concepts that are sublcass of Polyp w/ 1 and 0 otherwise (dysplasia-related concepts)
		for ix, (outcome, polyp) in enumerate(zip(report_outcomes, report_polyps)):
			if (outcome[1] is not None) and (polyp[1] is None):  # non-polyp outcome
				report_polyps.pop(ix)
			elif (outcome[1] is not None) and (polyp[1] is not None):  # polyp outcome
				report_outcomes.pop(ix)
			else:  # dysplasia outcome
				report_outcomes.pop(ix)
		# mask report_polyps w/ 1 for concepts that are subclass of Polyp and 0 for other 
		masked_outcomes = [0 if report_outcome[1] is None else 1 for report_outcome in report_polyps]
		# associate polyp-related mentions w/ dysplasia ones - restricted to colon disease only
		paired_outcomes = self.associate_polyp2dysplasia(report_polyps, masked_outcomes)
		# concatenate the non-polyp outcomes to paired_outcomes
		paired_outcomes += [[outcome[0]] for outcome in report_outcomes]
		# set the counter for outcomes identified from report
		report_outcome_n = 0
		# loop over outcomes and build 'Outcome'-related triples
		for pair in paired_outcomes:
			# increase outcomes counter
			report_outcome_n += 1

			## 'Diagnosis'-related triples

			# build the IRI for the identified outcome
			resource_outcome = resource + rid.replace('/', '_') + '/' + str(report_outcome_n)
			# attach outcome instance to graph
			graph.append((report, self.namespace['exa'] + 'ontology#hasOutcome', resource_outcome))
			# specify what the resource_outcome is
			graph.append((resource_outcome, 'a', pair[0]))
			if len(pair) == 2:  # target outcome has associated dysplasia
				# specify the associated dysplasia
				graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasDysplasia', pair[1]))

			## 'Anatomical'-related triples

			# specificy the anatomical location associated to target outcome
			for location in report_locations:  # @smarchesin TODO: is it correct? in this way we can associate multiple locations to the same outcome
				graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasLocation', location))

			## 'Procedure'-related triples

			# loop over procedures and build 'Procedure'-related triples
			for ix, procedure in enumerate(report_procedures):  # @smarchesin TODO: is it correct? in this way we can associate the same procedure to multiple outcomes
				# build the IRI for the identified procedure
				resource_procedure = resource + 'procedure/'+ rid.replace('/', '_') + '/' + str(report_outcome_n) + '.' + str(ix+1)
				# attach procedure instance to graph
				graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasIntervention', resource_procedure))
				# specify what the resource_procedure is
				graph.append((resource_procedure, 'a', procedure))
				# specify the anatomical location associated to target procedure
				for location in report_locations:  # @smarchesin TODO: is it correct? in this way we can associate multiple locations to the same procedure
					graph.append((resource_procedure, self.namespace['exa'] + 'ontology#hasTopography', location))

			## 'Test'-related triples - @smarchesin TODO: decide how to handle tests in colon

		# return report rdf graph
		return graph


	### RADBOUD SPECIFIC FUNCTIONS ###


	def radboud_create_graph(self, rid, report_data, report_concepts, onto_proc, use_case):
		"""
		Create the Radboud rdf report graph out of extracted concepts

		Params:
			rid (str): the report id
			report_data (dict): the target report data
			report_concepts (dict): the concepts extracted from the target report
			onto_proc (OntologyProc): instance of OntologyProc class
			use_case (str): the use_case considered - i.e. colon, lung, cervix, or celiac

		Returns: a list of (s, p, o) triples representing report data in rdf
		"""

		graph = list()

		## create report data-related triples

		# build the IRI for the resource
		resource = self.namespace['exa'] + 'resource/'
		# build the IRI for the given report
		report = resource + 'report/' + rid.replace('/', '_')
		# generate report data-related triples
		graph.append((report, 'a', self.namespace['exa'] + 'ontology#' + use_case.capitalize() + 'ClinicalCaseReport'))
		graph.append((report, self.namespace['dc'] + 'identifier', rid))
		# concatenate diagnoses to store them as a single field
		diagnoses = ' '.join([diagnosis for field, diagnosis in report_data.items() if 'diagnosis' in field]).strip()
		if diagnoses:  # textual diagnosis is present within report data
			graph.append((report, self.namespace['exa'] + 'ontology#hasDiagnosis', diagnoses))

		## create report concept-related triples

		# set ontology 'Outcome' IRI to identify its descendants within the 'Diagnosis' section
		ontology_outcome = 'http://purl.obolibrary.org/obo/NCIT_C20200'
		# set ontology 'Polyp' IRI to identify its descendants within the 'Diagnosis' section
		ontology_polyp = 'http://purl.obolibrary.org/obo/MONDO_0021400'

		# loop over the different diagnoses of the given report and treat each diagnosis as a separate case to associate w/ the report
		for dix, diagnosis_data in enumerate(report_concepts.values()): 
			# identify report procedures
			report_procedures = [procedure[0] for procedure in diagnosis_data['Procedure']]
			# identify report anatomical locations
			report_locations = [location[0] for location in diagnosis_data['Anatomical Location']]
			if not report_locations:  # add 'Colon, NOS' IRI as default
				report_locations += ['http://purl.obolibrary.org/obo/UBERON_0001155']
			# identify report tests
			report_tests = [test[0] for test in diagnosis_data['Test']]
			# identify report outcomes
			report_outcomes = [(diagnosis[0], onto_proc.get_higher_concept(iri1=diagnosis[0], iri2=ontology_outcome)) for diagnosis in diagnosis_data['Diagnosis']]
			# identify report polyps
			report_polyps = [(diagnosis[0], onto_proc.get_higher_concept(iri1=diagnosis[0], iri2=ontology_polyp, include_self=True)) for diagnosis in diagnosis_data['Diagnosis']]
			# restrict report_outcomes to those polyp-related and mask concepts that are sublcass of Polyp w/ 1 and 0 otherwise (dysplasia-related concepts)
			for ix, (outcome, polyp) in enumerate(zip(report_outcomes, report_polyps)):
				if (outcome[1] is not None) and (polyp[1] is None):  # non-polyp outcome
					report_polyps.pop(ix)
				elif (outcome[1] is not None) and (polyp[1] is not None):  # polyp outcome
					report_outcomes.pop(ix)
				else:  # dysplasia outcome
					report_outcomes.pop(ix)
			# mask report_polyps w/ 1 for concepts that are subclass of Polyp and 0 for other 
			masked_outcomes = [0 if report_outcome[1] is None else 1 for report_outcome in report_polyps]
			# associate polyp-related mentions w/ dysplasia ones - restricted to colon disease only
			paired_outcomes = self.associate_polyp2dysplasia(report_polyps, masked_outcomes)
			# concatenate the non-polyp outcomes to paired_outcomes
			paired_outcomes += [[outcome[0]] for outcome in report_outcomes]
			# set the counter for outcomes identified from report
			report_outcome_n = 0
			# loop over outcomes and build 'Outcome'-related triples
			for pair in paired_outcomes:
				# increase outcomes counter
				report_outcome_n += 1

				## 'Diagnosis'-related triples

				# build the IRI for the identified outcome
				resource_outcome = resource + rid.replace('/', '_') + '/' + str(dix+1) + '/' + str(report_outcome_n)
				# attach outcome instance to graph
				graph.append((report, self.namespace['exa'] + 'ontology#hasOutcome', resource_outcome))
				# specify what the resource_outcome is
				graph.append((resource_outcome, 'a', pair[0]))
				if len(pair) == 2:  # target outcome has associated dysplasia
					# specify the associated dysplasia
					graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasDysplasia', pair[1]))

				## 'Anatomical'-related triples

				# specificy the anatomical location associated to target outcome
				for location in report_locations:  # @smarchesin TODO: is it correct? in this way we can associate multiple locations to the same outcome
					graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasLocation', location))

				## 'Procedure'-related triples

				# loop over procedures and build 'Procedure'-related triples
				for ix, procedure in enumerate(report_procedures):  # @smarchesin TODO: is it correct? in this way we can associate the same procedure to multiple outcomes
					# build the IRI for the identified procedure
					resource_procedure = resource + 'procedure/'+ rid.replace('/', '_') + '/' + str(dix+1) + '/' + str(report_outcome_n) + '.' + str(ix+1)
					# attach procedure instance to graph
					graph.append((resource_outcome, self.namespace['exa'] + 'ontology#hasIntervention', resource_procedure))
					# specify what the resource_procedure is
					graph.append((resource_procedure, 'a', procedure))
					# specify the anatomical location associated to target procedure
					for location in report_locations:  # @smarchesin TODO: is it correct? in this way we can associate multiple locations to the same procedure
						graph.append((resource_procedure, self.namespace['exa'] + 'ontology#hasTopography', location))

				## 'Test'-related triples - @smarchesin TODO: decide how to handle tests in colon

		# return report rdf graph
		return graph