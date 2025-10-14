# Backup
My app was built for my own personal needs, to automate backing up my stuff.

Current issues:
1. When skipping an identical folder:
    a. The progress bar becomes inaccurate- the counter should be updated after skipping
    b. We should only log the highest hierarchy folder that was skipped - not every skipped folder
2. UI stuck sometimes - threading might help
