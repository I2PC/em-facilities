#!/bin/bash

# MAIN VARS
preCommands=""  # "cryosparc/cryosparc2_master/bin/cryosparcm restart"
scipionWrapper=""  # /opt/VirtualGL/bin/vglrun
scipionBin=~/scipionDEVEL/scipion
emfacilities=~/em-facilities
tokenDir=/tmp/scipion

# DERIVED VARS
scriptFolder=$emfacilities/usingAPI_demo
launcherScript=$scriptFolder/form_launcher.py
tokenPattern=$tokenDir/project_*  # must coincide with the token made by the form_launcher.py
pidPattern=$tokenDir/simulation_* # must coincide with the token made by the simulate_acquitition.py

function runJob(){
  echo
  echo "==>>" $@
  echo
  $@
}



# LAUNCHER

# make and clean the token
if ! ls $tokenDir >>/dev/null 2>/dev/null ; then mkdir $tokenDir ; fi
rm $tokenPattern 2>/dev/null

# Launch the acquisition form and start the simulation
$preCommands &
runJob $scipionBin python $launcherScript

# Getting project name form token
ls $tokenPattern >>/dev/null 2>/dev/null &&
projectToken=$(ls $tokenPattern) &&
project="${projectToken#*_}" &&
rm $tokenPattern

if [ "$project" ]
then
  # Scheduling the whole project
  #runJob $scipionBin python schedule_project.py $project &

  # Launch Scipion project using the token
  runJob $scipionWrapper $scipionBin project $project
fi

# Getting simulation's pid to kill it
ls $pidPattern >>/dev/null 2>/dev/null &&
pidToken=$(ls $pidPattern) &&
echo "Stopping the simulation..." &&
kill -9 "${pidToken#*_}" &&
rm $pidToken
