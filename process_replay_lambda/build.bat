mkdir build
copy *.py build
move octane build
python -m pip install -t build -r requirements.txt
del build.zip
cd build
zip -r build.zip *
move build.zip ..
cd ..
aws lambda update-function-code --function-name process-replay --zip-file fileb://build.zip --publish

