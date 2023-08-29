@echo off
for /f "delims=" %%x in (config.py) do (set "%%x")


set batchpath=%~dp0
echo %condaenvironment%
call %path_activate_conda% || (
  	echo Error: Failed to activate Conda. Check the path to conda's "activate.bat" within the .bat file.
	echo This issue may arise due to variations in the computer's hardware or operating system. Problem the computer was changed.
	pause  
	exit /b 1
)

call conda activate %condaenvironment% || (
  	echo Error: Failed the activate the conda environment. Check if the conda env %condaenvironment% is available or has a different name. Check the ReadMe for further explanations.
	echo This issue may arise due to variations in the computer's hardware or operating system. Problem the computer was changed.
	pause  
	exit /b 1
)
call cd %batchpath%
call python stackpipeline/GUI.py
pause
