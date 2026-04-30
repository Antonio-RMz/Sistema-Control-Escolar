import pymysql

try:
    query = "INSERT INTO t (a, b, c) VALUES (%s, %s, %s)"
    args = ("A", "B")
    query % args
except TypeError as e:
    print("Tuple too small:", str(e))

try:
    query = "INSERT INTO t (a, b, c) VALUES (%s, %s, %s)"
    args = ("A", "B", "C", "D")
    query % args
except TypeError as e:
    print("Tuple too large:", str(e))

try:
    query = "INSERT INTO t (a, b) VALUES (%s, %s)"
    args = ("A", {"a": 1})
    query % args
except TypeError as e:
    print("Tuple with dict:", str(e))
