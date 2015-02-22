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

def gen_door_graph(graphObj, doorList):
    # Set generic settings
    graphObj.show_legend = False
    graphObj.show_y_labels = False
    # graphObj.width = 100
    # Get all x labels
    x_labels = []
    unzipped = []
    
    def return_fixed_column_list(argList):
        # Create graph for that day
        prevStatus = None
        newList = []
        for i, row in enumerate(argList):
            time, status = row
            # If it starts with door close
            if i == 0 and status == 1:
                newList.append({'value': None})
            # Continue check if status has changed
            if prevStatus == status:
                # If change status, change color
                newList.append({'value': None})
            # Add value for next step
            newList.append({'value': 10, 'label': time})
            prevStatus = status
        # print newList
        return newList
    
    for element in doorList:
        x_labels.append(element['date'])
        fixed_column = return_fixed_column_list(element['status'])
        unzipped.append(fixed_column)
                        
    if len(x_labels) > 0:
        graphObj.x_labels = x_labels
        graphObj.x_label_rotation = 90
        
    # Created zipped variable
    # zipped = zip(*unzipped)
    zipped = map(None, *unzipped)
    
    for current_row in zipped:
        # Generate row in chart
        graphObj.add('', current_row)

def last_status_period(argDate, argTimeFrame, argDevId, argAttrId):
    ''' Get the last status of the door for that date and within timeframe = 10 min '''
    import time
    table = db_AH.event_history
    # whole_table = db_AH(((table.data=='Door Open')|(table.data=='Door Close'))&(table.date > argDate)).select(table.data, table.date)
    last_state = db_AH.executesql('SELECT data, date FROM event_history WHERE (date >= "%s" AND date < date_add("%s", INTERVAL "%s:0" MINUTE_SECOND)) AND (data = "Door Open" or data = "Door Close") AND device_id = %s AND attr_id = %s ORDER BY date DESC LIMIT 1' % (argDate,argDate,argTimeFrame,argDevId, argAttrId))
    return last_state

def status_prev_day(argDate, argDevId, argAttrId):
    ''' Get the last status of the previous day '''
    prev_day_status = db_AH.executesql('SELECT data, date from event_history WHERE date < "%s" AND (data = "Door Open" or data = "Door Close") AND device_id = %s AND attr_id = %s ORDER BY date DESC LIMIT 1' % (argDate,argDevId,argAttrId))
    return prev_day_status

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

def door_status(listDates, argDevId, argAttrId):
    ''' Creates a list ([day1][day2]) '''
    list_min = [ str(x).ljust(2, '0') for x in range(0,6) ]
    list_hour = [ str(x).zfill(2) for x in range(0,24) ]
    # varDoor = db_AH((table.data=='Door Open')|(table.data=='Door Close')).select(table.data, table.date)
    rangeArray = []
    for date in listDates:
        dayArray = []
        dayArray.append(status_prev_day(date,argDevId,argAttrId))
        for hour in list_hour:
            for minute in list_min:
                lastStatus = last_status_period('%s %s:%s:00' % (date,hour,minute), 10, argDevId, argAttrId)
                if len(lastStatus) == 0:
                    lastStatus = ([None, '%s:%s' % (hour,minute)],)
                dayArray.append(lastStatus)
        rangeArray.append({'date': date, 'list': dayArray})
    return rangeArray
    
def doorToGraphData(statusList):
    ''' Create graph data list '''
    result = []
    for currentElement in statusList:
        curDate = currentElement['date']
        curList = currentElement['list']
        newList = []
        prevStatus = None
        for curInt in curList:
            if curInt[0][0] is not None:
                status, time = curInt[0]
                # Strip the time in datetime
                time = time[11:]
                if status == 'Door Open':
                    newList.append([time, 1])
                elif status == 'Door Close':
                    newList.append([time, 0])
            else:
                # If no update, keep previous state
                status, time = prevStatus, curInt[0][1]
                if status == 'Door Open':
                    status = 1
                elif status == 'Door Close':
                    status = 0
                newList.append([time, status])
            # Update previous state
            prevStatus = status
        result.append({'date': curDate, 'status': newList})
    return result
    
def get_doors(attrName, genForm=False):
    ''' Get all device_id and attrId that matches attrName '''
    rows = prev_day_status = db_AH.executesql('SELECT attribute.attr_id, attribute.name, device.device_id, device.name, device.location FROM attribute INNER JOIN device_attr ON (attribute.attr_id = device_attr.attr_id) INNER JOIN device ON (device_attr.device_id = device.device_id) where attribute.name = "%s"' % attrName)
    if genForm is True:
        dropdown = SELECT(_name='DevAttr', *(OPTION(row[3] + "/" + row[4], _value=(row[2],row[0])) for row in rows))
        return dropdown
    else:
        return rows

def index():
    if len(request.vars) > 0:
        devId, attrId = request.vars.DevAttr.translate(None,' ()L').split(',')
        startDate = request.vars.startDate
        endDate = request.vars.endDate
        dateRange = getDateRange(startDate, endDate)
        doorStatusList = door_status(dateRange, devId, attrId)
        doorGraphValues = doorToGraphData(doorStatusList)

        response.headers['Content-Type']='image/svg+xml'
        chart_door = pygal.StackedBar(style=custom_style)
        chartList = doorGraphValues
        gen_door_graph(chart_door, chartList)
        # chart_door.render_to_png('/tmp/tmp.png')
        return chart_door.render()
    else:
        door_select = get_doors("Door", True)
        form = FORM('startDate', INPUT(_class='date', _name='startDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'), error_message='must be YYYY-MM-DD!')), 'endDate', INPUT(_class='date', _name='endDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'), error_message='must be YYYY-MM-DD!')), door_select, INPUT(_type='submit'))
        # if form.process().accepted:
        if form.accepts(request, session):
            response.flash = 'Form Accepted'
        elif form.errors:
            response.flash = 'Retry'
        else:
            response.flash = 'Please fill in form'
        return dict(result=BEAUTIFY(form))
