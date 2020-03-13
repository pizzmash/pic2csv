Pic2CSV
=============

Google Cloud Vision APIを使用して漫画画像データからテキスト領域情報を検出してcsvファイルを出力するプログラム

## Requires
- Python (>=3.3)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

## インストール
### python-dotenvのインストール
```
$ pip install python-dotenv
```

## 使用方法
### テキスト領域認識
`.env`にAPIキーを記載する必要がある

##### .env
```
API_KEY="your API key"
```

ローカル/オンライン上の画像を1枚ずつ指定する場合は，`-i`オプションを用いて以下のようにプログラムを実行する．結果が`pages.csv`と`frames.csv`に出力される．
```
$ python pic2csv.py -i image1.png image2.png image3.png …
```
ローカル上のあるディレクトリにまとめられた画像をまとめて指定する場合は，`-d`オプションを用いて以下のようにプログラムを実行する．
```
$ python pic2csv.py -d directory1 …
```
`-i`オプションを`-d`オプションを同時に使用することも可能である．また出力されるcsvファイルの出力先を指定する場合は，`pages.csv`と`frames.csv`それぞれについて`-p`オプションと`-f`オプションを使用する．

```
$ python pic2csv.py -d directory -p mypages.csv -f myframes.csv
```

####　出力ファイル例
##### pages.csv
```
source,page_id,frames
ginga_001.png,0,9
ginga_002.png,1,1
ginga_003.png,2,0
ginga_004.png,3,0
…
```

##### frames.csv
```
source,page_id,frame_id,startX,startY,width,height,text
ginga_001.png,0,0,840,34,168,229,ではみなさんは
ginga_001.png,0,1,215,34,243,301,そういうふうに川だといわれたり乳の流れたあとだといわれたりした
ginga_001.png,0,2,63,135,200,261,このぼんやりと白いものが
…
ginga_002.png,1,0,1799,244,355,458,「ぎんが」のページを
ginga_009.png,8,0,882,116,190,307,ではみなさんは
…
```


### CSVファイルの加工
`shape.py`を用いて，`pic2csv.py`にて生成されたCSVファイルに対して以下の処理を行える．

- 小さすぎるフレームの削除
- 他のフレームと包含関係にあるフレームの削除
- 一定の距離間にあるフレームの結合
- ノイズ文字の削除


以下はスクリプトの実行例．この例では`input_pages.csv`と`input_frames.csv`が`pic2csv.py`により生成されたCSVファイルであり，処理後の結果として`output_pages.csv`と`output_frames.csv`を出力する．
```
$ python shape.py input_pages.csv input_frames.csv output_pages.csv output_frames.csv
```

パラメータは`.env`にて指定可能
##### .env
```
MIN_W=15
MIN_H=15
X_EXPANSION=3
Y_EXPANSION=0
NOISE_CHARACTORS="、。])）」|\\/一"
```

`MIN_W`，`MIN_H`に幅/高さが何px以下のフレームを削除するかを指定する．`0`を指定すると変更が行われない．

`X_EXPANSION`，`Y_EXPANSION`にどれくらい近いフレーム同士を結合するかを指定する．ここで指定した値*2の距離以内にあるフレーム同士が結合される．`0`を指定すると変更が行われない

`NOISE_CHARACTORS`に削除対象とする文字を指定する．空文字列を指定すると変更が行われない．
