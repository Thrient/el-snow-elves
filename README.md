```sh
python -m nuitka --python-flag=no_warnings,-O,no_docstrings --remove-output --module script --include-package=script

````

```sh
ren script.cp312-win_amd64.pyd script.pyd
````


```sh
pyinstaller Elves.spec --distpath dist --workpath build --noconfirm --clean
```

```sh
Remove-Item script.pyd -Force
Remove-Item script.pyi -Force
robocopy "resources" "dist\Elves\resources" /E
copy "E:\Code\snow-elves\Tools\dist\Update.exe" "dist\Elves\Update.exe"
Remove-Item 'dist\Elves.zip'  -Force
```
