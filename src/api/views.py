# -*- coding: utf-8 -*-

# Copyright (c) 2017 Rohit Lodha
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import unicode_literals

from rest_framework.parsers import FileUploadParser,FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from models import ValidateFileUpload,ConvertFileUpload,CompareFileUpload
from serializers import ValidateSerializer,ConvertSerializer,CompareSerializer,ValidateSerializerReturn,ConvertSerializerReturn,CompareSerializerReturn
from rest_framework import status
from rest_framework.decorators import api_view,renderer_classes
from rest_framework.renderers import BrowsableAPIRenderer,JSONRenderer

from django.core.files.storage import FileSystemStorage
from django.conf import settings

import jpype
from traceback import format_exc
from os.path import abspath
from time import time
from urlparse import urljoin


class ValidateViewSet(ModelViewSet):
    """ Returns all validate api request """
    queryset = ValidateFileUpload.objects.all()
    serializer_class = ValidateSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

class ConvertViewSet(ModelViewSet):
    """ Returns all convert api request """
    queryset = ConvertFileUpload.objects.all()
    serializer_class = ConvertSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

class CompareViewSet(ModelViewSet):
    """ Returns all compare api request """
    queryset = CompareFileUpload.objects.all()
    serializer_class = CompareSerializerReturn
    parser_classes = (MultiPartParser, FormParser,)

@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def validate(request):
    """ Handle Validate api request """
    if request.method == 'GET':
        """ Return all validate api request """
        query = ValidateFileUpload.objects.all()
        serializer = ValidateSerializer(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """ Return validate tool result on the post file"""
        serializer = ValidateSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    folder = "api/"+str(request.user) +"/"+ str(int(time()))
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,
                        base_url=urljoin(settings.MEDIA_URL, folder+'/')
                        )
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    """ Call the java function with parameter"""
                    retval = verifyclass.verify(settings.APP_DIR+uploaded_file_url)
                    if (len(retval) > 0):
                        result = "The following error(s)/warning(s) were raised: " + str(retval)
                        returnstatus = status.HTTP_400_BAD_REQUEST
                        httpstatus = 400
                        jpype.detachThreadFromJVM()
                    else :
                        result = "This SPDX Document is valid."
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                        jpype.detachThreadFromJVM()
                else :
                    result = "File Not Uploaded"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    httpstatus = 400
                    jpype.detachThreadFromJVM()
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                result = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            except :
                """ Other errors raised"""
                result = format_exc()
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            query = ValidateFileUpload.objects.create(
                owner=request.user,
                file=request.data.get('file'),
                result=result,
                status = httpstatus,
                )
            serial = ValidateSerializerReturn(instance=query)
            return Response(
                serial.data, status=returnstatus
                )
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

def extensionGiven(filename):
    if (filename.find(".")!=-1):
        return True
    else:
        return False

def getFileFormat(to_format):
    if (to_format=="Tag"):
        return ".spdx"
    elif (to_format=="RDF"):
        return ".rdf"
    elif (to_format=="Spreadsheet"):
        return ".xlsx"
    elif (to_format=="HTML"):
        return ".html"
    else :
        return ".invalid"

@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def convert(request):
    """ Handle Convert api request """
    if request.method == 'GET':
        """ Return all convert api request """
        query = ConvertFileUpload.objects.all()
        serializer = ConvertSerializer(query, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        """ Return convert tool result on the post file"""
        serializer = ConvertSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            result = ""
            message = ""
            try :
                if request.FILES["file"]:
                    """ Saving file to the media directory """
                    myfile = request.FILES['file']
                    folder = "api/"+str(request.user) +"/"+ str(int(time()))
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,
                        base_url=urljoin(settings.MEDIA_URL, folder+'/')
                        )
                    filename = fs.save(myfile.name, myfile)
                    uploaded_file_url = fs.url(filename)
                    option1 = request.POST["from_format"]
                    option2 = request.POST["to_format"]
                    convertfile =  request.POST["cfilename"]
                    warningoccurred = False
                    if (extensionGiven(convertfile)==False):
                        extension = getFileFormat(option2)
                        convertfile = convertfile + extension
                    """ Call the java function with parameters as list"""
                    if (option1=="Tag"):
                        print ("Verifing for Tag/Value Document")
                        if (option2=="RDF"):
                            tagtordfclass = package.TagToRDF
                            retval = tagtordfclass.onlineFunction([
                                settings.APP_DIR+uploaded_file_url,
                                settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="Spreadsheet"):
                            tagtosprdclass = package.TagToSpreadsheet
                            retval = tagtosprdclass.onlineFunction([
                                settings.APP_DIR+uploaded_file_url,
                                settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            message = "Select valid conversion types."
                            returnstatus = status.HTTP_400_BAD_REQUEST
                            httpstatus = 400
                            jpype.detachThreadFromJVM()
                    elif (option1=="RDF"):
                        print ("Verifing for RDF Document")
                        if (option2=="Tag"):
                            rdftotagclass = package.RdfToTag
                            retval = rdftotagclass.onlineFunction([
                                settings.APP_DIR+uploaded_file_url,
                                settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="Spreadsheet"):
                            rdftosprdclass = package.RdfToSpreadsheet
                            retval = rdftosprdclass.onlineFunction([
                                settings.APP_DIR+uploaded_file_url,
                                settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="HTML"):
                            rdftohtmlclass = package.RdfToHtml
                            retval = rdftohtmlclass.onlineFunction([
                                settings.APP_DIR+uploaded_file_url,
                                settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            message = "Select valid conversion types."
                            returnstatus = status.HTTP_400_BAD_REQUEST
                            httpstatus = 400
                            jpype.detachThreadFromJVM()
                    elif (option1=="Spreadsheet"):
                        print ("Verifing for Spreadsheet Document")
                        if (option2=="Tag"):
                            sprdtotagclass = package.SpreadsheetToTag
                            retval = sprdtotagclass.onlineFunction([
                                settings.APP_DIR+uploaded_file_url,
                                settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        elif (option2=="RDF"):
                            sprdtordfclass = package.SpreadsheetToRDF
                            retval = sprdtordfclass.onlineFunction([
                                settings.APP_DIR+uploaded_file_url,
                                settings.MEDIA_ROOT+"/"+ folder+"/"+convertfile
                                ])
                            if (len(retval) > 0):
                                warningoccurred = True
                        else :
                            message = "Select valid conversion types."
                            returnstatus = status.HTTP_400_BAD_REQUEST
                            httpstatus = 400
                            jpype.detachThreadFromJVM()
                    if (warningoccurred == True ):
                        message = "The following error(s)/warning(s) were raised: " + str(retval)
                        result = "/media/" + folder+"/"+ convertfile
                        returnstatus = status.HTTP_406_NOT_ACCEPTABLE
                        httpstatus = 406
                        jpype.detachThreadFromJVM()
                    else :
                        result = "/media/" + folder+"/"+ convertfile
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                        jpype.detachThreadFromJVM()
                else :
                    message = "File Not Found"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    httpstatus = 400
                    jpype.detachThreadFromJVM()
            except jpype.JavaException,ex :
                message = jpype.JavaException.message(ex)
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM() 
            except :
                message = format_exc()
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM() 
            query = ConvertFileUpload.objects.create(
                owner=request.user,
                file=request.data.get('file'),
                result=result,message=message,
                from_format=request.POST["from_format"],
                to_format=request.POST["to_format"],
                cfilename=request.POST["cfilename"],
                status =httpstatus
                )
            serial = ConvertSerializerReturn(instance=query)
            return Response(
                serial.data,status=returnstatus
                )   
        else:
            return Response(
                serializer.errors,status=status.HTTP_400_BAD_REQUEST
                )


@api_view(['GET', 'POST'])
@renderer_classes((JSONRenderer,))
def compare(request):
    """ Handle Compare api request """
    if request.method == 'GET':
        """ Return all compare api request """
        query = CompareFileUpload.objects.all()
        serializer = CompareSerializerReturn(query, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        """ Return compare tool result on the post file"""
        serializer = CompareSerializer(data=request.data)
        if serializer.is_valid():
            if (jpype.isJVMStarted()==0):
                """ If JVM not already started, start it, attach a Thread and start processing the request """
                classpath =settings.JAR_ABSOLUTE_PATH
                jpype.startJVM(jpype.getDefaultJVMPath(),"-ea","-Djava.class.path=%s"%classpath)
            """ Attach a Thread and start processing the request """
            jpype.attachThreadToJVM()
            package = jpype.JPackage("org.spdx.tools")
            verifyclass = package.Verify
            compareclass = package.CompareMultpleSpdxDocs
            result=""
            message=""
            erroroccurred = False
            try :
                if (request.FILES["file1"] and request.FILES["file2"]):
                    """ Saving file to the media directory """
                    rfilename = request.POST["rfilename"]
                    if (extensionGiven(rfilename)==False):
                        rfilename = rfilename+".xlsx"
                    folder = "api/"+str(request.user) +"/"+ str(int(time()))
                    fs = FileSystemStorage(location=settings.MEDIA_ROOT +"/"+ folder,
                        base_url=urljoin(settings.MEDIA_URL, folder+'/')
                        )
                    callfunc = [settings.MEDIA_ROOT+"/"+ folder+"/"+rfilename]
                    file1 = request.FILES["file1"]
                    file2 = request.FILES["file2"]
                    filename1 = fs.save(file1.name, file1)
                    uploaded_file_url1 = fs.url(filename1)
                    filename2 = fs.save(file2.name, file2)
                    uploaded_file_url2 = fs.url(filename2)
                    callfunc.append(settings.APP_DIR+uploaded_file_url1)
                    callfunc.append(settings.APP_DIR+uploaded_file_url2)
                    """ Call the java function with parameters as list"""
                    retval1 = verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url1)
                    if (len(retval1) > 0):
                        erroroccurred = True
                        message = "The following error(s)/warning(s) were raised by " + str(file1.name) + ": " +str(retval1)
                    retval2 = verifyclass.verifyRDFFile(settings.APP_DIR+uploaded_file_url2)
                    if (len(retval2) > 0):
                        erroroccurred = True
                        message += "The following error(s)/warning(s) were raised by " + str(file1.name) + ": " +str(retval2)
                    try :
                        compareclass.onlineFunction(callfunc)
                        result = "/media/" + folder+"/"+ rfilename
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                    except :
                        message += "While running compare tool " + format_exc()
                        returnstatus = status.HTTP_400_BAD_REQUEST
                        httpstatus = 400
                    if (erroroccurred == False):
                        returnstatus = status.HTTP_201_CREATED
                        httpstatus = 201
                    else :
                        returnstatus = status.HTTP_406_BAD_REQUEST
                        httpstatus = 406
                    jpype.detachThreadFromJVM()
                else :
                    message = "File Not Uploaded"
                    returnstatus = status.HTTP_400_BAD_REQUEST
                    httpstatus = 400
                    jpype.detachThreadFromJVM()
            except jpype.JavaException,ex :
                """ Error raised by verifyclass.verify without exiting the application"""
                message = jpype.JavaException.message(ex) #+ "This SPDX Document is not a valid RDF/XML or tag/value format"
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            except :
                message = format_exc()
                returnstatus = status.HTTP_400_BAD_REQUEST
                httpstatus = 400
                jpype.detachThreadFromJVM()
            query = CompareFileUpload.objects.create(
                owner=request.user,
                message=message,
                file1=request.data.get('file1'),
                file2=request.data.get('file2'),
                rfilename = rfilename,
                result=result,
                status=httpstatus
                )
            serial = CompareSerializerReturn(instance=query)
            return Response(
                serial.data,status=returnstatus
                )
        else:
            return Response(
                serializer.errors,status=status.HTTP_400_BAD_REQUEST
                )