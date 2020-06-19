from django.shortcuts import render
from django.utils.encoding import smart_str
from django.http import HttpResponse
from django.http import JsonResponse
from examodeWebAppInstance import bio_proc_init
import sys
import os
import requests as req


# NOTE: private data are replaced with asterisks ***

sys.path.insert(0, '***/MODEL')
import entity_linking
import time


# ExaMode CERT views here.

def index(request):
    """Home page of 'examodeWebAppInstance' app of 'examodeWebApp' project"""
    return render(request, 'examodeWebAppInstance/index.html')


def getReport(request):
    """Return the report for a given request"""

    diagnosis = request.POST.get("diagnosis", "")
    materials = request.POST.get("materials", "")
    snomed_code_procedure = request.POST.get("snomed_code_procedure", "")
    snomed_code_topography = request.POST.get("snomed_code_topography", "")
    snomed_code_diagnosis = request.POST.get("snomed_code_diagnosis", "")
    codes = []
    csrfmiddlewaretoken = request.POST.get("csrfmiddlewaretoken", "")
    recaptcha_token = request.POST.get("token", "")

    result = req.post('https://www.google.com/recaptcha/api/siteverify', data = {'secret': '***', 'response': recaptcha_token})

    if result.status_code != 200:
        return JsonResponse({"error":"Error in validating captcha"})

    response_JSON = result.json()

    print(response_JSON)

    if response_JSON["success"]:

        if snomed_code_procedure != "" and snomed_code_topography != "" and snomed_code_diagnosis != "":
            codes = [snomed_code_procedure, snomed_code_topography, snomed_code_diagnosis]

        print(codes)

        gender = request.POST.get("gender", "")
        age = request.POST.get("age", "")
        rdf_format = request.POST.get("rdf_format", "turtle")
        notes = request.POST.get("notes", "")

        filename = "report_"+csrfmiddlewaretoken
        path = "***/downloads/"
        output = path + filename

        start_time = time.time()
        el = entity_linking.EL(use_case='colon')
        result = el.perform_linking_and_serialization(report={'diagnosis': diagnosis,
                                                              'materials': materials,
                                                              'codes': codes,
                                                              'gender': gender,
                                                              'age': age},
                                                      output=output,
                                                      rdf_format=rdf_format)
        print("Program take: %s seconds to be executed." % (time.time() - start_time))

        if result:
            json_response = {"result": "graph generated"}
        else:
            json_response = {"result": "error"}
    else:
        json_response = {"error": "Invalid captcha"}

    return JsonResponse(json_response)

def download(request, filename):
    """Download requested filename"""
    concepts_graph = ""


    path = "***/downloads/"
    files = getConceptsGraphFileInfo(path)

    output = ""

    for file in files:
        if file["filename"] == filename:
            output = file["path"]
            break

    if not output:
        print(f"File {filename} not found")
        return JsonResponse({"error":"file not found"})

    concepts_graph = ""

    with open(output, mode='r', encoding='UTF-8') as f:
        concepts_graph = f.read()

    response = HttpResponse(concepts_graph, content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(filename)
    response['X-Sendfile'] = smart_str(output)
    return response

def removePreviousFiles(dir_path):
    files = os.listdir(dir_path)
    for file in files:
        os.remove(dir_path+file)

def getConceptsGraphFileInfo(dir_path):
    files = os.listdir(dir_path)
    path = ""
    filename = ""
    base_path = "***/downloads/"

    list_files = []


    for file in files:
            filename = file
            path = base_path + filename
            dict = {"filename":filename, "path":path}
            list_files.append(dict)

    return list_files

def spellchecker(request, word):
    dict = bio_proc_init.spell_checker(word)
    print(f"spellchecker: {dict}")

    return JsonResponse(dict)

def static(request, dir, file):
    """Download static resources"""



    path = "***/static/"

    output = path+dir+"/"+file

    content_type_dict = {'html': 'text/html', 'txt': 'text/plain', 'jpg': 'image/jpeg', 'png': 'image/png', 'css': 'text/css' }
    if('jpg' in file.lower() or 'png' in file.lower()):
        print('binary file')
        with open(output, mode='rb') as f:
            data = f.read()
    else:
        with open(output, mode='r', encoding='UTF-8') as f:
            data = f.read()

    content_type = ""
    if('jpg' in file.lower()):
        content_type = content_type_dict['jpg']
    elif('png' in file.lower()):
        content_type = content_type_dict['png']
    elif('txt' in file.lower()):
        content_type = content_type_dict['txt']
    elif('html' in file.lower()):
        content_type = content_type_dict['html']
    elif('css' in file.lower()):
        content_type = content_type_dict['css']

    response = HttpResponse(data, content_type=content_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file)
    response['X-Sendfile'] = smart_str(output)
    return response