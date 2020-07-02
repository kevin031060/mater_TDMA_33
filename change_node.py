import random
import matplotlib.pyplot as plt
import math
import pickle
import plot_node as plot_node

def change_node(node_num):

    x_list = []
    y_list = []

    for i in range(node_num):
        x = 10 * random.random()
        y = 2 * random.random()
        # plt.annotate(str(i+1), xy=(x, y), xytext=(x+0.2, y+0.1),
        #              arrowprops=dict(facecolor='black', shrink=0.0005),
        #              )
        x_list.append(x)
        y_list.append(y)

    output = open('xlist.pkl', 'wb')
    pickle.dump(x_list, output)
    output.close()
    output = open('ylist.pkl', 'wb')
    pickle.dump(y_list, output)
    output.close()

if __name__ == '__main__':
    change_node(6)
    plot_node.plot_node()
