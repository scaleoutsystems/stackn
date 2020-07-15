import sys

with open('reports/tests.py', 'r+') as f:
    contents = f.read().\
        replace("access_key=''", "access_key='{}'".format(sys.argv[1])).\
        replace("secret_key=''", "secret_key='{}'".format(sys.argv[2]))
    f.seek(0)
    f.truncate()
    f.write(contents)
