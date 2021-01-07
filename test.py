import random

list1 = [sum(random.choice(range(1,7))  for i in range(0,3)) for i in range(1,100001)]
list2 = [sum(random.choice(range(1,7))  for i in range(0,4)) for i in range(1,100001)]
list3 = [1 for i in range(1,len(list1)) if list1[i] > list2[i] ]
list4 = [1 for i in range(1,len(list1)) if list1[i] == list2[i] ]

ties = len(list4)
total = sum(list3)/(100000.0 - ties)

l = [1,2,3,4,6]

l = [7-i for i in l]

print(l)
