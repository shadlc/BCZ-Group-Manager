@echo off
:: 将数据拷贝到.\groupmanager YY.MM.DD\ 目录下
mkdir "groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%"
copy ..\strategy.json ".\groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%\strategy %date:~2,2%.%date:~5,2%.%date:~8,2%.json"
copy  ..\config.json ".\groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%\config %date:~2,2%.%date:~5,2%.%date:~8,2%.json"
copy  ..\monitor.json ".\groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%\group %date:~2,2%.%date:~5,2%.%date:~8,2%.json"
copy  ..\data.db ".\groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%\data %date:~2,2%.%date:~5,2%.%date:~8,2%.db"
copy  ..\local.json ".\groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%\local %date:~2,2%.%date:~5,2%.%date:~8,2%.json"
copy  ..\tidal_token.json ".\groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%\tidal_token %date:~2,2%.%date:~5,2%.%date:~8,2%.json"
copy  ..\poster_token.json ".\groupmanager %date:~2,2%.%date:~5,2%.%date:~8,2%\poster_token %date:~2,2%.%date:~5,2%.%date:~8,2%.json"

pause