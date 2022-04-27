import os

benchmark = '/Users/pkun/PycharmProjects/ui_api_automated_test/benchmark'
num = 0
lines = []
for f in os.listdir(benchmark):
    project = os.path.join(benchmark, f)
    if os.path.isdir(project):
        for file in os.listdir(project):
            if file.endswith('.log'):
                f = open(os.path.join(project, file), 'r').read()
                f = f.split('\n')
                for line in f:
                    if line.startswith('2022'):
                        if 'valid' in line and 'path' in line and 'successfully' not in line:
                            lines.append(line)
                            num += 1
print(num)
