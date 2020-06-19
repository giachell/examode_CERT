from entity_linking import EL
import time
start_time = time.time()
el = EL(use_case='colon')
result = el.perform_linking_and_serialization(report={'diagnosis': "tubular adenoma with high-grade dysplasia.",
                                             'materials': "",
                                             'codes': [],
                                             'gender': "M",
                                             'age': "27"},
                                     output='stream',
                                     rdf_format='turtle')
print("Program take: %s seconds to be executed." % (time.time() - start_time))
print(result)