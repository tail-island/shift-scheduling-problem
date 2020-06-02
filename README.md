# シフト・スケジューリング問題をいろいろな手法で解いてみた

アルゴリズムの勉強に、シフト・スケジューリング問題を解いてみました。本稿を書いている2020年5月に最もホットな話題はCOVID-19で、これが我々のサラリーマン生活にどのような影響を与えるかを考えてみると、出社したい（社員側の要望。去年までは出社させたいという会社側の要望だった）とテレワークさせたい（会社側の要望。去年まではテレワークしたいという社員側の要望だった）をいい感じに満たすことなんじゃないなかなぁと。うん、いわゆるひとつのシフト・スケジューリング問題ですな。

## 制約

* 社員はA、B、C、D、Eの5人
* 最低2名出社しなければならない。そして、できるだけ出社する人数を少なくしたい
* 社員のコミュニケーション活性化のために、できるだけ異なるペアの社員が出社するようにしたい。可能なら、たとえばAさんとBさんというペアが出社するのは一度だけにしたい（もちろん、席を離す等の感染対策を実施した上で）。

## [イジング模型を使用した焼きなまし法](https://github.com/tail-island/shift-scheduling-problem/blob/master/simulated-annealing/shift_scheduling_problem.py)

まず最初に、D-Waveの量子焼きなまし法でも使われているイジング模型でやってみましょう。ただし、量子焼きなまし法は普通のコンピューターでは実行できませんから、普通の焼きなまし法でやります。富士通のデジタルアニーラとかと同じやり方ですね。

でも、イジング模型を焼きなまし法で解く処理を作るのは面倒だったので、[D-Wave社のneal](https://docs.ocean.dwavesys.com/projects/neal/en/latest/index.html)を使用しました。あと、イジング模型を手作りするのもかなーり大変（というか、私の数学能力が低すぎてカケラも理解できない）ので、イジング模型の生成は[リクルート・コミュニケーションズ社のPyQUBO](https://pyqubo.readthedocs.io/en/latest/)を使用しました。

というわけで、nealとPyQUBOを使用して問題を解くコードはこんな感じ。

~~~ python
import numpy as np

from funcy  import *
from neal   import SimulatedAnnealingSampler
from pyqubo import Array, Constraint, Placeholder, Sum

M = 5   # 社員の数
D = 10  # 日数

BETA_RANGE         = (5, 100)  # 焼きなましの温度の逆数。大きい方が解が安定しますが、局所解に陥る可能性が高くなってしまいます
NUM_READS          = 10        # 焼きなましする回数。NUM_READS個の解が生成されます。多いほうが良い解がでる可能性が高くなります
NUM_SWEEPS         = 100000    # 焼きなましのステップを実施する回数。1つの解を生成するために繰り返し処理をする回数です。大きい方が良い解がでる可能性が高くなります
BETA_SCHEDULE_TYPE = 'linear'  # 焼きなましの温度をどのように変化させるか。linearだと線形に変化させます

# nealを使用してイジング模型を焼きなましして解を返します
def solve(hs, js):
    response = SimulatedAnnealingSampler().sample_ising(hs, js, beta_range=BETA_RANGE, num_reads=NUM_READS, num_sweeps=NUM_SWEEPS, beta_schedule_type=BETA_SCHEDULE_TYPE, seed=1)

    # NUM_READS個の解の中から、もっとも良い解を返します
    return tuple(response.record.sample[np.argmin(response.record.energy)])

# QUBOを構成する変数を定義します
xs = Array.create('x', shape=(M, D), vartype='BINARY')

# チューニングのための変数を定義します
a = Placeholder('A')
b = Placeholder('B')

# QUBOを定義します。ここから……
h = 0

# 1日に2名以上、かつ、できるだけ少なくという制約を追加します。2名より多くても少なくてもペナルティが発生するようになっています
for d in range(D):
    h += a * Constraint((Sum(0, M, lambda m: xs[m][d]) - 2) ** 2, f'day-{d}')  # 2を引くと、少なければ負、多ければ正の数になるわけですが、それを2乗して正の値にします

# 同じ人と別の日に出社しないという制約を追加します
for m1 in range(M):
    for m2 in range(m1 + 1, M):
        for d1 in range(D):
            for d2 in range(d1 + 1, D):
                h += b * xs[m1][d1] * xs[m2][d1] * xs[m1][d2] * xs[m2][d2]  # xsは1か0なので、掛け算をする場合は、全部1の場合にだけ1になります

# コンパイルしてモデルを作ります
model = h.compile()
# ……ここまで。QUBOを定義します

# チューニングのための変数の値
feed_dict = {'A': 2.0, 'B': 1.0}

# イジング模型を生成して、nealで解きます
hs, js, _ = model.to_ising(feed_dict=feed_dict)
answer, broken, energy = model.decode_solution(dict(enumerate(solve(hs, js))), vartype='SPIN', feed_dict=feed_dict)

# 結果を出力します
print(f'broken:\t{len(broken)}')  # Constraintに違反した場合は、brokenに値が入ります
print(f'energy:\t{energy}')       # QUBOのエネルギー。今回のモデルでは、全ての制約を満たした場合は0になります

# 日単位で、出社する社員を出力します
for d in range(D):
    print(tuple(keep(lambda m: 'ABCDE'[m] if answer['x'][m][d] == 1 else False, range(M))))
~~~

で、このプログラムを実行した結果はこんな感じ。

~~~
broken:	0
energy:	0.0
('D', 'E')
('A', 'D')
('B', 'C')
('A', 'C')
('B', 'D')
('B', 'E')
('C', 'E')
('A', 'E')
('A', 'B')
('C', 'D')
~~~

うん、正しいですね。毎日2名が出社していますし、同じ組合せはありません。ちなみに、私のコンピューターでの実行時間は0.734秒でした。解を10個作成していますので、1個あたり0.073秒。nealすげぇ速い！

### 簡単な解説

[Wikipediaのイジング模型のページ](https://ja.wikipedia.org/wiki/%E3%82%A4%E3%82%B8%E3%83%B3%E3%82%B0%E6%A8%A1%E5%9E%8B)を読むと、「二つの配位状態をとる格子点から構成され、再隣接する格子点のみの相互作用を考慮する格子模型」と書いてあってもーなんだか分かりません。ハミルトニアンって物理の用語みたいだけど美味しいの？　今から物理を勉強しないとならないの？

ご安心ください。物理を勉強しなければならないのはイジング模型を活用するハードウェアを作る人であって、我々プログラマーではありません。しかも、イジング模型はソフトウェア的にはかなり簡単な話なんです。

具体例で説明しましょう。まず、格子という言葉（イメージ的に縦横があるように思える）は無視してください（物理ハードウェア屋には重要だけど、プログラマーの我々には関係ない）。で、二つの配位状態ってのは、-1か1のどちらかしか代入できない特殊な変数だと考えてください。1とか-1だとイメージが掴みづらいので、今回は、3人が、ある提案に賛成するか反対するかをそれぞれ投票する場合で考えましょう。賛成の場合は1、反対の場合は-1になるわけですな。この3人の間には微妙な関係があって、aさんとbさんは同じ行動を取ると気持ちが良くて、何らかの過去の因縁でcさんとbさんは違う行動を取ると気持ちが良いとします。さて、この条件下で全員ができるだけ気持ちよくなるには、どうすればよいでしょうか？

コンピューターは数値しか扱えませんので、なんとかして数値で表現していなければなりません。aやb、cは1か-1のどちらかの値しか取れないので、みんなが気持ち良いときに数値が*小さく*なる式はこんなコードで表現できます。

~~~
-1 * a * b + 1 * b * c
~~~

少し詳しく見ていきましょう。1と-1の組合せを掛け算した結果は以下になります。

|値1|値2|結果|
| --: | --: | --: |
| 1   | 1   | 1   |
| 1   | -1  | -1  |
| -1  | 1   | -1  |
| -1  | -1  | 1   |
|     |     |     |

値が同じ場合と違う場合で1と-1に気持ちよく分かれるので、この結果に-1をかければ同じ場合は-1という小さな値に、違う場合は1という大きな値になるというわけ。ほら、先程の式でうまく表現できていたでしょ？

ただ、このままだと汎用性がなくて不便ですから、汎用的にしましょう。全ての変数の掛け算結果に、以下の表の値（ただしa * aは毎回同じなので無意味なので空欄で、a * bとb * aは同じ値になるので片方だけに値を入れる）を掛けることにします。

|||||
| ----- | ----- | ----- | ----- |
|       | __a__ | __b__ | __c__ |
| __a__ |       | -1    | 0     |
| __b__ |       |       | 1     |
| __c__ |       |       |       |
|       |       |       |       |

関係がないところは0にしておけばよいわけですな。で、このテーブルを使って計算をするコードを書いてみると、こんな感じ。aとb、cが`xs`という配列に、上の表の値が`js`という変数に入っていると考えてください。

~~~ python
def energy():
    result = 0

    for i in range(1, len(xs)):
        for j in range(i + 1, len(xs)):
            result += js[i][j] * xs[i] * xs[j]

    return result
~~~

これで、bさんとcさんが和解する等して関係性が変わったとしても、同じコードで表現できるようになりました（実際には、さらに汎用的にするためにもう一つの変数（イジング模型を使用した焼きなまし法のコードでの`hs`）も使用します）。で、この汎用的で素晴らしいこれが、イジング模型なんです。

ここまでくれば、`xs`の適当な要素をひっくり返して上のコードの結果を比べることで、良くなったか悪くなったかが簡単に分かります。いわゆる山登り法で解けるわけですな。ただ、山登り法の説明には局所解に陥りやすいと書いてあってなんか不安なので、最初のうちは上のコードの結果が少し悪くなる場合でも移動を許す、最後の方はその度合いを減らして良くなる方向に移動させるというやり方でこの問題を回避してみましょう。これは現実世界での焼きなましに似ているので焼きなまし法と呼ばれていて、結果が悪くなる場合でも許す度合いを現実世界の焼きなましにならって温度と呼びます。あと、上のコードの結果に現実世界で対応するのはエネルギーなので、上のコードの結果をエネルギーと呼びます。温度を下げながら、エネルギーが最小になる組合せを求める、みたいな表現となるわけですな。D-Wave社のnealは、この作業をとても効率よく実施してくれるんです。

というわけで焼きなましてみれば、その結果は、a=1, b=1, c=-1かa=-1, b=-1, c=1になるはずです。どちらの場合もエネルギーは最小の-2なので全員が気持ち良い。

ならあとは本稿の最初に挙げた制約に合わせて先程の表の値を作るだけ……なんですけど、これがかなーり難しい。本稿の制約のように、複数の変数が絡む場合はもうどうしていいか分かりません（裏で変数を追加して、その追加した変数も含めた関係で定義するらしい）。だから、リクルート・コミュニケーションズ社のPyQUBOを使いましょう。PyQUBOなら、式での表現を汎用性があるイジング模型に変換してくれるんです。あと、1と-1だと考えるのが大変なので、1と0を使うQUBOという形式でも定義できる（私では理解は出来なかったけど、イジング模型とQUBOは相互に変換できるらしい）ようになっています。

具体的に式で表現してみましょう。`xs`を`M`×`D`の二次元配列と考えて、出社する場合は1、出社しない場合は0とすれば、一日目に出社する社員の数は以下で計算できます。

~~~ python
result = 0

for m in range(M):
    result += xs[m][0]

return result
~~~

で、この結果は2に近いほど良くて、多くても少なくても駄目なわけです。だから2を引いて`abs`して絶対値を求めたい……のですけど、残念なことに`abs`のような関数は使えません。ではどうするかというと、2乗しちゃえばよいわけ。私は数学が苦手なのでよくわからないのですけど、マイナスとマイナスを掛け算すればプラスになるらしいですもんね。あと、PyQUBOは`Sum`という合計を求める関数を提供してくれているので、以下のコードになるわけです。

~~~ python
h += (Sum(0, M, lambda m: xs[m][0]) - 2) ** 2
~~~

これで、出社する人数が2の場合に最もエネルギーが小さくなって、2より多くても少なくてもそれより大きなエネルギーになるようになりました。

残りの、できるだけ異なるペアの社員については、異なる日に同じ組合せがあったら駄目にしちゃえばオッケー。簡単にするためにもう少し細かく考えて、たとえば「社員0と社員1で、2日目と3日目が同じならペナルティを与える」とする場合は、以下のコードで表現できます。

~~~ python
h += xs[0][2] * xs[1][2] * xs[0][3] * xs[1][3]
~~~

QUBOだからxsの要素の値は1か0のどちらかなので、だから0日目と1日目の両方に社員0と社員1の両方が出社する場合、つまり全部1の場合以外は0になります。全部1ということは同じ組合せなので、その場合に1になるのであればペナルティとしてとても都合がよい。あとは、他の社員の組合せと他の日の組合せを網羅するために、4重のループを書けば完成です。

あと、大抵の物事には優先順位があり、そして、異なる物事を足し合わせるのは困難です（今回の適当に作った2つの式の単位系が同じとは思えません。「かゆさ」と「うるささ」を足して「不愉快さ」を計算するのは困難でしょ？）。なので、適当な係数、`a`と`b`を掛けることにして、これらの値はチューニングの際に指定できるようにしましょう（かゆさ×`a`＋うるささ×`b`＝不愉快さと仮置きして、`a`や`b`の値は適宜調整する）。このようなときに便利なのが`Placeholder`です。今回は、いろいろ試してみて`a=1.0`と`b=0.5`にしてみました。と、こんな感じでPyQUBOでQUBOを定義すると、あとは`model.to_ising()`でイジング模型に一発で変換されるというわけ。これをnealで解けば答えが返ってくる。nealの代わりにD-Waveを使うことも可能。デジタルアニーラで解いて実行時間や精度をnealと比べたりもできちゃう。いやぁ、世の中便利になりましたな。

## [遺伝的アルゴリズム](https://github.com/tail-island/shift-scheduling-problem/blob/master/genetic-algorithms/shift_scheduling_problem.py)

調子に乗って、なんだか名前が浪漫的な遺伝的アルゴリズムでやりましょう。

例によって遺伝的アルゴリズムをする処理を作るのは面倒だったので、[DEAP](https://deap.readthedocs.io/en/master/)というオープン・ソースのライブラリを使用しました。コードはこんな感じ。

~~~ python
from deap      import algorithms, base, creator, tools
from functools import reduce
from funcy     import *
from random    import randint, random, seed

M = 5   # 社員の数
D = 10  # 日数

# 評価関数
def evaluate(individual):
    # 1日に2名以上、かつ、できるだけ少なくという制約を追加します。2名より多くても少なくてもペナルティが発生するようになっています
    def member_size():
        result = 0

        for d in range(D):
            result += abs(reduce(lambda acc, m: acc + individual[m * D + d], range(M), 0) - 2)  # 値そのものをしようしているので、absとかも使えます

        return result

    # 同じ人と別の日に出社しないという制約を追加します
    def different_member():
        result = 0

        for m1 in range(M):
            for m2 in range(m1 + 1, M):
                for d1 in range(D):
                    for d2 in range(d1 + 1, D):
                        result += individual[m1 * D + d1] * individual[m2 * D + d1] * individual[m1 * D + d2] * individual[m2 * D + d2]

        return result

    # 複数の評価の視点を、それぞれの視点での評価結果を要素とするタプルで返します
    return (member_size(), different_member())

# どのように遺伝的アルゴリズムするのかをDEAPで定義します
creator.create('Fitness', base.Fitness, weights=(-1.0, -0.5))  # evaluate()の結果が小さいほど良いので、ウェイトにマイナスを付けておきます
creator.create('Individual', list, fitness=creator.Fitness)

toolbox = base.Toolbox()

toolbox.register('attribute', randint, 0, 1)
toolbox.register('individual', tools.initRepeat, creator.Individual, toolbox.attribute, n=M * D)
toolbox.register('population', tools.initRepeat, list, toolbox.individual)
toolbox.register('mate', tools.cxTwoPoint)
toolbox.register('mutate', tools.mutFlipBit, indpb=0.05)
toolbox.register('select', tools.selTournament, tournsize=3)
toolbox.register('evaluate', evaluate)

# 再現性のために、ランダムのシードを固定します
seed(1)

# 遺伝アルゴリズムで問題を解きます
population, _ = algorithms.eaSimple(toolbox.population(n=100), toolbox, 0.5, 0.2, 300, verbose=False)

# 最も良い解を取得します
individual = tools.selBest(population, 1)[0]

# 結果を出力します
print(f'fitness:\t{individual.fitness.values}')

# 日単位で、出社する社員を出力します
for d in range(D):
    print(tuple(keep(lambda m: 'ABCDE'[m] if individual[m * D + d] else False, range(M))))
~~~

で、結果はこんな感じ。

~~~
fitness:	(0.0, 0.0)
('B', 'E')
('A', 'D')
('B', 'C')
('C', 'E')
('D', 'E')
('C', 'D')
('A', 'C')
('A', 'E')
('B', 'D')
('A', 'B')
~~~

はい。正しい解ですね。私のコンピューターでの実行時間は4.595秒でした。なんだ遅いじゃん使えないと感じた方は、次の「簡単な解説」を最後まで読んでみてください。

### 簡単な解説

かっこいい親から生まれた子供は多分かっこいい。で、そうでない親から生まれた私は……。

一つ前の焼きなまし法でもそうなのですけど、新しい解を作ることでより良い解を探していくという方式では、新しい解の作り方が重要です。たとえばランダムに新しい解を作ったりしたら、たぶん悪くなることが多くていつまで待っても良い解は見つからないでしょう。だから、山登り法では、現在の解を少し変えただけの、現在の解の近傍の解を使用します。良い解に似ているんだからたぶん良いだろう、って考えですね。で、遺伝的アルゴリズムでは、解を遺伝子みたいな感じで表現して、交配して子供が生まれたり突然変異したりする感じで新しい解を作成して、あと自然淘汰っぽい感じでより良い解を探していきます。交配や自然淘汰のために、解は1つではなくて複数個持ちます。かっこいい親の子供は多分かっこいいでしょうから、だから婚活市場で淘汰されずに生き残れそうって感じですね。

で、遺伝的アルゴリズムで最も重要なのは「解を染色体でどのように表現するか」です。今回のように、出社したら1で出社しないなら0のリストで表現しても構いません。数値の集合ならなんでもよい（NumPyのndarrayとか、SetやDictionary、木構造なんかも使えます）ので、巡回セールスマン問題だったら巡回する都市の番号のリストでもオッケー。車の運転とかなら、アクセルやブレーキを踏み込む強さを浮動小数点で表しても構いません。DEAPは、様々な遺伝子や染色体の表現を可能にするための機能を豊富に持っています。たとえば、巡回セールスマンで巡回する都市の番号を遺伝子にした場合なんかは、[DEAPのドキュメントのCreting Types](https://deap.readthedocs.io/en/master/tutorials/basic/part1.html)のPermutationが役に立ちます（これでもう順序表現のような面倒な手法を使わなくても済む！）。

あと、交配（遺伝的アルゴリズムでは交差と呼ぶ）の方法とか、突然変異の方法とか、自然淘汰する方法なんかも実はいろいろあるんですけど、それらの多くを実装してくれています。そしてさらに、これらをいい感じに組み合わせる方法を`algorithms`パッケージで提供してくれるんです。

でも、DEAPは使い方にちょっと癖があるんですよね……。DEAPが提供する機能を再利用して問題を解くのに必要な道具を作っていくのですけど、それを普通の関数合成ではなくてDEAPの機能でやらなければならないんです。たとえば、個体（解の1つに相当します）である`Individual`クラスを定義するには、`creator.create('Invididual', ...)`みたいにDEAPのAPIでやらなければなりません。で、交差するメソッドを作るのは`toolbox.register('mate', tools.cxTwoPoint)`みたいな感じ。これだけで2点交差をするメソッドを生成してくれるのは楽なのですけど、できれば普通に`partial`みたいな感じで書きたかった……。

まぁ、こんなのは贅沢な悩みなので、サクサクとプログラムを作ってしまいましょう。個体を評価する関数は自前で書かなければなりませんので、イジング模型を使用した焼きなましのときに書いたコードを参考にして、でも遺伝的アルゴリズムの場合は`abs`が使えて便利だなぁとか考えながら`evaluate()`関数を作成しました。あとは、解の良さを評価する`Fitness`クラス、個体を表現する`Individual`クラスを作成して、個体の染色体の属性を作る`attribute()`メソッドを作成してそれを利用して個体を生成する`individual()`メソッドを作成してそれを利用して集団を生成する`population()`メソッドを生成します。あとは、遺伝的アルゴリズムに必要な交差の`mate()`メソッドと突然変異の`mutation()`メソッドと自然淘汰の`select()`メソッドと、最初に作成した`evalute()`関数を呼び出す`evalute()`メソッドを生成します。

で、今回は、`algorithms.eaSimple()`で最もシンプルな形の遺伝アルゴリズムを実行させてみました。ライブラリに完全おまかせの手抜きでも、100個体で300世代の遺伝的アルゴリズムをやれば、正解がでちゃうんですね。

さて、イジング模型を使用した焼きなまし法よりも遅かった遺伝的アルゴリズムの良いところは、イジング模型より解の表現が柔軟なので適用可能な問題が多いことと、やり方がいっぱいあるのでチューニングの余地が大きいことです。本稿ではチューニングをしませんでしたが、染色体の表現をもっと効率化したり交差のやり方を変えたり突然変異が発生する確率をいい感じに変更したりすれば、イジング模型を使用した焼きなまし法よりももっと高速に精度の高い解を導けるようになるかもしれないわけ。すぐに効果が見えるので、チューニングは楽しいしね。

まぁ、そのためには遺伝的アルゴリズムの様々な手法の勉強をしなければならないのですけど、DEAPの実装で試しながら勉強すれば、すぐにマスターできるんじゃないかな。

## [整数計画法](https://github.com/tail-island/shift-scheduling-problem/blob/master/integer-programming/shift_scheduling_problem.py)

他に何かないかなーと考えたときに目に付いたのが、整数計画法です。線型計画法（Linear Programming）の整数に限定してさらに難しくなっちゃったバージョンですね。

線形計画法というのは、一次式（変数を1つだけ掛けたものが加減算でつながっている式。3 * x + yは一次式で、3 * a * a + bは二次式）で目的関数や制約関数を表現して、数学的にサクッと解いちゃう方法です。目的関数は、イジング模型を使用した焼きなまし法や遺伝的アルゴリズムでやったみたいな解の良さを表す式で、これができるだけ大きかったり小さかったりする解を選びます。で、制約関数というのは、解の制約を条件式で表現したものです。

え？　何を言っているか分からない？

私も全く分かっていないんだから聞かないでください……。でも、[PuLP](https://coin-or.github.io/pulp/)を使えばサクサクと整数計画法（もちろん線型計画法も）ができちゃうんです。コードはこんな感じ。

~~~ python
from functools import reduce
from funcy     import *
from pulp      import *

M = 5   # 社員の数
D = 10  # 日数

# 問題の中で使用する変数を定義します
xs = LpVariable.dicts('x', (range(M), range(D)), 0, 1, 'Binary')

# 問題を定義します。ここから……
problem = LpProblem('shift-scheduling-problem', LpMinimize)

# 1日に2名以上という制約を追加します
for d in range(D):
    problem += reduce(lambda acc, m: acc + xs[m][d], range(M), 0) >= 2

# 同じ人と別の日に出社しないという制約を追加します
for m1 in range(M):
    for m2 in range(m1 + 1, M):
        for d1 in range(D):
            for d2 in range(d1 + 1, D):
                problem += xs[m1][d1] + xs[m2][d1] + xs[m1][d2] + xs[m2][d2] <= 3  # 不等号（<）は使用できなかったので、<= 3で

# problem.writeLP('shift-scheduling-problem')
# ……ここまで。問題を定義します

# 整数計画法で、問題を解きます
status = problem.solve()

# 結果を出力します
print(LpStatus[status])

# 日単位で、出社する社員を出力します
for d in range(D):
    print(tuple(keep(lambda m: 'ABCDE'[m] if xs[m][d].value() else False, range(M))))
~~~

で、結果はこんな感じ。

~~~
Optimal
('D', 'E')
('C', 'D')
('A', 'E')
('C', 'E')
('B', 'D')
('B', 'C')
('A', 'C')
('A', 'D')
('B', 'E')
('A', 'B')
~~~

最適（Optimal）な解ですな。実行時間は0.132秒でとても速い！

### 簡単な解説

PuLPでの変数は、`LpVariable`で作成します。今回は多数の変数が必要でしたので、`LpVariable.dicts()`で一気に大量に生成しました。あと、今回は、制約を満たす解の中での優劣はありません（できるだけ異なるペアの社員の制約を満たそうとすると、出社する人数は少なくなる）ので、制約だけを定義しています。

PuLPでの制約の書き方は、条件式になります。1日の出社人数を`reduce()`で計算した結果`>= 2`のような感じですね。この条件式を`LpProblem`として作成した問題に`+=`で追加していきます。同じ人と別の日に出社しない制約では、これまでのように`xs[] * xs[] * xs[] * xs[]`とすると4次式になってしまいますので、足し算（これなら一次式）した結果`<= 3`という形の制約にしました。

あとはこれを`solve()`するだけ。もし制約を満たせるなら、制約を満たす中で目的関数が最も小さくなる最適解を、数学の魔法で解いて返してくれます（ちなみに、制約を満たせたかどうかは、`LpStatus[status]`で確認できます）。どんな数学の魔法を使っているのかは私は全く知らないのですけど、PuLPを使うだけなら無問題です。

うん、中身は分からないけど、こんなに短い時間で最適解を出してくれるなんてPuLPスゴイ……のはもちろんスゴイのですけど、残念なことに、整数計画法は完璧なわけではありません。今回の問題みたいに簡単ならばすぐに答えが返ってきますけど、難しい問題の場合は解を探すのにとても長い時間がかかったりするんです。遺伝的アルゴリズムやイジング模型を使用した焼きなまし法は、最適じゃないかもしれないけどそこそこ良さそうな解を出力するという方式なので、難しい問題でも何らかの解を出すことが出来るんですよ。難しい問題だと一次式では表現できない場合もあるしね。もちろん、絶対に最適解じゃなければ駄目だったり、あまり複雑ではない問題の場合は、整数計画法（線型計画法）がよいのですけど。

## [冷静になってみる](https://github.com/tail-island/shift-scheduling-problem/blob/master/combinatorics/shift_scheduling_problem.py)

でも、あれ？　冷静になってみると、もっと簡単なプログラムでもっと短い時間で解けるんじゃないかな？　ほら、組合せで考えて、こんな感じで……。

~~~ python
from itertools import combinations, cycle

# 重複しない社員2名の組合せを生成します
members = cycle(combinations('ABCDE', 2))  # 10日ならcycleしなくても良いのですけど、念の為

# 10日分、出力します
for _ in range(10):
    print(next(members))
~~~

実行してみたら……。

~~~
('A', 'B')
('A', 'C')
('A', 'D')
('A', 'E')
('B', 'C')
('B', 'D')
('B', 'E')
('C', 'D')
('C', 'E')
('D', 'E')
~~~

うん、見るからに正しいですな。実行時間は、0.028秒でした……。

### 簡単な解説

実は、異なるペアを選ぶ処理は、プログラムで表現してよいならとても簡単なんです。こんな感じ。

~~~ python
def getPairs(xs):
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            yield xs[i], xs[j]
~~~

同じものが選ばれないように、そして順序を逆にした組合せが選ばれないようにするために、`j`のループの`range`を`i + 1`から始めただけ。イジング模型を使用した焼きなまし法のコードの、同じ人と別の日に出社しない制約のところで使ったのと同じテクニックですな。で、この関数が返す結果を数えてみると10個で、だから今回の問題はうまくやればちょうど全ての制約を満たす答えを出せるという問題だったんですな。

で、この、5個の中から2個を選ぶ組合せの数は10ってのは、昔どこかで習ったような気がします……。[Wikipediaの組合せ数学](https://ja.wikipedia.org/wiki/%E7%B5%84%E5%90%88%E3%81%9B%E6%95%B0%E5%AD%A6)の繰り返しを許さない組合せの式がまさにそれ。5! / (2! * (5 - 2)!) = 10ですもんね。

と、こんな感じに有名な処理なので、組合せはたいていのプログラミング言語でライブラリ化されています。本稿で使用したPythonの場合は、`itertools.combinarions`がそれ。`combinations`の結果を、集合を繰り返して無限集合を作る`cycle`にかけて、その先頭から日数分だけ表示するだけでオッケーだったんですな。

というわけで、これが今回のオチ（制約のところでオチに気がついちゃった人はごめんなさい。あと、シフト・スケジューリング問題という用語は釣りです。真面目にシフト・スケジューリング問題をやっている人、本当にごめんなさい）なのですけど、本稿で言いたいことは、組合せをマスターしましょうという話ではありません。本稿は、イジング模型を使用した焼きなまし法も遺伝的アルゴリズムも整数計画法も組合せも、今どきのライブラリを使えば簡単に実装できると主張します。それぞれの手法には良いところも悪いところもあるので、問題によってどの手法が適切なのかは分かりません。ではどうするかといえば、とりあえず色々やってみちゃえばいいんじゃないかな。だって、こんなに簡単に実装できちゃうんですから。
