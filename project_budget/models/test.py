dict_sample = {
        1:{'name': 'name1', 'color': 'green'},
        2:{'name': 'name2', 'color': 'red'}
        }

for x in dict_sample.items():
    y = list(x[1].values())
    print(y[0])
    print(y[1])
