cs244_pa3
=========

cs244_pa3

1. On Ubuntu 10.04, download and build nox-classic.  
2. Set NOX_CORE_DIR and the LD_PRELOAD directories in order to get the shared objects to load correctly:
3. Navigate to noxcore/build/src/nox/coreapps/examples, and add 'nox.coreapps.examples.update_app' to the JSON.
4. Create a symlink to the frenetic code:
  ln -s ~/cs244_pa3/updates/update_app.py . 

5. Set the correct system path in update_app.py, aka (or add to your PYTHONPATH):
sys.path.append('/home/mininet/cs244_pa3/updates')

5. Run with correct enviroment variables
For example:

From the updates directory:
sudo NOX_CORE_DIR=/home/mininet/nox-classic/build/src LD_PRELOAD=/home/mininet/nox-classic/build/src/nox/coreapps/pyrt/.libs/pyrt.so:/home/mininet/nox-classic/build/src/lib/.libs/libnoxcore.so:/home/mininet/nox-classic/build/src/builtin/.libs/libbuiltin.so:/usr/lib/libboost_filesystem.so ./run.py -m fattree fattree 1 none
Module = fattree
Getting function `Topology` from module `fattree`
*** Mininet Up ***
*** Application started ***
*** Application finished ***
   Update Statistics
--------------------------------------------
Switch  (+) (-) (~) Total   Overhead
--------------------------------------------
s101    550 390 0   940 42%
s102    426 294 0   720 62%
s103    580 420 0   1000    48%
s104    550 390 0   940 42%
s105    742 522 0   1264    97%
s106    182 132 0   314 100%
--------------------------------------------
total   3030    2148    0   3030    100%
*** Mininet Down ***

When troubleshooting make sure to clear old instances:
sudo ps -ef
sudo killall ofdatapath
sudo killall bash
sudo killall ofprotocol
