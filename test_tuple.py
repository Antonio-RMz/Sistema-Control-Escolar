import pymysql

try:
    query = "INSERT INTO t (a, b, c) VALUES (%s, %s, %s)"
    args = ( ("A", "B"), "C", "D" )
    query % args
except TypeError as e:
    print("Tuple with tuple:", str(e))
