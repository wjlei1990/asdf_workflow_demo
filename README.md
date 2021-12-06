### Usage

This repocitory is for illustration purpose only. This is not for production purpose.

This examples runs on serial mode (single core) to make code eaisier to understand.

### Dependancy:
0. pyyaml
```
pip install pyyaml

```

1. pytomo3d
Read this carefully:
```
https://github.com/wjlei1990/pytomo3d/blob/master/INSTALL.md
```

2. pyasdf
```
https://github.com/SeismicData/pyasdf
```

After installing package, please make sure test case pass by running:
```
python -m pytest
```
in the source code (python package) directory.


### Window Selection
```
python window_asdf.py
```

### Adjoint sources
```
python adjoint_asdf.py
```

