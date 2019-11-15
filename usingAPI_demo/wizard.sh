#!/bin/bash

# MAIN VARS
preCommands="cryosparc/cryosparc2_master/bin/cryosparcm start"
scipionWrapper=/opt/VirtualGL/bin/vglrun
scipionBin=~/scipion/scipion
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
export ScipionProjectName=$(date +%Y%m%d)_mySelf_myProtein
$preCommands &
runJob $scipionBin python $launcherScript

# Getting project name form token
ls $tokenPattern >>/dev/null 2>/dev/null &&
projectToken=$(ls $tokenPattern) &&
project="${projectToken#*_}" &&
rm $tokenPattern

if [ "$project" ]
then
  if ls $tokenDir/wait4picking_$project >>/dev/null 2>/dev/null
    then scheduleArg = '--ignore XmippProtParticlePicking'
  fi

  # Set colors and labels
  runJob $scipionWrapper $scipionBin python $scriptFolder/set_labels_colors.py $project

  # Scheduling the whole project
  runJob $scipionBin python $scriptFolder/schedule_project.py $project $scheduleArg &

  # Launch Scipion project
  runJob $scipionWrapper $scipionBin project $project
fi

# Getting simulation's pid to kill it
ls $pidPattern >>/dev/null 2>/dev/null &&
pidToken=$(ls $pidPattern) &&
echo "Stopping the simulation..." &&
kill -9 "${pidToken#*_}" &&
rm $pidToken
