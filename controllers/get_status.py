##################################################################################################
import pygal
from pygal.style import CleanStyle
from pygal.style import SaturateStyle
from pygal.style import Style

def calc_day(fromDay, days):
    ''' Calc the date from datetime format +|- N days '''
    from datetime import datetime, timedelta, date
    if fromDay == 'now':
        fromDay = datetime.now()
    else:
        fromDay = datetime.strptime(fromDay, '%Y-%m-%d %H:%M:%S')
    new_day = fromDay + timedelta(days=days)
    return new_day.strftime('%Y-%m-%d %H:%M:%S')

def current_datetime():
    ''' Function to return current datetime '''
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_datey_data(devId, attrId, fromDateTime, toDateTime, **kwargs):
    '''
    Function to returns either
    hits = True: Returns 1 if hit followed by 0
    on_off = [True_Condition, False_Condition]
    default returns [(datetime.datetime(2014, 10, 18, 15, 58, 29), 27.0), (datetime.datetime(2014, 10, 18, 16, 9, 34), 27.0)]
    '''
    from datetime import datetime, timedelta
    import re
    hits = kwargs.get('hits', False)
    on_off = kwargs.get('on_off', None)
    result = []

    # Function to parse through the rows
    def parse_rows(rows, **kwargs):
        loop_result = []
        #prev_status = 'off' # used for on_off
        if on_off is not None:
            cond_on, cond_off = on_off
            data = rows[0][0]
            if re.findall(cond_on, data):
                prev_status = 'on'
            else:
                prev_status = 'off'
        for row in rows:
            data, date = row
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            if hits:
                loop_result.append((date + timedelta(seconds=-1), 0))
                loop_result.append((date, 1))
                loop_result.append((date + timedelta(seconds=1), 0))
            elif on_off is not None:
                # cond_on, cond_off = on_off
                # If found status on
                if re.findall(cond_on, data) and prev_status == 'off':
                    loop_result.append((date + timedelta(seconds=-1), 0))
                    loop_result.append((date, 1))
                    prev_status = 'on'
                elif re.findall(cond_off, data) and prev_status == 'on':
                    loop_result.append((date + timedelta(seconds=1), 1))
                    loop_result.append((date, 0))
                    prev_status = 'off'
                elif prev_status == 'on':
                    loop_result.append((date, 1))
                    prev_status = 'on'
                elif prev_status == 'off':
                    loop_result.append((date, 0))
                    prev_status = 'on'
            else:
                # Normal graph mode
                loop_result.append((date, float(data)))
        return loop_result
    
    #### Adding the first value (to get x-axis right) ####
    last_state = db_AH.executesql('SELECT data, date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date < "%s" AND event_history.device_id=%s AND event_history.attr_id=%s ORDER BY date DESC LIMIT 1' % (fromDateTime, devId, attrId))
    # If no data before time, check after that start time
    if not len(last_state) > 0:
        last_state = db_AH.executesql('SELECT data, date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date > "%s" AND event_history.device_id=%s AND event_history.attr_id=%s ORDER BY date ASC LIMIT 1' % (fromDateTime, devId, attrId))
    data, date = last_state[0]
    result.extend(parse_rows(((data, fromDateTime),), hits=hits, on_off=on_off))

    ### Get rest of the rows ###
    rows = db_AH.executesql('SELECT data, date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date > "%s" AND event_history.date < "%s" AND event_history.device_id=%s AND event_history.attr_id=%s ORDER BY date' % (fromDateTime, toDateTime, devId, attrId))
    date = datetime.strptime(toDateTime, '%Y-%m-%d %H:%M:%S')
    result.extend(parse_rows(rows, hits=hits, on_off=on_off))

    # Adding last row (to get x-axis right)
    last_state = db_AH.executesql('SELECT data, date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date > "%s" AND event_history.device_id=%s AND event_history.attr_id=%s ORDER BY date DESC LIMIT 1' % (fromDateTime, devId, attrId))
    if not len(last_state) > 0:
        last_state = db_AH.executesql('SELECT data, date FROM event_history INNER JOIN device ON (event_history.device_id = device.device_id) WHERE event_history.date < "%s" AND event_history.device_id=%s AND event_history.attr_id=%s ORDER BY date ASC LIMIT 1' % (fromDateTime, devId, attrId))
    data, date = last_state[0]
    result.extend(parse_rows(((data, toDateTime),), hits=hits, on_off=on_off))
    return result


def render_graph(devId, attrId, fromDateTime, toDateTime, **kwargs):
    ''' Renders small graphs for the period '''
    from pygal.style import BlueStyle
    from datetime import datetime, timedelta
    
    height = kwargs.get('height', 150)
    width = kwargs.get('width', 800)
    sparkline = kwargs.get('sparkline', True)
    show_dots = kwargs.get('show_dots', True)
    show_y_guides = kwargs.get('show_y_guides', True)
    show_y_labels = kwargs.get('show_y_labels', True)
    show_x_guides = kwargs.get('show_x_guides', False)
    hits = kwargs.get('hits', False)
    on_off = kwargs.get('on_off', None)
    
    last_state = db_AH.executesql('SELECT data, date FROM event_history WHERE date < "%s" AND device_id = %s AND attr_id = %s ORDER BY date DESC LIMIT 1' % (fromDateTime,devId, attrId))
    sensor_name = db_AH.executesql('SELECT d.name as name, d.location as location, aa.name as attribute FROM device d INNER JOIN device_attr a ON (d.DEVICE_ID = a.device_id) INNER JOIN attribute aa ON (a.attr_id = aa.attr_id) WHERE d.DEVICE_ID = %s AND a.attr_id = %s LIMIT 1' % (devId, attrId))
    sensor_name = "-".join(sensor_name[0])
    
    # Create graph
    chart = pygal.DateY(include_x_axis=True, style=BlueStyle, show_only_major=True, height=height, width=width, title=sensor_name)
    chart.show_y_guides = show_y_guides
    chart.x_label_format = "%d/%m %H"
    chart.x_label_rotation = 90

    # Get data
    data = get_datey_data(devId, attrId, fromDateTime, toDateTime, **kwargs)
    chart.add('', data)
    
    # Render graph
    if sparkline:
        return chart.render_sparkline(show_dots=show_dots, width=width, height=height, show_y_labels=show_y_labels, show_minor_y_labels=False, show_x_guides=show_x_guides, margin=1, spacing=1, fill=True)
    else:
        return chart.render()
########################################################################################################################


# coding: utf8
if auth.user is None:
    redirect(URL('default', 'user', args='login',
    vars=dict(_next=URL(args=request.args, vars=request.vars))))

def user(): return dict(form=auth())

# @auth.requires_permission('read', secrets)
# @auth.requires(auth.user_id==1 or request.client=='127.0.0.1', requires_login=True)
# @auth.requires_login()

def get_all_sensors():
    items = db_AH((db_AH.device.device_id == db_AH.device_attr.device_id) & (db_AH.device_attr.attr_id == db_AH.attribute.attr_id)).select(db_AH.device.device_id, db_AH.device_attr.attr_id, db_AH.device.location, db_AH.device.name, db_AH.attribute.name)
    myset = []
    all_set = []
    for row in items:
        values = '%s,%s' % (row.device.device_id, row.device_attr.attr_id)
        item = '%s-%s-%s' % (row.device.location, row.device.name, row.attribute.name)
        myset.append((values, item))
        all_set.append(values)
    # myset = [ ('1,2,3', 'Sensor1'), ('4,5,6', 'Sensor2'), ('7,8,9', 'Sensor3') ]
    # Create form including sensors and DateStart and DateEnd
    form = SQLFORM.factory(Field('Sensors', type='boolean', requires=IS_IN_SET(myset, multiple=True), widget=SQLFORM.widgets.checkboxes.widget, default = all_set), Field('startDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'))), Field('endDate', widget=SQLFORM.widgets.date.widget, requires=IS_DATE(format=T('%Y-%m-%d'))), formstyle='divs')
    return form

def index():
    status_all = db_AH((db_AH.device.device_id == db_AH.device_attr.device_id) & (db_AH.device_attr.attr_id == db_AH.attribute.attr_id)).select(db_AH.device.location, db_AH.device.name, db_AH.attribute.name, db_AH.device_attr.data, db_AH.device_attr.updated)
    result = dict(status_all=SQLTABLE(status_all, headers={'device.location': T('Location'), 'device.name': T('Name'), 'attribute.name': T('Sensor Name'), 'device_attr.data': T('Value'), 'device_attr.updated': T('Last Updated')}))

    if len(request.vars) == 0:
        # Get all sensors and create as FORM
        all_sensors = get_all_sensors()
        # Create form with sensors and start and endDate
        graphs = FORM(all_sensors)
        
        if graphs.accepts(request, session):
            response.flash = 'Form Accepted'
        elif graphs.errors:
            response.flash = 'Retry'
        else:
            response.flash = 'Please fill in form'
            result['graphs'] = graphs
    else:
        sensors = request.vars['Sensors']
        startDate = request.vars['startDate']
        endDate = request.vars['endDate']

        # a = endDate
        # int(endDate)
        if (startDate is None or startDate == '') or (endDate is None or endDate == ''):
            endDate = current_datetime()
            startDate = calc_day(endDate, -1)
        else:
            startDate += " 00:00:00"
            endDate += " 23:59:00"

        SensorParams = {1: {'type': 'motion', 'show_dots': False, 'hits': True, 'on_off': None},
                        2: {'type': 'door', 'show_dots': False, 'hits': None, 'on_off': ['Open', 'Close']},
                        3: {'type': 'power', 'show_dots': False, 'hits': None, 'on_off': None},
                        4: {'type': 'humid', 'show_dots': False, 'hits': None, 'on_off': None},
                        5: {'type': 'temp', 'show_dots': False, 'hits': None, 'on_off': None},
                        6: {'type': 'smoke', 'show_dots': False, 'hits': None, 'on_off': None},
                        7: {'type': 'bright', 'show_dots': False, 'hits': None, 'on_off': None}}

        result['graphs'] = []
        # Convert to list if needed
        if type(sensors) is str:
            sensors = sensors.split()
        # Iterate through all sensors and generate XML
        for sensor in sensors:
            a = sensor.split(",")
            deviceId, sensorTypeId = [int(x) for x in sensor.split(",")]
            result['graphs'].append(XML(render_graph(deviceId, sensorTypeId, startDate, endDate, show_dots=SensorParams[sensorTypeId]['show_dots'], hits=SensorParams[sensorTypeId]['hits'], on_off=SensorParams[sensorTypeId]['on_off'])))
            
    return result
