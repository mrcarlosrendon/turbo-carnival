mkdir build
copy *.py build
move octane build
python -m pip install -t build -r requirements.txt
del build.zip
cd build
zip build.zip *
move build.zip ..
cd ..

