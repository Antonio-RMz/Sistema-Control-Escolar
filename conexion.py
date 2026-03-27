import pymysql
## Conexión a la base de datos
miConexion = pymysql.connect(host='localhost', user='root', passwd='root', db='escuelaBTI')
# Crear un cursor para ejecutar consultas SQL
#un cursor es un objeto que se utiliza para interactuar con la base de datos. Permite ejecutar consultas SQL, recuperar resultados y gestionar transacciones.
#en palabras simples un cursor es como un puntero que se utiliza para recorrer los resultados de una consulta SQL. Permite acceder a los datos de la base de datos de manera eficiente y flexible.
#una analogia de cursor es como un marcador en un libro. Imagina que estás leyendo un libro 
# y quieres marcar una página para volver a ella más tarde. El cursor es ese marcador que 
# te permite recordar dónde te quedaste. De manera similar, en una base de datos, 
# el cursor te permite recordar dónde estás en los resultados de una consulta SQL,
# para que puedas acceder a los datos de manera eficiente y flexible.
cur = miConexion.cursor()
cur.execute("SELECT * FROM TB_ALUMNOS")
# Imprime los resultados de la consulta. Se trae los registros de la tabla TB_ALUMNOS
for fila in cur.fetchall():
    print(fila)
