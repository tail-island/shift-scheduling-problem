from itertools import combinations, cycle


members = cycle(combinations('ABCDE', 2))  # 10日ならcycleしなくても良いのですけど、念の為

for _ in range(10):
    print(next(members))


def get2(xs):
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            yield (xs[i], xs[j])

print(tuple(get2('ABCDE')))