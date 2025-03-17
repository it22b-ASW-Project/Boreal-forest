"# Boreal-forest" 

- PARA INICIAR LA APLICACIÓN 

$ py .\manage.py runserver

(puede que en vez de py sea python o python3)

- PARA AÑADIR/MODIFICAR TABLAS DE LA BD

$ py .\manage.py makemigrations

(este comando crear archivos de migracion a partir de los cambios en el archivo models.py)

- PARA APLICAR LOS CAMBIOS EN LA BASE DE DATOS

$ py .\manage.py migrate

(este comando aplica los cambios descritos en los archivos de la carpeta ./migrations sobre nuestra BD)

*Al hacer el pull, probablemente este último comando sea el útil, porque los archivos de migración ya estarán creados.

*Para consultar el archivo boreal_forest.sqlite3 (nuestra BD), os podeis descargar la aplicación en "sqlitebrowser.org/dl/".



