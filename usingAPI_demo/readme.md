
# usingAPI_demo a self contained tutorial to on-line processing of cryo-EM data

The aim of this tutorial is to learn how to use the Scipion API in order to 
create and launch cryo-EM workflows to process data is streaming as soon as it 
arrives from the microscope.

This tutorial is in beta version, thus even it is usable and quite stable, 
it is under evaluation when applied to different data sets.


## Requisites

This tutorial runs over [Scipion](http://scipion.i2pc.es/) and some of its 
plugins. Especially, it needs the development version of Scipion.


### Scipion devel

To install the devel version of Scipion, we recommend to make a clear installation
from github
```
cd
git clone https://github.com/i2pc/scipion scipion-devel
git checkout devel
``` 

If a Scipion installation is in the system, we can re-use the config files from it
```
cp ~/scipion/config/scipion.conf config/scipion.conf
```
assuming that the already installed Scipion is in `~/scipion`.

If no previous installation is in the system, we need to configure Scipion by
```
./scipion config
```
If all it's fine (all green) we are ready to install Scipion, if not please check
[here for more information](https://scipion-em.github.io/docs/docs/scipion-modes/scipion-configuration.html)
Also, we strongly recommend to set `CUDA=True` in the `config/scipion.conf` file.

To install Scipion just
```
./scipion install -j 8    # where 8 is the number of cores to be used
```


### Xmipp devel

We also need the development version of [Xmipp](http://xmipp.i2pc.es/).
To do a clear installation of the devel version of Xmipp run
```
cd 
git clone https://github.com/i2pc/xmipp xmipp-devel
~/scipion-devel run ./xmipp
~/scipion-devel installp -p $(pwd)/src/scipion-em-xmipp --devel
```
see [here for more information](https://github.com/i2pc/xmipp#getting-started).


### The rest of the plugins

See [the plugin manager guide](https://scipion-em.github.io/docs/docs/user/plugin-manager.html#plugin-manager)
to learn how to easily install plugins. Basically is
```
cd ~/scipion-devel
./scipion
``` 
and go to `config >> Plugins`.

The plugin manager will install the plugin but also the package below.
If a valid installation of any package (eman, relion...) is in the system, 
Scipion can use it to run the plugin.

The demo workflow included in this tutorial needs the following plugins installed
(we indicate how install them using an existing installation):

- [Eman2](https://github.com/scipion-em/scipion-em-eman2/#eman2-plugin): 
`./scipion installp -p scipion-em-eman2 --noBin`.
Set `EMAN2_HOME=/path/to/eman`.
- [Relion3](https://github.com/scipion-em/scipion-em-relion/#relion-plugin):
`./scipion installp -p scipion-em-relion --noBin`.
Set `RELION_HOME=/path/to/relion3`.
- [Motioncor2](https://github.com/scipion-em/scipion-em-relion/#relion-plugin):
`./scipion installp -p scipion-em-motioncorr --noBin`.
Set `MOTIONCOR_HOME=/path/to/eman2`.
- [CTFfind4](https://github.com/scipion-em/scipion-em-grigoriefflab#setup):
`./scipion installp -p scipion-em-grigoriefflab --noBin`.
Set `CTFFIND_HOME=/path/to/ctffind4`.
- [gCTF](https://github.com/scipion-em/scipion-em-gctf#gctf-plugin):
`./scipion installp -p scipion-em-gctf --noBin`.
Set `GCTF_HOME=/path/to/relion3gctf`.
- [Cryolo](https://github.com/scipion-em/scipion-em-sphire#sphire-scipion-plugin):
`./scipion installp -p scipion-em-sphire --noBin`.
Set `CRYOLO_HOME=/path/to/cryolo`.
- [cryoSparc2](https://github.com/scipion-em/scipion-em-cryosparc2#cryosparc2-plugin):
`./scipion installp -p scipion-em-cryosparc2`.
Set `CRYOSPARC_HOME=/path/to/cryosparc2`.

