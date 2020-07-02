import matplotlib.pyplot as plt
import pickle
import math
import config

def plot_node(x_list, y_list):
    # pkl_file = open(GlobalVar.x, 'rb')
    # x_list = pickle.load(pkl_file)
    # pkl_file.close()
    #
    # pkl_file = open(GlobalVar.y, 'rb')
    # y_list = pickle.load(pkl_file)
    # pkl_file.close()

    plt.figure()
    node_num = len(x_list)
    for i in range(node_num):
        x = x_list[i]
        y = y_list[i]

        plt.text(x + 0.05, y + 0.05, str(i + 1))
        plt.plot(x, y, '.', color='red')

    for i in range(0, node_num - 1):
        for j in range(i + 1, node_num):
            if math.sqrt(math.pow((x_list[i] - x_list[j]), 2) + math.pow((y_list[i] - y_list[j]), 2)) < config.radius:
                plt.plot([x_list[i], x_list[j]], [y_list[i], y_list[j]], '-')
    plt.show()

if __name__ == '__main__':
    pkl_file = open('xlist.pkl', 'rb')
    x_list = pickle.load(pkl_file)
    pkl_file.close()

    pkl_file = open('ylist.pkl', 'rb')
    y_list = pickle.load(pkl_file)
    pkl_file.close()
    plot_node(x_list, y_list)