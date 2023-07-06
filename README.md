# easypipeline
データ解析を繰り返すパイプライン処理を行い、結果を表にまとめ、HTML、csv、fitsで表示・保存したいことがある。また、それをなるべく汎用なライブラリだけで簡単に構築したい。その一例がここで書いたコードである。

## 初期設定

まず、この[easypipeline](https://github.com/tenoto/easypipeline)をローカル環境にダウンロードする。

```
git clone https://github.com/tenoto/easypipeline
cd easypipeline
```
この下には以下のファイルが入っている。

```
easypipeline
├── README.md (使い方メモ、このファイル)
├── easypipeline (プログラムの本体)
│   ├── __init__.py (おまじない)
│   ├── cli (Command Line Interface, CLI のこと)
│   │   ├── convert_csv2fits.py (出力された csv ファイルを fits 形式に変換する)
│   │   └── run_pipeline.py (メインのコードを読み出す CLI コード、引数を入れて実行する。test 参照)
│   ├── cogamo.py (今回の例で使った、雷雲プロジェクトのHKデータを扱うクラス)
│   └── pipeline.py (本節の議論であるパイプライン処理を実装したクラス)
├── setenv 
│   └── setenv.bashrc (このモジュールの CLI を別の階層からも呼び出せるようにするおまじない)
└── test (サンプルコード)
    └── example001 (ひとつめの例)
        ├── input (入力ファイル)
        │   ├── data (取得データなど。これは改変しないデータ)
        │   │   ├── 012_20210108.csv
        │   │   ├── 016_20210108.csv
        │   │   ├── 017_20210204.csv
        │   │   └── 028_20210102.csv
        │   └── parameter (表にしたいコラム名や、解析パラメータのファイル)
        │       ├── def_columns.yaml (表に詰めたいコラム)
        │       └── input_parameter.yaml (解析に使うパラメータを収容する)
        └── run_example001.sh (テストコードを実行するスクリプト)
```

まず、以下のおまじないをする。これで、CLI の下に格納されているスクリプト(run_pipeline.py,convert_csv2fits.py)などを、別階層のディレクトリからでも PATH が通っているので、読めるようになる。
```
source setenv/setenv.bashrc
```

## まず試してみる。

やってみよう。この状態で、easypipeline の直下で以下のコードを走らせてみる。もし、python のライブラリが足りないと言われたら、適宜、追加してください。
```
test/example001/run_example001.sh 
```
すると、勝手にウェブブラウザが表示されてパイプライン解析の結果を示す表が表示され、実行されると "Status" のコラムに Done という緑背景の文字がリアルタイムに表示、更新されていくはずである。これがやりたかったこと。



## 編集履歴
2023-07-06 version 1, 榎戸輝揚
