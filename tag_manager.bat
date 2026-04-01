@echo off
echo Deleting old local tags...
git tag -d v3.3
git tag -d v3.4
git tag -d v3.5
git tag -d v3.5.0
git tag -d temp_v3.4
echo Deleting old remote tags...
git push origin --delete v3.3
git push origin --delete v3.4
git push origin --delete v3.5
git push origin --delete v3.5.0
echo Creating new tags...
git tag v1.0.0 9b7fe6e
git tag v1.1.0 d5b1296
git tag v1.2.0 6f234c8
git tag v1.3.0 653ea1d
echo Pushing new tags...
git push origin --tags
echo Done.
