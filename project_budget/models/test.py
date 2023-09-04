atr_value ='1|1: Статистика' \
            '2: Топливо ' \
            '3: ТЭК' \
            '4: КНВ' \
            '5: Лаборатория' \
            '6: Несоответствия' \
            '8: Производство' \
            '9: УЗК ' \
            '10: УТК' \
            '15: ИЛ ' \
            '17: ТКК' \
            '19: КП' \
            '20: SPC' \
            '23: КТД' \
            '26: УТД' \
            '27: Планирование' \
            '30: Сменка' \
            '32:  Испытания' \
            '34: Кадры ' \
            '35: Геометрия' \
            '36: ПРГР' \
            '80: Автоматизированная аналитика'
atr_value = atr_value + ':'
arr = atr_value.split('|')
key = arr[0]
value = arr[1]
pos = value.find(key)
if pos != -1:
    value = value[pos:len(value)]
    arr = value.split(':')
    result = arr[1]
    lenres = len(result)
    maybedigit = result[lenres-1:lenres]
    while maybedigit.isdigit():
        result = result[0:lenres-1]
        maybedigit = result[lenres-1:lenres]
    print (result)
else:
    print( '')


