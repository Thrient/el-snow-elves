
```bash
python -m nuitka --python-flag=no_warnings,-O,no_docstrings --remove-output --module script --include-package=script
````

```bash
Remove-Item script.pyd -Force
ren script.cp312-win_amd64.pyd script.pyd
````

```bash
pyinstaller Elves.spec --distpath E:\Desktop\ 
```

```bash
robocopy "resources" "E:\Desktop\Elves\resources" /E
```

```bash
robocopy "dist" "E:\Desktop\Elves\_internal\dist" /E
```