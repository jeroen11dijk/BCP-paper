if(DEFINED ENV{DESTDIR})
  # If DESTDIR is not absolute path, make it relative to /data/or-tools/build
  # like any install() command.
  if(IS_ABSOLUTE $ENV{DESTDIR})
    set(ROOT "--root=$ENV{DESTDIR}")
  else()
    set(ROOT "--root=/data/or-tools/build/$ENV{DESTDIR}")
  endif()
else()
  set(ROOT "")
endif()

# Check if we have system Python on Debian/Ubuntu, if so tell setuptools
# to use the deb layout (dist-packages instead of site-packages).
execute_process(
  COMMAND /usr/bin/python3.9 -c "import sys; sys.stdout.write(sys.path[-1])"
  OUTPUT_VARIABLE Python_STDLIB_DIR
)
if(Python_STDLIB_DIR MATCHES ".*/dist-packages$")
  set(SETUPTOOLS_INSTALL_LAYOUT "--install-layout=deb")
else()
  set(SETUPTOOLS_INSTALL_LAYOUT "")
endif()

execute_process(
  WORKING_DIRECTORY /data/or-tools/build/python
  COMMAND /usr/bin/python3.9 setup.py install
    ${ROOT}
    --prefix=/usr/local
    ${SETUPTOOLS_INSTALL_LAYOUT}
)
