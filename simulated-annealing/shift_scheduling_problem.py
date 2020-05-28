import numpy as np

from funcy  import *
from neal   import SimulatedAnnealingSampler
from pyqubo import Array, Constraint, Placeholder, Sum, solve_qubo


M = 5
D = 10

BETA_RANGE         = (5, 100)
NUM_READS          = 10
NUM_SWEEPS         = 100000
BETA_SCHEDULE_TYPE = 'linear'


def solve(hs, js):
    response = SimulatedAnnealingSampler().sample_ising(hs, js, beta_range=BETA_RANGE, num_reads=NUM_READS, num_sweeps=NUM_SWEEPS, beta_schedule_type=BETA_SCHEDULE_TYPE, seed=1)

    return tuple(response.record.sample[np.argmin(response.record.energy)])


xs = Array.create('x', shape=(M, D), vartype='BINARY')

a = Placeholder('A')
b = Placeholder('B')

h = 0

for d in range(D):
    h += a * Constraint((Sum(0, M, lambda m: xs[m][d]) - 2) ** 2, f'day-{d}')

for m1 in range(M):
    for m2 in range(m1 + 1, M):
        for d1 in range(D):
            for d2 in range(d1 + 1, D):
                h += b * xs[m1][d1] * xs[m2][d1] * xs[m1][d2] * xs[m2][d2]

model = h.compile()


feed_dict = {'A': 2.0, 'B': 1.0}

hs, js, _ = model.to_ising(feed_dict=feed_dict)
answer, broken, energy = model.decode_solution(dict(enumerate(solve(hs, js))), vartype='SPIN', feed_dict=feed_dict)


print(f'broken:\t{len(broken)}')
print(f'energy:\t{energy}')

for d in range(D):
    print(tuple(keep(lambda m: 'ABCDE'[m] if answer['x'][m][d] == 1 else False, range(M))))
