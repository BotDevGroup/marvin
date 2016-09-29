@ECHO OFF

set arg1 = %1


IF /I "%1%" == "stop"  goto STOP
IF /I "%1%" == "START"  goto START
echo "marvin.bat start to start, marvin.bat stop to stop"
goto EXIT


:START
if exist var\log goto LOGEXISTS
mkdir var\log
:LOGEXISTS
if exist var\schedule goto SCHEDULEEXISTS
mkdir var\schedule
:SCHEDULEEXISTS
start celery worker --app=marvinbot.celeryapp:marvinbot_app -l info --logfile=var\log\marvinbot.worker.log --pidfile=var\marvinbot.worker.pid
start celery beat --app=marvinbot.celeryapp:marvinbot_app -l info --logfile=var\log\marvinbot.beat.log --pidfile=var\marvinbot.beat.pid -s var\schedule\celerybeat-schedule

goto EXIT
:STOP

if not exist "var\marvinbot.worker.pid" goto BEAT
for /f %%G in (var\marvinbot.worker.pid) do (SET workerpid=%%G)
taskkill /f /PID %workerpid%
del var\marvinbot.worker.pid
:BEAT
if not exist "var\marvinbot.beat.pid" goto NOKILL
for /f %%G in (var\marvinbot.beat.pid) do (SET beatpid=%%G)

taskkill /f /pid %beatpid%
del var\marvinbot.beat.pid
goto EXIT
:NOKILL
echo No process to kill


:EXIT
ECHO ON
