import pandas as pd
def create_medications(names, counts):
    medications = pd.Series(data=[*counts],index=[*names])
    return medications
def get_percent(medications, name):
    percent = medications.loc[name]/sum(medications) * 100
    return percent


names=['chlorhexidine', 'cyntomycin', 'afobazol']
counts=[15, 18, 7]

print(get_percent(create_medications(names, counts), "chlorhexidine")) #37.5


