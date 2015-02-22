# coding: utf8
if auth.user is None:
    redirect(URL('default', 'user', args='login',
    vars=dict(_next=URL(args=request.args, vars=request.vars))))

import pygal
from pygal.style import CleanStyle
from pygal.style import SaturateStyle
from pygal.style import Style
custom_style = Style(
  colors=('#01DF01', '#FF0000'))

'''
from pygal.style import Style
custom_style = Style(
  background='transparent',
  plot_background='transparent',
  foreground='#53E89B',
  foreground_light='#53A0E8',
  foreground_dark='#630C0D',
  opacity='.6',
  opacity_hover='.9',
  transition='400ms ease-in',
  colors=('#E853A0', '#E8537A', '#E95355', '#E87653', '#E89B53'))
'''

def fixGraphList(argList, argDates):
    import re
    result = []
    for element, date in zip(argList, argDates):
        if re.search(r'\d{4}-\d{2}-\d{2}', date):
            value = element[0][0]
            result.append({'value': value, 'xlink': URL('index', vars=dict(startDate=date, endDate=date, DevAttr=request.vars.DevAttr))})
        else:
            result.append(element[0][0])
    return result

def gen_line_graph(graphObj, dateList, graphLists):
    # If one day specify hours in x-labels
    if len(dateList) == 1:
        dateList = [ str(x).zfill(2) for x in range(0,24) ]
    
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

def motion_status_period(listDates, argDevList):
    ''' Creates a list ({'name': [dev1-day1,dev1-day]}) '''
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
        if len(listDates) > 1:
            for date in listDates:
                rows = db_AH.executesql('SELECT count(*) FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date LIKE "%s%%" AND event_history.device_id=%s AND event_history.attr_id=%s' % (date, devId, attrId))
                result[name].append(rows)
        else:
                list_hour = [ str(x).zfill(2) for x in range(0,24) ]
                for hour in list_hour:
                    # rows = db_AH.executesql('SELECT event_history.data, event_history.date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date LIKE "%s%%" AND event_history.device_id=%s AND event_history.attr_id=%s' % (listDates[0] + ' ' + hour, devId, attrId))
                    rows = db_AH.executesql('SELECT count(*) FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date LIKE "%s%%" AND event_history.device_id=%s AND event_history.attr_id=%s' % (listDates[0] + ' ' + hour, devId, attrId))
                    result[name].append(rows)
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

def index():
    if len(request.vars) > 0:
        devList = request.vars.DevAttr
        startDate = request.vars.startDate
        endDate = request.vars.endDate
        dateRange = getDateRange(startDate, endDate)
        statusList = motion_status_period(dateRange, devList)
        response.headers['Content-Type']='image/svg+xml'
        chart_motion = pygal.Line(interpolate='hermite', interpolation_parameters={'type': 'cardinal', 'c': .75})
        gen_line_graph(chart_motion, dateRange, statusList)
        return chart_motion.render()
    else:
        motion_select = get_all_sensormatch_at_location("Motion", True)
        form = FORM('startDate', INPUT(_class='date', _name='startDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'), error_message='must be YYYY-MM-DD!')), 'endDate', INPUT(_class='date', _name='endDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'), error_message='must be YYYY-MM-DD!')), motion_select, INPUT(_type='submit'))
        # if form.process().accepted:
        if form.accepts(request, session):
            response.flash = 'Form Accepted'
        elif form.errors:
            response.flash = 'Retry'
        else:
            response.flash = 'Please fill in form'
        return dict(result=BEAUTIFY(form))
