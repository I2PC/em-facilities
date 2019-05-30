
# MAIN VARS
scipionBin=~/scipion/scipion
emfacilities=~/em-facilities
tokenPattern=/tmp/scipion/project_*  # must coincide with the token made by the acquisitionScript

# DERIVED VARS
scriptFolder=$emfacilities/usingAPI_demo
acquisitionScript=$scriptFolder/acquisition_workflow_demo.py


# LAUNCHER

rm $tokenPattern 2>/dev/null

$scipionBin python $acquisitionScript

ls $tokenPattern 2>/dev/null && projectToken=$(ls $tokenPattern) && project="${projectToken#*_}" && rm $tokenPattern && $scipionBin project $project


