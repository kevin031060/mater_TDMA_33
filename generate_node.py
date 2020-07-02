import random
import matplotlib.pyplot as plt
import math
import pickle
import config
def generate_node(node_num = 7, show = False):
    x_list = []
    y_list = []

    plt.figure()
    for i in range(node_num):
        x = 10 * random.random()
        y = 0.5 * random.random()
        # plt.annotate(str(i+1), xy=(x, y), xytext=(x+0.2, y+0.1),
        #              arrowprops=dict(facecolor='black', shrink=0.0005),
        #              )
        plt.text(x + 0.05, y + 0.02, str(i + 1))
        plt.plot(x, y, '.', color='red')
        x_list.append(x)
        y_list.append(y)

    output = open('xlist.pkl', 'wb')
    pickle.dump(x_list, output)
    output.close()
    output = open('ylist.pkl', 'wb')
    pickle.dump(y_list, output)
    output.close()

    if show:
        plt.plot(x_list, y_list, '.', color='red')
        for i in range(0, node_num - 1):
            for j in range(i + 1, node_num):
                if math.sqrt(
                        math.pow((x_list[i] - x_list[j]), 2) + math.pow((y_list[i] - y_list[j]), 2)) < config.radius:
                    plt.plot([x_list[i], x_list[j]], [y_list[i], y_list[j]], '-')
        plt.show()

    return x_list, y_list


if __name__ == '__main__':
    generate_node(12)