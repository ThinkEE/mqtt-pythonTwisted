################################################################################
# MIT License
#
# Copyright (c) 2017 Jean-Charles Fosse & Johann Bigler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

from twisted.internet import reactor

from modules.worker import MQTTWorker

#http://patorjk.com/software/taag/#p=display&h=1&f=Stick%20Letters&t=dEEmBox%20Main
BANNER = r"""
      ________   ___     ________ __
 |\/|/  \|  |     ||  ||/__`||__ |  \
 |  |\__X|  |     ||/\||.__/||___|__/

"""

# ------------------------------------------------------------------------------
if __name__ == '__main__':

    print("")
    print("-------------------------------------------------------------------")
    print(BANNER)

    config = {
      "endpoint": "____",
      "version": "v311",
      "client_id": "____",
      "username": "____",
      "app_key": "____"
    }

    # Worker managing the router. It is a Singleton
    worker = MQTTWorker(reactor, config)

    # Starts the worker
    worker.start()

    reactor.run() # Start Twisted reactor

    print("")
    print("-------------------------------------------------------------------")
    print("DEBUG: Shuting down module %s" %(APP_NAME))
