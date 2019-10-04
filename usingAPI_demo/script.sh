
# MAIN VARS
preCommands="cryosparc/cryosparc2_master/bin/cryosparcm restart"
scipionWrapper=/opt/VirtualGL/bin/vglrun
scipionBin=~/scipion/scipion
emfacilities=~/em-facilities
tokenDir=/tmp/scipion
tokenPattern=$tokenDir/project_*  # must coincide with the token made by the acquisitionScript

# DERIVED VARS
scriptFolder=$emfacilities/usingAPI_demo
acquisitionScript=$scriptFolder/acquisition_workflow_demo.py


# LAUNCHER

# make and clean the token
if ! ls $tokenDir 2>/dev/null ; then mkdir $tokenDir ; fi
rm $tokenPattern 2>/dev/null

# Launch the acquisition form and start the simulation
$preCommands &
$scipionBin python $acquisitionScript

# Launch Scipion project using the token
ls $tokenPattern 2>/dev/null && 
projectToken=$(ls $tokenPattern) && 
project="${projectToken#*_}" && 
rm $tokenPattern && 
$scipionWrapper $scipionBin project $project


