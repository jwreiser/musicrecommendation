import generateRecommendations as grec
from pynput.keyboard import Key, Listener



def on_release(key):
    print('{0} release'.format(
        key))
    if key == Key.esc:
        # Stop listener
        return False

# Collect events until released

if __name__ == '__main__':
    grec.generate_recommendations()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
