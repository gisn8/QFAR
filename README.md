# QFAR
Bulk Find and Replace for QGIS Project Files

A recent network update left me with hundreds of QGIS project files each with dozens of layer locations needing 
updated to the new layer sources if I ever hoped to use them again. Without this, it would take significant time to even
open a project file with dead ends and then more time rerouting the layers. Testing on dozens of files, this is nearly 
instantaneous.

This program finds qgz and qgs files within a given directory and optionally its subdirectories, copies the files to a 
temp file while finding and replacing the values the user submitted, renames the original to a numbered hidden archive 
file if desired, replaces the original file with the modified version and assigns the "modified file date" to the same 
values as the original file. 

This could be used, for example, to change the IP address of your database source (ex. 192.168.12.34 to 192.168.56.78), 
drive locations (ex. /home/user/GIS_Data to /home/user/Drives/Data/GIS_Data), or even layer specific changes 
(Aerials_2018 to Aerials_2022), though there may be layer specific modifications that would need to be addressed. But as
this is a simple find and replace, any reference to the FIND string will be replaced regardless, so proceed with caution.

Archive copies that are made are prepended with '.' regardless of system. This makes them hidden on Linux systems; on 
Windows, the extra step is taken to also make them hidden; the archive name will still be prepended with '.'. Any files
prepended with '.' will be ignored, however Windows QGS and QGZ files that are not prepended with '.', even if hidden,
will be modified.

Considered seeking out "source=..." and finding and replacing within those strings specifically, but there are going 
be layer names that reference the source of the file that may also need updated to reduce confusion. However this could 
also potentially impact internal file metadata. *Again, this is a simple find and replace method.*


*** WARNING! ***
There are no safeguards against error or malicious injection! It is not outside the possibility to completely corrupt 
your files beyond hope of recovery! Take extreme care! Developer is not responsible for results!

It is recommended that you create a new directory and copy over a few QGIS project files to make sure you're getting the 
results you're expecting before using on your working directories.

WINDOWS: I've tried to accomodate for Windows, but at this time, my Windows machine is down. I could not adequately test. 
LINUX: Performed as expected.
APPLE: I have no access to an Apple machine at this time.
