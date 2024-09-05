from rest_framework import viewsets, status, views, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.mail import EmailMessage, EmailMultiAlternatives, send_mail
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from . import utils, serializers
from django.conf import settings

class UploadView(views.APIView):

    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        params = request.query_params
        instance_type = params.get('instance_type', None)
        instance_id = params.get('instance_id', None)
        user_type = params.get('user_type', None)
        if user_type is not None:
            if instance_type is not None:
                filenames = []
                serializer = serializers.FileSerializer(data=request.data, many=True)
                if serializer.is_valid(raise_exception=True):
                    for data in serializer.data:
                        file = data['file']
                        if user_type == 'user':
                            user_prefix = f'user_id_{user.user_id}'
                        if user_type == 'admin':
                            user_prefix = user_type
                        datetime = utils.return_date_and_time()
                        keywords = {
                            'user': user_prefix,
                            'instance_type': instance_type
                        }
                        file_type = data['file_type']
                        if instance_id is not None:
                            folder = f'{instance_type}/{instance_id}'
                        else:
                            folder = f'{instance_type}/temp/'
                        folder = f'{folder}{file_type}'
                        filename = utils.generate_filename(datetime=datetime, **keywords)
                        path = f'{folder}{filename}'
                        request.session[filename] = {
                            'path': path,
                            'user_filename': file.name,
                            'status': 'new',
                            'is_deleted': False
                        }
                        default_storage.save(path, ContentFile(file.read()))
                        filenames.append(filename)
                    return Response({'message': 'File Uploaded Successfully!', 'filenames': filenames}, status=status.HTTP_200_OK)
        
    def delete(self, request):
        user = request.user
        filename = request.query_params.get('filename', None)
        if filename is not None:
            file = request.session[filename]
            path = file.get('path', None)
            if path is not None:
                default_storage.exists(path)
                if True:
                    default_storage.delete(path)
                    file['status'] = 'deleted'
                    file['is_deleted'] = True
                    request.session[filename] = file
                    pass

class Test(views.APIView):
    def post(self, request):
        try:
            print(settings.EMAIL_HOST_USER)
            print(settings.EMAIL_HOST_PASSWORD)
            subject = 'subject'
            message = 'test message'
            from_email = 'noreply@autolectronix.co.za'
            recipient_list = [request.data.get('email', None)]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            return Response({'message': 'success!!'}, status=status.HTTP_200_OK)
        except Exception:
            return Exception