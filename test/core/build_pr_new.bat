@echo off
cls

:start
echo BUILD SCRIPTS FOR PROJECT REALITY
echo Select build option: (normally, this will be 1)
echo 1 - Full build
echo 2 - Full build without SVN update
echo 3 - Full build without SVN update or export (MUST have folders already exported)
echo 4 - Patch build
echo 5 - Patch build without SVN update
echo 6 - Patch build without SVN update or export (MUST have folder already exported)
echo 7 - Core only
echo 8 - Levels only
echo 9 - Build installers only

set choice=
set /p choice=?

if '%choice%' == '1' goto FULL_BUILD
if '%choice%' == '2' goto FULL_BUILD_NO_UPDATE
if '%choice%' == '3' goto FULL_BUILD_NO_EXPORT
if '%choice%' == '4' goto PATCH_BUILD
if '%choice%' == '5' goto PATCH_BUILD_NO_UPDATE
if '%choice%' == '6' goto PATCH_BUILD_NO_EXPORT
if '%choice%' == '7' goto CORE_BUILD
if '%choice%' == '8' goto LEVELS_BUILD
if '%choice%' == '9' goto INSTALLER_BUILD

ECHO "%choice%" is not valid please try again
goto start


:FULL_BUILD
echo COMMENCING FULL BUILD OF PR
pause

call scripts\svn_update_core.bat
call scripts\svn_update_levels.bat

call scripts\svn_export_core.bat
call scripts\svn_export_levels.bat

call scripts\core_archive_build.bat
call scripts\levels_archive_build.bat

call scripts\python_compile.bat

call scripts\core_cleanup.bat
call scripts\levels_cleanup.bat

call scripts\server_build.bat
call scripts\server_cleanup.bat

call scripts\build_installers.bat

echo BUILD COMPLETE.
pause
exit

:PATCH_BUILD
echo COMMENCING PATCH BUILD OF PR
pause

rem call scripts\svn_update_core.bat
rem call scripts\svn_update_levels.bat

rem call scripts\svn_export_core.bat
rem call scripts\svn_export_levels.bat

rem call scripts\core_archive_cleanup.bat
rem call scripts\levels_archive_cleanup.bat

call scripts\patch_archive_build.bat

call scripts\python_compile.bat

call scripts\core_cleanup.bat
call scripts\levels_cleanup.bat

call scripts\patch_cleanup.bat

call scripts\server_build_patch.bat
call scripts\server_cleanup.bat

call scripts\build_installers_patch.bat

echo BUILD COMPLETE.
pause
exit

:FULL_BUILD_NO_UPDATE
echo COMMENCING FULL BUILD, WITHOUT SVN UPDATE
pause
call scripts\svn_export_core.bat
call scripts\svn_export_levels.bat

call scripts\core_archive_build.bat
call scripts\levels_archive_build.bat

call scripts\python_compile.bat

call scripts\core_cleanup.bat
call scripts\levels_cleanup.bat

call scripts\server_build.bat
call scripts\server_cleanup.bat

call scripts\build_installers.bat

echo BUILD COMPLETE.
pause
exit


:FULL_BUILD_NO_EXPORT
echo COMMENCING FULL BUILD, WITHOUT SVN UPDATE OR EXPORT
echo IF YOU DO NOT HAVE AN EXPORT OF THE SVN DIRECTORIES WITH THE CORRECT NAMING, CANCEL NOW.
pause

call scripts\core_archive_build.bat
call scripts\levels_archive_build.bat

call scripts\python_compile.bat

call scripts\core_cleanup.bat
call scripts\levels_cleanup.bat

call scripts\server_build.bat
call scripts\server_cleanup.bat

call scripts\build_installers.bat

echo BUILD COMPLETE.
pause
exit


:CORE_BUILD
echo BUILDING PR CORE ONLY
pause

call scripts\svn_update_core.bat
call scripts\svn_export_core.bat
call scripts\core_archive_build.bat
call scripts\python_compile.bat
call scripts\core_cleanup.bat

echo BUILD COMPLETE
pause
exit


:LEVELS_BUILD
echo BUILDING PR LEVELS ONLY
pause

call scripts\svn_update_core.bat
call scripts\svn_export_core.bat
call scripts\levels_archive_build.bat
call scripts\python_compile.bat
call scripts\levels_cleanup.bat

call scripts\build_installers.bat

echo BUILD COMPLETE
pause
exit

:INSTALLER_BUILD
echo BUILDING INSTALLERS
pause

call scripts\build_installers.bat

echo BUILD COMPLETE
pause
exit