
# GENERAL VARS
tokenPattern=~/em-facilities/usingAPI_demo/project_*
scipionBin=~/scipion/scipion
acquisitionScript=~/em-facilities/usingAPI_demo/acquisition_workflow_demo.py


# LAUNCHER
#rm $tokenPattern 2>/dev/null

#$scipionBin python $acquisitionScript

#ls $tokenPattern 2>/dev/null && projectToken=$(ls $tokenPattern) && rm $projectToken && project="${projectToken#*_}" && echo $project && $scipionBin project $project

emfacilities=~/em-facilities/usingAPI_demo

rm /tmp/scipion/project_* 2>/dev/null

~/scipion/scipion python $emfacilities/acquisition_workflow_demo.py

ls $emfacilities/project_* 2>/dev/null && projectToken=$(ls /tmp/scipion/project_*)  && project="${projectToken#*_}" && echo $project && ~/scipion/scipion project $project


