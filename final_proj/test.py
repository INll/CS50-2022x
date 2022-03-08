temp = 3 

if temp == True:
    print("hello world")

# pairs = [('cheese', 'queso'), ('red', 'rojo'), ('school', 'escuela')]

# test = [tupleElement for tupleElement in pairs for item in tupleElement[:] if 'queso' in item]

# print(test)


# dictVal = {
#     "1": 1,
#     "2": 2,
#     "3": 3
# }

# dictMain = {
#     'one': dictVal,
#     'two': dictVal,
#     'three': dictVal
# }

# test = dictMain['three']
# test2 = dictMain['three']['3']

# print(type(dictMain))

# if type(dictMain) is dict:
#     print(dictMain)
    
    
                    # for attempt in range(3):
                    #     global keepLooping
                    #     keepLooping = True
                    #     try:
                    #         for key, val in userNameToID.items():   # Dict, key is ID, val is username#0000
                    #             if val == message.content:
                    #                 followingID = key
                    #                 keepLooping = False   # This is only False if a valid user is found!
                    #                 break 
                    #         if keepLooping == False:
                    #             break
                    #         raise KeyError   # If every key val is exhausted and no user is found
                        
                    #     except RuntimeError:   # If a new user just joined, new key val pair will be added
                    #         time.sleep(1)      # to userNameToID causing dict size changed error
                    #     except KeyError:
                    #         await message.author.send(f"`{message.content}`: No such user. Please try again.")
                    #         break
                    # if keepLooping:
                    #     print(f"`{caller} called ;;sub: Unknown error occurred. Conversion failed after 3 attempts.`")