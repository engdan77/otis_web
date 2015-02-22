# coding: utf8

import pygal
from pygal.style import CleanStyle
from pygal.style import SaturateStyle
from pygal.style import Style

sensor_type = 'Temperature'

def diffdates(d1, d2):
    import time
    #Date format: %Y-%m-%d %H:%M:%S
    return (time.mktime(time.strptime(d2,"%Y-%m-%d %H:%M:%S")) -
               time.mktime(time.strptime(d1, "%Y-%m-%d %H:%M:%S"))) / 60 / 60

def addDay(argDate, days):
    import time
    import datetime
    date = datetime.datetime.strptime(argDate,"%Y-%m-%d %H:%M:%S")
    date += datetime.timedelta(days=1)
    return date.strftime('%Y-%m-%d')


def fixGraphListToDateY(argList, argDates):
    import re
    from datetime import datetime, timedelta
    result = []
    for element, date in zip(argList, argDates):
        if re.search(r'\d{4}-\d{2}-\d{2}', date):
            value = element
            year, month, day = re.match(r'(\d{4})-(\d{2})-(\d{2})', date).groups()
            result.append({'value': (datetime(int(year), int(month), int(day)), value), 'xlink': URL('index', vars=dict(startDate=date, endDate=date, DevAttr=request.vars.DevAttr))})
        elif re.search(r'\d{2}:\d{2}:\d{2}', date):
            value = element
            hour, min, sec = re.match(r'(\d{2}):(\d{2}):(\d{2})', date).groups()
            result.append({'value': (datetime(2010, 1, 1, int(hour), int(min), int(sec)), value)})
    return result


def fixGraphList(argList, argDates):
    import re
    result = []
    for element, date in zip(argList, argDates):
        if re.search(r'\d{4}-\d{2}-\d{2}', date):
            value = element
            result.append({'value': value, 'xlink': URL('index', vars=dict(startDate=date, endDate=date, DevAttr=request.vars.DevAttr))})
        else:
            result.append(element)
    return result


def gen_datey_graph(graphObj, dateList, graphLists):
    # If one day specify hours in x-labels
    if len(dateList) == 1:
        firstElement = graphLists.keys()[0]
    graphObj.x_labels = dateList
    graphObj.x_label_rotation = 90
    
    for currentName in graphLists.keys():
        # Generate line in chart
        graphObj.add(currentName, fixGraphListToDateY(graphLists[currentName], dateList))

    
def gen_line_graph(graphObj, dateList, graphLists):
    # If one day specify hours in x-labels
    if len(dateList) == 1:
        firstElement = graphLists.keys()[0]
        # Get dates as x-labels from first in dict
        # dateList = [ x[1][11:] for x in graphLists[firstElement][0] ]
    graphObj.x_labels = dateList
    graphObj.x_label_rotation = 90
    
    for currentName in graphLists.keys():
        # Generate line in chart
        graphObj.add(currentName, fixGraphList(graphLists[currentName], dateList))

def getDateRange(startDate, endDate):
    ''' Generate a list of dates '''
    import datetime
    dateList = []
    start = datetime.datetime.strptime(startDate, '%Y-%m-%d')
    end = datetime.datetime.strptime(endDate, '%Y-%m-%d')
    step = datetime.timedelta(days=1)
    while start <= end:
        dateList.append(start.strftime("%Y-%m-%d"))
        start += step
    return dateList

def getClockChanges(date, argDevList):
    # Convert string to 2-dimensional array
    argDevList = argDevList.translate(None, "'([]Lu").split(')')
    newDevList = []
    for device in argDevList:
        row = device.split(', ')
        if len(row) == 3:
            newDevList.append(row)
    argDevList = newDevList
    
    result = {}
    for element in argDevList:
        name, devId, attrId = element
        result[name] = []
        rows = db_AH.executesql('SELECT date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date LIKE "%s%%" AND event_history.device_id=%s AND event_history.attr_id=%s' % (date, devId, attrId))
        result = [ x[0][11:] for x in rows ]
    return result

    
    
def general_status_period(listDates, argDevList, currentDate=None):
    ''' Creates a list ({'name': [dev1-day1,dev1-day]}) '''
    import re
    # Convert string to 2-dimensional array
    argDevList = argDevList.translate(None, "'([]Lu").split(')')
    newDevList = []
    for device in argDevList:
        row = device.split(', ')
        if len(row) == 3:
            newDevList.append(row)
    argDevList = newDevList
    
    result = {}
    for element in argDevList:
        name, devId, attrId = element
        result[name] = []
        # if len(listDates) > 1:
        if currentDate is None:
            rows = []
            # Get the last state
            last_state = db_AH.executesql('SELECT data, date FROM event_history WHERE date < "%s" AND device_id = %s AND attr_id = %s ORDER BY date DESC LIMIT 1' % (listDates[0],devId, attrId))
            rows.extend(last_state)
            # Iterate through all dates
            for date in listDates:
                rows = []
                # Get all general change rows for that device
                next_rows = db_AH.executesql('SELECT data, date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date LIKE "%s%%" AND event_history.device_id=%s AND event_history.attr_id=%s' % (date, devId, attrId))
                rows.extend(next_rows)
                # Check all rows and check for how long time general been above threshold
                time_within = timeAboveUnder(rows, 10, 100)
                result[name].append(time_within)
        else:
                rows = db_AH.executesql('SELECT data FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date LIKE "%s%%" AND event_history.device_id=%s AND event_history.attr_id=%s' % (currentDate, devId, attrId))
                result[name] = [ float(x[0]) for x in rows ]
    return result


def get_all_sensormatch_at_location(attrName, genForm=False):
    ''' Get all device_id and attrId that matches attrName per location '''
    rows = db_AH.executesql('SELECT attribute.attr_id, attribute.name, device.device_id, device.name, device.location FROM attribute INNER JOIN device_attr ON (attribute.attr_id = device_attr.attr_id) INNER JOIN device ON (device_attr.device_id = device.device_id) WHERE attribute.name = "%s"' % attrName)

    # Create a dict of unique locations
    listLocations = list(set(zip(*rows)[4]))
    
    result = {}
    for location in listLocations:
        result[location] = []
    
    # Process each row to create a dict
    for row in rows:
        currentLocation = row[4]
        result[currentLocation].append((row[3] + "/" + row[4], row[2], row[0]))

    # Create list
    rows = []
    for key in result.keys():
        rows.append((key, result[key]))
    
    if genForm is True:
        dropdown = SELECT(_name='DevAttr', *(OPTION(row[0], _value=(row[1])) for row in rows))
        return dropdown
    else:
        return rows

def gen_graph(devList, startDate, endDate):
    import re
    devList = request.vars.DevAttr
    startDate = request.vars.startDate
    endDate = request.vars.endDate
    dateRange = getDateRange(startDate, endDate)
    if len(dateRange) == 1:
        dateRange = getClockChanges(startDate, devList)
        statusList = general_status_period(dateRange, devList, startDate)
    else:
        statusList = general_status_period(dateRange, devList)
    chart_general = pygal.DateY(include_x_axis=True)
    chart_general.show_y_guides = False
    chart_general.show_dots = False
    # Change display format depending of dateformat, time of day, or date
    if (re.search(r'\d{2}:\d{2}:\d{2}', dateRange[0])):
        chart_general.x_label_format = "%H:%M"
    else:
        chart_general.x_label_format = "%Y-%m-%d %H:%M"
    gen_datey_graph(chart_general, dateRange, statusList)
    # return chart_general.render()
    return str(devList)

    
def index():
    import re
    if len(request.vars) > 0:
        devList = request.vars.DevAttr
        startDate = request.vars.startDate
        endDate = request.vars.endDate
        dateRange = getDateRange(startDate, endDate)

        if len(dateRange) == 1:
            dateRange = getClockChanges(startDate, devList)
            statusList = general_status_period(dateRange, devList, startDate)
        else:
            statusList = general_status_period(dateRange, devList)
        # response.headers['Content-Type']='image/svg+xml'
        # chart_general = pygal.Line(interpolate='hermite', interpolation_parameters={'type': 'cardinal', 'c': .75})
        
        chart_general = pygal.DateY(include_x_axis=True)
        chart_general.show_y_guides = False
        chart_general.show_dots = False
        # Change display format depending of dateformat, time of day, or date
        if (re.search(r'\d{2}:\d{2}:\d{2}', dateRange[0])):
            chart_general.x_label_format = "%H:%M"
        else:
            chart_general.x_label_format = "%Y-%m-%d %H:%M"
        
        gen_datey_graph(chart_general, dateRange, statusList)
        return chart_general.render()
    else:
        motion_select = get_all_sensormatch_at_location(sensor_type, True)
        form = FORM('startDate', INPUT(_class='date', _name='startDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'), error_message='must be YYYY-MM-DD!')), 'endDate', INPUT(_class='date', _name='endDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'), error_message='must be YYYY-MM-DD!')), motion_select, INPUT(_type='submit'))
        # if form.process().accepted:
        if form.accepts(request, session):
            response.flash = 'Form Accepted'
        elif form.errors:
            response.flash = 'Retry'
        else:
            response.flash = 'Please fill in form'
        return dict(result=BEAUTIFY(form))
