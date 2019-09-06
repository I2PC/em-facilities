
# MAIN VARS
scipionBin=~/scipionBIN/scipion
emfacilities=~/em-facilities
tokenDir=/tmp/scipion
tokenPattern=$tokenDir/project_*  # must coincide with the token made by the acquisitionScript

# DERIVED VARS
scriptFolder=$emfacilities/usingAPI_demo
acquisitionScript=$scriptFolder/form_launcher.py  # acquisition_workflow_demo.py


# LAUNCHER

if ! ls $tokenDir 2>/dev/null ; then mkdir $tokenDir ; fi

rm $tokenPattern 2>/dev/null

$scipionBin python $acquisitionScript

ls $tokenPattern 2>/dev/null && projectToken=$(ls $tokenPattern) && project="${projectToken#*_}" && rm $tokenPattern && $scipionBin project $project


