import os
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from botocore.exceptions import ClientError

class Command(BaseCommand):
    help = 'Test AWS S3 connection and upload'

    def handle(self, *args, **options):
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        region = settings.AWS_S3_REGION_NAME
        key = 'media/test_s3_file.txt'
        file_content = "Archivo de prueba para verificar conexión S3."

        try:
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_session_token=getattr(settings, 'AWS_SESSION_TOKEN', None),
                region_name=region,
            )

            # Subir archivo de prueba
            print(f"➡️ Subiendo archivo a {bucket_name}/{key}...")
            s3.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=file_content,
                ACL='public-read',
                ContentType='text/plain',
            )
            print("✅ Archivo subido exitosamente.")

            # Generar URL pública
            public_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
            print(f"🌐 URL pública generada: {public_url}")

            # Verificar acceso con HEAD
            print("🔎 Verificando acceso a la URL pública...")
            import requests
            response = requests.head(public_url)
            if response.status_code == 200:
                print("✅ Acceso público confirmado.")
            else:
                print(f"⚠️ Acceso denegado. Status code: {response.status_code}")
        except ClientError as e:
            print(f"❌ Error de cliente: {e}")
        except Exception as e:
            print(f"❌ Otro error: {e}")
