import spacy
import textdistance
import statistics
import itertools
import operator
import re
import pickle
import os
import sys
import en_core_sci_lg

# NOTE: private data are replaced with asterisks ***

sys.path.insert(0, '***/MODEL')

import utils

from tqdm import tqdm
from collections import Counter
from spacy.tokens import Span
from negspacy.negation import Negex
from scispacy.umls_linking import UmlsEntityLinker
from scispacy.abbreviation import AbbreviationDetector
from sklearn.metrics.pairwise import cosine_similarity
from bionlp import BioNLP

bio_proc_init = BioNLP(biospacy="en_core_sci_lg", rules='***/MODEL/rules.txt', dysplasia_mappings='***/MODEL/dysplasia_mappings.txt', dict_path='***/MODEL/spell_suggestions/en_US.dic', aff_path='***/MODEL/spell_suggestions/en_US.aff')
