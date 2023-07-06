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

まず、以下のおまじないをする。これで、CLI の下に格納されているスクリプト(run_pipeline.py,convert_csv2fits.py)などを、別階層のディレクトリからでも PATH が通っているので、呼べるようになる。
```
source setenv/setenv.bashrc
```

## まず試してみる。

やってみよう。この状態で、easypipeline の直下で以下のコードを走らせてみる。もし、python のライブラリが足りないと言われたら、適宜、追加してください。
```
test/example001/run_example001.sh 
```
すると、勝手にウェブブラウザが表示されてパイプライン解析の結果を示す表が表示され、実行されると "Status" のコラムに Done という緑背景の文字がリアルタイムに表示、更新されていくはずである。下の画像みたいな感じ。

<img width="723" alt="スクリーンショット 2023-07-06 15 52 00" src="https://github.com/tenoto/easypipeline/assets/9628581/f0e06094-fc0e-49bd-869a-3cbe9615b702">

ここで、"QLcurve" のコラムのリンクをクリックすると、作成された pdf ファイルを画面上に表示することができる。

スクリプトを実施すると、

```
=== Pipeline: easypipeline generated === 
mkdir -p output/data
Pipeline run_pipeline: #_of_rows = 4  
-- 0/4 process started.
-- HKData 012_20210108: init input/data/012_20210108.csv
-- HKData 012_20210108: set_time_series
-- HKData 012_20210108: run
-- HKData 012_20210108: set_outdir
-- HKData 012_20210108: plot_qlcurves
-- status: Done
-- 1/4 process started.
-- HKData 016_20210108: init input/data/016_20210108.csv
-- HKData 016_20210108: set_time_series
-- HKData 016_20210108: run
-- HKData 016_20210108: set_outdir
-- HKData 016_20210108: plot_qlcurves
-- status: Done
-- 2/4 process started.
-- HKData 017_20210204: init input/data/017_20210204.csv
-- HKData 017_20210204: set_time_series
-- HKData 017_20210204: run
-- HKData 017_20210204: set_outdir
-- HKData 017_20210204: plot_qlcurves
-- status: Done
-- 3/4 process started.
-- HKData 028_20210102: init input/data/028_20210102.csv
-- HKData 028_20210102: set_time_series
-- HKData 028_20210102: run
-- HKData 028_20210102: set_outdir
-- HKData 028_20210102: plot_qlcurves
-- status: Done
```
みたいな表示が出て、実施状況はコマンドプロンプトでも確認できるようになっている。	

この段階で、test/example001/output/ の下には、同じ内容で２つの形式のファイルが生成されている。

- easypipeline.html (上で表示している HTML 形式のファイル)
- easypipeline.csv (CSV 形式の表、pandas などで読むことができる)

さらに、
```
easypipeline/cli/convert_csv2fits.py test/example001/output/easypipeline.csv --column test/example001/input/parameter/def_columns.yaml
```
を実行すると、

- easypipeline.fits (fits 形式のファイルなので、HEASoft の fv や他のコマンドで扱える)

も同じディレクトリに作成される。

## 何が便利か？

たくさんのデータを解析すると、個々の解析結果を細かく見ていきたい要求と、全体の結果を一覧性よく確認したり、相互の相関を取ったりしたくなる。また、パイプライン処理の実施状況を確認したり、途中で何らかのエラーで失敗したものを飛ばしながら、他は先に進めて、後でバグ取りをしたいときなどに使えると思う。

今回、表を作ったり、ループ処理を回す場所は、pipeline.py の中の PipelineTable というクラスで、run_pipeline という関数に担わせた。このループ処理の個別の解析は、cogamo.py の中の HKData というクラスの中で定義している。この HKData クラスの個々の関数に個別の処理を行わせ、それをまとめたものが、run という関数である。

なので、ユーザーはこの形式をコピーした後、 cogamo.py に相当するような、自分が処理したい対象のデータを扱うモジュール（クラス）を作成して、個々の処理をその中で定義し、pipeline.py の中の run_pipeline の関数で定義している、以下の箇所を、cogamo.py から呼び出して書き直せば、同様の枠組みを作ることができる。

```
			#### BEGIN: User can modify this ####
			status = '--'
			try:
				cgmhkfile = cogamo.HKData(self.df.iloc[index]['Filepath'])
				cgmhkfile.run(self,index)	
			except Exception as e:
				status = 'Error'
			else:
				status = 'Done'
			finally:
				sys.stdout.write('-- status: {}\n'.format(status))
				self.df.iloc[index]['Status'] = status 
				self.write()
				if flag_realtime_open: os.system('open %s ' % self.table_htmlpath)
			#### END: User can modify this ####				

```

## 各コードの役割
easypipeline の下には、メインになるプログラム群が入っている。この中で、cli はコマンドラインで呼び出すスクリプトなので、基本はこの cli 下のコードを呼び出して解析をする。たとえば、cli/run_pipeline.py では、argparse モジュールを使って引数処理をした後、easypipeline/pipeline.py を呼び出して実行している。なので、本体は、easypipeline/pipeline.py の中に記載されており、これがループ処理・パイプライン処理の大枠を決めている。

## ユーザーさんへ
なので、コードの中身をざっと読んで枠組みを理解して、適宜、改造して使ってみてほしい。合わせて、オブジェクト指向的な書き方に慣れているのも目的としている。なお、このコードは合間時間に試験的に初心者が書いたものなので、あまり信用しすぎないように。

## 宿題
以下の点はこれから実装する。
- エラーが出たときのログを各ファイルに保存する。
- 例外処理はまだ不十分なのだろうから、改訂する。
- xspec でフィットする例を作成する。


## 編集履歴
2023-07-06 version 1, 榎戸輝揚, 基本的な枠組みを作成した。CR大学院生のために公開。
