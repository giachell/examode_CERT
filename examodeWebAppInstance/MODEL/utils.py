def sanitize_record(record, use_case):
	"""
	Sanitize record replacing translation errors

	Params:
		record (str): target record

	Returns: the sanitized record
	"""
	if record:
		record = record.replace('octopus', 'polyp')
		if use_case == 'colon':
			record = record.replace('blind', 'cecum')
			record = record.replace('cecal', 'cecum')
			record = record.replace('rectal', 'rectum')
			record = record.replace('proximal colon', 'right colon')
	return record


def sanitize_code(code):
	"""
	Sanitize code removing non necessary characters

	Params:
		code (str): target code

	Returns: the sanitized code
	"""

	if code:
		code = code.replace('-', '')
	return code


def read_rules(rules):
	"""
	Read rules stored within file

	Params: 
		rules (str): path to rules file

	Returns: a dict of trigger: [candidates] representing rules for each use-case
	"""

	with open(rules, 'r') as file:
		lines = file.readlines()

	rules = {'colon': {}, 'cervix': {}, 'celiac': {}, 'lung': {}}
	for line in lines:
		trigger, candidates, position, use_cases = line.strip().split('\t')
		use_cases = use_cases.split(',')
		for use_case in use_cases:
			rules[use_case][trigger] = (candidates.split(','), position)
	return rules


def read_dysplasia_mappings(mappings):
	"""
	Read dysplasia mappings stored within file

	Params:
		mappings (str): path to dysplasia mappings file

	Returns: a dict of trigger: grade representing mappings for each use-case
	"""

	with open(mappings, 'r') as file:
		lines = file.readlines()

	mappings = {'colon': {}, 'cervix': {}, 'celiac': {}, 'lung': {}}
	for line in lines:
		trigger, grade, use_cases = line.strip().split('\t')
		use_cases = use_cases.split(',')
		for use_case in use_cases:
			mappings[use_case][trigger] = grade
	return mappings


def read_hierarchies(hrels):
	"""
	Read hierarchy relations stored within file
	
	Params:
		hrels (str): hierarchy relations file path
		
	Returns: the list of hierarchical relations
	"""
	
	with open(hrels, 'r') as f:
		rels = f.readlines()
	return [rel.strip() for rel in rels]


def convert_concepts2labels(report_concepts):
	"""
	Convert the concepts extracted from reports to the set of pre-defined labels used for classification
	
	Params:
		report_concepts (dict(list)): the dict containing for each report the extracted concepts
		
	Returns: a dict containing for each report the set of pre-defined labels where 0 = abscence and 1 = presence
	"""
	
	report_labels = dict()
	# loop over reports
	for rid, rconcepts in report_concepts.items():
		# assign pre-defined set of labels to current report
		report_labels[rid] = {'cancer': 0, 'adenoma_hg_dysplasia': 0, 'adenoma_lg_dysplasia': 0,'hyperplastic_polyp': 0, 'non_informative': 0}
		# textify diagnosis section
		diagnosis = ' '.join([concept[1].lower() for concept in rconcepts['Diagnosis']])
		# update pre-defined labels w/ 1 in case of label presence
		if ('adenocarcinoma') in diagnosis:  # update 'cancer' label
			report_labels[rid]['cancer'] = 1
		if ('adenoma' and 'mild') in diagnosis:  # update adenoma_lg_dysplasia
			report_labels[rid]['adenoma_lg_dysplasia'] = 1
		if ('adenoma' and 'moderate') in diagnosis:  # update adenoma_lg_dysplasia
			report_labels[rid]['adenoma_lg_dysplasia'] = 1
		if ('adenoma' and 'severe') in diagnosis:  # update adenoma_hg_dysplasia
			report_labels[rid]['adenoma_hg_dysplasia'] = 1
		if ('hyperplastic') in diagnosis:  # update hyperplastic_polyp
			report_labels[rid]['hyperplastic_polyp'] = 1
		if sum(report_labels[rid].values()) == 0:  # update non_informative
			report_labels[rid]['non_informative'] = 1   
	return report_labels


def convert_concepts2binary_labels(report_labels):
	"""
	Convert the pre-defined labels extracted from reports to binary labels used for classification
	
	Params:
		report_labels (dict(list)): the dict containing for each report the pre-defined labels
		
	Returns: a dict containing for each report the set of binary labels where 0 = abscence and 1 = presence
	"""
	
	binary_labels = dict()
	# loop over reports
	for rid, rlabels in report_labels.items():
		# assign binary labels to current report
		binary_labels[rid] = {'cancer_or_adenoma': 0, 'other': 0}
		# update binary labels w/ 1 in case of label presence
		if rlabels['cancer'] == 1 or rlabels['adenoma_lg_dysplasia'] == 1 or rlabels['adenoma_hg_dysplasia'] == 1:  # update 'cancer_or_adenoma' label
			binary_labels[rid]['cancer_or_adenoma'] = 1
		else:  # update 'other' label
			binary_labels[rid]['other'] = 1  
	return binary_labels