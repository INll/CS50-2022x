def todo(*argv):
    x = len(argv)
    for arg in argv:
        print(arg)
        

testcmds = []
testcmds.append("50, 10, 3, 30")

for i in range(len(testcmds)):
    try:
        todo(testcmds[i])
        todo(50, 10, 3, 30)
    except:
        pass