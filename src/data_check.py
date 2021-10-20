f = open('data/input.tsv', 'r')
target = 'system requests from direct business'
data = []
for i in f:
    if target in i:
        data.append(i)
f.close()

for i in data:
    if 'yes' in i:
        print(i)


one_line = data[0]



print(one_line.split('\t'))