# -*- coding: utf-8 -*-
# import pygal_graph

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
    
    # Create graph
    chart = pygal.DateY(include_x_axis=True, style=BlueStyle, show_only_major=True, height=height, width=width)
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

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    
    currentDateTime = current_datetime()
    fromDateTime = calc_day(currentDateTime, -3)

    # Adjust if any graphs should be shown in index page
    # Temperatur=XML(render_graph(3, 5, fromDateTime, currentDateTime, show_dots=False))
    # Procent_smoke=XML(render_graph(3, 6, fromDateTime, currentDateTime, show_dots=False))
    # Kitchen_Stove=XML(render_graph(2, 3, fromDateTime, currentDateTime, show_dots=False))
    # Humid=XML(render_graph(3, 4, fromDateTime, currentDateTime, show_dots=False))
    # Brightness=XML(render_graph(3, 7, fromDateTime, currentDateTime, show_dots=False))
    # Hall_motions=XML(render_graph(1, 1, fromDateTime, currentDateTime, show_dots=False, hits=True))
    # Hall_door=XML(render_graph(1, 2, fromDateTime, currentDateTime, show_dots=False, on_off=['Open', 'Close']))

    # return dict(test=locals())
    # return dict(test=device_monitoring)
    return dict()


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())

@auth.requires_membership("admin")
def list_users():
    btn = lambda row: A("Edit", _href=URL('manage_user', args=row.auth_user.id))
    db.auth_user.edit = Field.Virtual(btn)
    rows = db(db.auth_user).select()
    headers = ["ID", "Name", "Last Name", "Email", "Edit"]
    fields = ['id', 'first_name', 'last_name', "email", "edit"]
    table = TABLE(THEAD(TR(*[B(header) for header in headers])),
                  TBODY(*[TR(*[TD(row[field]) for field in fields]) \
                        for row in rows]))
    table["_class"] = "table table-striped table-bordered table-condensed"
    return dict(table=table)

@auth.requires_membership("admin")
def manage_user():
    user_id = request.args(0) or redirect(URL('list_users'))
    form = SQLFORM(db.auth_user, user_id).process()
    membership_panel = LOAD(request.controller,
                            'manage_membership.html',
                             args=[user_id],
                             ajax=True)
    return dict(form=form,membership_panel=membership_panel)

@auth.requires_membership("admin")
def manage_membership():
    user_id = request.args(0) or redirect(URL('list_users'))
    db.auth_membership.user_id.default = int(user_id)
    db.auth_membership.user_id.writable = False
    form = SQLFORM.grid(db.auth_membership.user_id == user_id,
                       args=[user_id],
                       searchable=False,
                       deletable=False,
                       details=False,
                       selectable=False,
                       csv=False,
                       user_signature=False)  # change to True in production
    return form
