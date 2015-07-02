# bottle-pxsession

bottle-pxsession is a secure pickle based session library

##Example Usage :
```
app = bottle.default_app()
plugin = bottle_pxsession.SessionPlugin(session_key='your_session_key',cookie_lifetime=600)
app.install(plugin)
```
**See "test.py"**
