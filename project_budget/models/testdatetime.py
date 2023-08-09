import datetime
import dateutil.tz

print(datetime.datetime.now())
tzinfo=dateutil.tz.tzoffset(None, 9*60*60)
print(datetime.datetime.tzinfo.utcoffset(datetime.datetime.now()))

    # .strftime("%d/%m/%y %H:%M:%S")