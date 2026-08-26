import os
path = r"F:\Grade2master2\CITYLBM开发文件\v0.2.1\src\Resources\Validation\_rhino_test.txt"
with open(path, 'w') as f:
    f.write("Rhino Python script executed successfully!\n")
    import sys
    f.write("Python: " + sys.version + "\n")