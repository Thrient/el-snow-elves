```bash
python -m nuitka --python-flag=no_warnings,-O,no_docstrings --remove-output --module script --include-package=script
ren script.cp312-win_amd64.pyd script.pyd
````

```bash
pyinstaller Elves.spec --distpath E:\Desktop\ 
```

```bash
Remove-Item script.pyd -Force
Remove-Item script.pyi -Force
robocopy "resources" "E:\Desktop\Elves\resources" /E
robocopy "dist" "E:\Desktop\Elves\_internal\dist" /E
Remove-Item E:\Desktop\Elves.zip  -Force
```
