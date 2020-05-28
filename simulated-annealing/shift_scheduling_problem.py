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
