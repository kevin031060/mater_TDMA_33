
from multiprocessing import Process
import time
import argparse
import os
import numpy as np
timesleep = 1.5
seed = np.random.randint(100000, size=100)
def simulate_start(sequence):
    ids=[]
    from simulate import node
    for i in range(len(sequence)):
        node_start = node(sequence[i], seed[i])
        p = Process(target=node_start.run)
        p.start()
        ids.append(p.pid)
        time.sleep(timesleep)
    time.sleep(15)
    print("PIDs:",ids)
    return ids
def run_batch(args):

    if args.example:
        if args.seq is not None:
            sequence = list(map(int,args.seq.split(',')))
        else:
            sequence = (np.random.permutation(12) + 1).tolist()
            # sequence = [1, 4, 3, 5, 6, 7, 2]

        if os.path.exists('config.py'):
            os.remove('config.py')
        time.sleep(1)
        with open('config.py','w') as f:
            f.writelines('import numpy as np\n')
            f.writelines('radius = 3\n')
            f.writelines('x = \'xlist2.pkl\'\n')
            f.writelines('y = \'ylist2.pkl\'\n')
            f.writelines('all_F = np.random.randint(1000,size=32)\n')
            f.flush()

        while True:
            if os.path.exists('config.py'):
                print("config created")
                print("Topology generated")
                break
        print('SEQ:',sequence)

        return simulate_start(sequence)
    else:

        if args.seq is not None:
            # sequence = [1, 4, 3, 5, 6, 7, 2]
            sequence = list(map(int, args.seq.split(',')))
            num = len(sequence)
            print('SEQ:', sequence)
        else:
            sequence = (np.random.permutation(args.num) + 1).tolist()
            num = args.num
            print('SEQ:', sequence)


        if os.path.exists('xlist.pkl'):
            os.remove('xlist.pkl')
        if os.path.exists('ylist.pkl'):
            os.remove('ylist.pkl')
        if os.path.exists('config.py'):
            os.remove('config.py')
        time.sleep(1)
        with open('config.py','w') as f:
            f.writelines('import numpy as np\n')
            f.writelines('radius = 3\n')
            f.writelines('x = \'xlist.pkl\'\n')
            f.writelines('y = \'ylist.pkl\'\n')
            f.writelines('all_F = np.random.randint(1000,size=32)\n')
            f.flush()
        while True:
            time.sleep(0.2)
            if os.path.exists('config.py'):
                print("config created")
                break
        from generate_node import generate_node
        print(generate_node(num))
        print("Generating topology with %d nodes.............." % num)
        while True:
            if os.path.exists('xlist.pkl') and os.path.exists('ylist.pkl'):
                print("Topology generated")
                break
        with open('config.py','r') as f:
            print(f.read())
        return simulate_start(sequence)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--num', type=int, default=7, help='number of nodes')
    parser.add_argument('--seq', default=None, help='sequence of start')
    parser.add_argument('--example', default=False)
    args = parser.parse_args()
    run_batch(args)




