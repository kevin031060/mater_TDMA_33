import os
for i in range(1,20):
    os.system('kill -9 $(lsof -t -i:%d)'%(9000+i))