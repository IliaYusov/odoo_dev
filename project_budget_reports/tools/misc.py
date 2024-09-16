from odoo.tools import float_round, get_lang, NON_BREAKING_SPACE


def formatLang(env, value, digits=2, grouping=True, monetary=False, dp=None, currency_obj=None,
               rounding_method='HALF-EVEN', rounding_unit='decimals'):
    if value == '':
        return ''

    if rounding_unit == 'decimals':
        if dp:
            digits = env['decimal.precision'].precision_get(dp)
        elif currency_obj:
            digits = currency_obj.decimal_places
    else:
        digits = 0

    rounding_unit_mapping = {
        'decimals': 1,
        'thousands': 10 ** 3,
        'millions': 10 ** 6,
        'billions': 10 ** 9
    }

    value /= rounding_unit_mapping.get(rounding_unit, 1)

    rounded_value = float_round(value, precision_digits=digits, rounding_method=rounding_method)
    formatted_value = get_lang(env).format(f'%.{digits}f', rounded_value, grouping=grouping, monetary=monetary)

    if currency_obj and currency_obj.symbol:
        arguments = (formatted_value, NON_BREAKING_SPACE, currency_obj.symbol)

        return '%s%s%s' % (arguments if currency_obj.position == 'after' else arguments[::-1])

    return formatted_value


def floatRound(value, digits=2, rounding_method='HALF-EVEN', rounding_unit='decimals'):
    if value == '':
        value = 0

    rounding_unit_mapping = {
        'decimals': 1,
        'thousands': 10 ** 3,
        'millions': 10 ** 6,
        'billions': 10 ** 9
    }

    value /= rounding_unit_mapping.get(rounding_unit, 1)

    return float_round(value, precision_digits=digits, rounding_method=rounding_method)
