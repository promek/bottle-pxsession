import bottle
import bottle_pxsession

app = bottle.default_app()
plugin = bottle_pxsession.SessionPlugin(session_key='your_session_key',cookie_lifetime=600)
app.install(plugin)

@bottle.route('/')
def index(session):
    #print session.items()
    #print session.has_key('test')
    session['test'] = session.get('test',0) + 1
    session.save() # save session
    return 'Test : %d' % session['test']
bottle.run(app=app)
