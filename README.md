
**NOTE** Since this framework performs a lot of system-level configuration changes to operate
it is highly recommended to create an environment for this inside a VM.

# Setup instructions

- Run `setup.sh` which will set up cross-compilation toolchains and setup the cross-compiled
  FirmFuzz kernels
 
- Fix up path for `HOME_DIR` in `./framework/scripts/env_var.config` and put `PATH` in `TEST_PATH`, this is because
  we run certain scripts as sudo and require location of cross compilation binaries
- Update `ROOT_DIR` in `cleanup_fs.sh`to point to your FirmFuzz Directory

# Run instructions

Using FirmFuzz on a firmware filesystem is a three-step process:
- Extracting the firmware filesystem from the firmware image
- Create a firmware emulation configuration for the extracted filesystem
- Run the fuzzer on the emulated fimrware image

Instructions for each of these steps is provided below.

## Filesystem extraction

- Use the firmadyne extractor system to extract the linux filesystem from the firmware image. Otherwise
you can provide a filesystem extracted using binwalk as well but I didn't test with that.

## Firmware Emulation

- Put the extracted filesystem from the previous phase (in the form of a .tgz file) into a folder name
  `$IMAGE_DIR`. (Note that `IMAGE_DIR` can be named anything

- Run `./run_batch_fs.sh $IMAGE_DIR. Note that $IMAGE_DIR should have a succeeding backslash when being passed to this script

- If a succcessful emulation for the firmware image is created, it would be placed in $HOME_DIR/final/scratch_ffs`

- To test the emulation, go to the newly created folder and run `sudo ./run.sh`. 

## Fuzzing

Before running, the fuzzer certain setup needs to be carried out.

### Fuzzer setup

```
sudo apt-get install python-pip python-dev 
libffi-dev libssl-dev libxml2-dev 
libxslt1-dev libjpeg8-dev zlib1g-dev g++

sudo pip install "mitmproxy==0.18.2"
sudo pip install "numpy"
sudo pip install "selenium==3.4.3"

# Install mitmdump v0.18.2

# Install geckodriver(v0.18.0) and put it in `/usr/local/bin`
```

### Create memory snapshot

Before running the firmware image for fuzzing, we create a memory snapshot to
revert to in case the firmware reaches an inconsistent state during fuzzing
You can use the following instructions to do so:
```
- Once the emulation reaches the stable state, run the following commands to
  save snapshot of the stable state
    - `ctrl-a and then c` to get into QEMU monitor mode
    - `savevm 1` to save the stable snapshot of the image

- Exit the emulation
```

### Run the fuzzer

- Fix the `FUZZER_ROOT_DIR` path in `env_fuzzer.py`
- Run the emulated image
- Run the selenium backend: `java -jar selenium-server-standalone-3.4.0.jar`
- Run the proxy server using the IP address where the firmware is exposing the web API. You can find this looking at the `run.sh` script that is generated for the emulated firmware
- The proxy server can be run as `mitmdump -R http://192.168.10.1 -s proxylogger.py`
- With these components up, the fuzzer can be fired up. An example invocation is provided that tests CI: `python fuzzer.py -d ~/location/of/emulated/firmware/ -u http://0.0.0.0:8080 -v 1 -a 1
